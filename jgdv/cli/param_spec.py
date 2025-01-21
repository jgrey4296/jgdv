#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import builtins
import datetime
import enum
import functools as ftz
import importlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import typing
import weakref
from dataclasses import InitVar, dataclass, field
from types import GenericAlias
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Self,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from pydantic import BaseModel, Field, InstanceOf, field_validator, model_validator

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv._abstract.protocols import Buildable_p, ParamStruct_p, ProtocolModelMeta
from jgdv.mixins.annotate import SubAnnotate_m
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from .errors import ArgParseError

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

NON_ASSIGN_PREFIX : Final[str] = "-"
ASSIGN_PREFIX     : Final[str] = "--"
END_SEP           : Final[str] = "--"

class _DefaultsBuilder_m:

    @staticmethod
    def build_defaults(params:list[ParamStruct_p]) -> dict:
        result = {}
        for p in params:
            assert(isinstance(p, ParamStruct_p))
            if p.name in result:
                raise KeyError("Duplicate default key found", p, params)
            result.setdefault(*p.default_tuple())

        return result

    def default_tuple(self) -> tuple[str, Any]:
        return self.name, self.default_value

    @property
    def default_value(self):
        match self.default:
            case type():
                return self.default()
            case x if callable(x):
                return x()
            case x:
                return x

    @staticmethod
    def check_insists(params:list[Self], data:dict) -> None:
        missing = []
        for p in params:
            if p.insist and p.name not in data:
                missing.append(p.name)
        else:
            if bool(missing):
                raise ArgParseError("Missing Required Params", missing)

class _ConsumerArg_m:
    "Mixin for CLI arg consumption"

    def consume(self, args:list[str], *, offset:int=0) -> Maybe[tuple[dict, int]]:
        """
          Given a list of args, possibly add a value to the data.
          operates on both the args list
          return maybe(newdata, amount_consumed)

          handles:
          ["--arg=val"],
          ["-arg", "val"],
          ["val"],     (if positional=True)
          ["-arg"],    (if type=bool)
          ["-no-arg"], (if type=bool)
          """
        consumed, remaining = 0, args[offset:]
        try:
            match remaining:
                case []:
                    return None
                case [x, *xs] if not self.matches_head(x):
                    return None
                case [*xs]:
                    key, value, consumed = self.next_value(xs)
                    return self.coerce_types(key, value), consumed
                case _:
                    raise ArgParseError("Tried to consume a bad type", remaining)
        except ArgParseError as err:
            logging.debug("Parsing Failed: %s : %s (%s)", self.name, args, err)
            return None

    def matches_head(self, val) -> bool:
        """ test to see if a cli argument matches this param

        Will match anything if self.positional
        Matchs {self.prefix}{self.name} if not an assignment
        Matches {self.prefix}{self.name}{separator} if an assignment
        """
        key, *_ = self._split_assignment(val)
        return key in self.key_strs and key.startswith(str(self.prefix))

    def next_value(self, args:list) -> tuple[str, list, int]:
        if self.positional or self.type_ is bool:
            return self.name, [args[0]], 1
        if self.separator not in args[0]:
            return self.name, [args[1]], 2

        key, *vals = self._split_assignment(args[0])
        if key != self.name:
            raise ArgParseError("Assignment doesn't match", key, self.name)
        return self.name, [vals[0]], 1

    def coerce_types(self, key, value) -> dict:
        """ process the parsed values """
        result = {}
        match self.type_(), value:
            case _, None | []:
                pass
            case bool(), [x]:
                result[key] = bool(x)
            case int(), [*xs]:
                result[key] = ftz.reduce(lambda x, y: x+int(y), xs, 0)
            case list(), list():
                result[key] = value
            case set(), list():
                result[key] = set(value)
            case _, [x]:
                result[key] = x
            case _, val:
                result[key] = val

        return result

    def _split_assignment(self, val) -> list[str]:
        return val.split(self.separator)

    def _match_on_end(self, val) -> bool:
        return val == END_SEP

PSpecMixins = [SubAnnotate_m, _ConsumerArg_m, _DefaultsBuilder_m]
PSpecProtocols = [ParamStruct_p, Buildable_p]

class ParamSpecBase(*PSpecMixins, BaseModel, *PSpecProtocols, metaclass=ProtocolModelMeta, arbitrary_types_allowed=True):

    """ Declarative CLI Parameter Spec.

    Declared the param name (turns into {prefix}{name})
    The value will be parsed into a given {type_}, and lifted to a list or set if necessary
    If given, can have a {default} value.
    {insist} will cause an error if it isn't parsed

    If {prefix} is a non-empty string, then its positional, and to parse it requires no -key.
    If {prefix} is an int, then the parameter has to be in the correct place in the given args.

    Can have a {desc} to help usage.
    Can be set using a short version of the name ({prefix}{name[0]}).
    If {implicit}, will not be listed when printing a param spec collection.

    """

    name                 : str
    type_                : InstanceOf[type]          = Field(default=bool, alias="type")

    insist               : bool                      = False
    default              : Any|Callable              = None
    desc                 : str                       = "An undescribed parameter"
    count                : int                       = 1
    prefix               : int|str                   = NON_ASSIGN_PREFIX
    separator            : str                       = "="

    _short               : Maybe[str]                = None
    _accumulation_types  : ClassVar[list[Any]]       = [int, list, set]
    _pad                 : ClassVar[int]             = 15

    _subtypes            : dict[type, type]          = {}

    @classmethod
    def build(cls:BaseModel, data:dict) -> ParamSpecBase:
        return cls.model_validate(data)

    @staticmethod
    def key_func(x):
        """ Sort Parameters so:
        -{prefix len} < name < positional < int positional < --help

        """
        match x.prefix:
            case _ if x.name == "help":
                return (99, 99, x.prefix, x.name)
            case str():
                return (0, -len(x.prefix), x.prefix, x.name)
            case int() as p:
                return (10, p, x.prefix, x.name)

    @field_validator("type_", mode="before")
    def validate_type(cls, val):
        match val:
            case "int":
                return int
            case "float":
                return float
            case "bool":
                return bool
            case "str":
                return str
            case "list":
                return list
            case x if x in [bool, str, list, set, float, int]:
                return x
            case types.GenericAlias():
                return val.__origin__
            case typing.Any:
                return Any
            case _:
                raise TypeError("Bad Type for ParamSpec", val)

    @field_validator("default")
    def validate_default(cls, val):
        match val:
            case "None":
                return None
            case _:
                 return val

    @model_validator(mode="after")
    def validate_model (self) -> Self:
        # TODO extract prefix automatically from name
        #
        match self.prefix:
            case str() if bool(self.prefix) and self.name.startswith(self.prefix):
                raise TypeError("Prefix was found in the base name", self, self.prefix)
            case str() if bool(self.prefix) and self.separator in self.name:
                raise TypeError("Separator was found in the base name", self)

        match self._get_annotation():
            case None:
                pass
            case x:
                self.type_ = self.validate_type(x)

        match self.type_:
            case builtins.bool:
                self.default = self.default or False
            case builtins.int:
                self.default = self.default or 0
            case builtins.str:
                self.default = self.default or ""
            case builtins.list:
                self.default = self.default or list
            case builtins.set:
                self.default = self.default or set
            case _:
                self.default = None

        return self

    @ftz.cached_property
    def short(self) -> str:
        return self._short or self.name[0]

    @ftz.cached_property
    def inverse(self) -> None:
        return f"no-{self.name}"

    @ftz.cached_property
    def repeatable(self):
        return self.type_ in ParamSpecBase._accumulation_types

    @ftz.cached_property
    def key_str(self) -> str:
        """ Get how the param needs to be written in the cli.
        eg: -test or --test
        """
        match self.prefix:
            case str():
                return f"{self.prefix}{self.name}"
            case _:
                return self.name

    @ftz.cached_property
    def short_key_str(self) -> Maybe[str]:
        match self.prefix:
            case str():
                return f"{self.prefix}{self.short}"
            case _:
                return None

    @ftz.cached_property
    def key_strs(self) -> list[str]:
        """ all available key-str variations """
        match self.prefix:
            case str():
                inv = f"{self.prefix}{self.inverse}"
                return [self.key_str, self.short_key_str, inv]
            case _:
                return [self.key_str, self.short_key_str]

    @ftz.cached_property
    def positional(self) -> bool:
        match self.prefix:
            case str() if bool(self.prefix):
                return False
            case _:
                return True

    def help_str(self):
        match self.key_str:
            case None:
                parts = [f"[{self.name}]"]
            case str() as x:
                parts = [x]

        parts.append(" " * (self._pad - len(parts[0])))
        match self.type_:
            case type() if self.type_ is bool:
                parts.append(f"{'(bool)': <10}:")
            case str() if bool(self.default):
                parts.append(f"{'(str)': <10}:")
            case str():
                parts.append(f"{'(str)': <10}:")
            case _:
                pass

        parts.append(f"{self.desc:<30}")
        pad = " "*max(0, (85 - (len(parts)+sum(map(len, parts)))))
        match self.default:
            case None:
                pass
            case str():
                parts.append(f'{pad}: Defaults to: "{self.default}"')
            case _:
                parts.append(f"{pad}: Defaults to: {self.default}")

        return " ".join(parts)

    def __repr__(self):
        if self.positional:
            return f"<{self.__class__.__name__}: {self.name}>"
        return f"<{self.__class__.__name__}: {self.prefix}{self.name}>"

class ToggleParam(ParamSpecBase[bool]):

    def next_value(self, args:list) -> tuple[str, list, int]:
        head, *_ = args
        if self.inverse in head:
            value = self.default_value
        else:
            value = not self.default_value

        return self.name, [value], 1

class LiteralParam(ToggleParam):
    """
    Match on a Literal Parameter.
    For command/subcmd names etc
    """
    prefix : str = ""

    def matches_head(self, val) -> bool:
        """ test to see if a cli argument matches this param

        Will match anything if self.positional
        Matchs {self.prefix}{self.name} if not an assignment
        Matches {self.prefix}{self.name}{separator} if an assignment
        """
        match val:
            case x if x == self.name:
                return True
            case _:
                return False

class ImplicitParam(ParamSpecBase):
    """
    A Parameter that is implicit, so doesn't give a help description unless forced to
    """

    def help_str(self):
        return ""

class PositionalParam(ParamSpecBase):
    """ TODO a param that is specified by its position in the arg list """

    @ftz.cached_property
    def key_str(self) -> str:
        return self.name

    def matches_head(self, val) -> bool:
        return True

    def next_value(self, args:list) -> tuple[str, list, int]:
        match self.count:
            case 1:
                return self.name, [args[0]], 1
            case -1:
                idx     = args.index(END_SEP)
                claimed = args[max(idx, len(args))]
                return self.name, claimed, len(claimed)
            case int() as x if x < len(args):
                return self.name, args[:x], x
            case _:
                raise ArgParseError()

class KeyParam(ParamSpecBase):
    """ TODO a param that is specified by a prefix key """

    def matches_head(self, val) -> bool:
        return val in self.key_strs

    def get_next_value(self, args:list) -> tuple[list, int]:
        """ get the value for a -key val """
        logging.debug("Getting Key/Value: %s : %s", self.name, args)
        match args:
            case [x, y, *_] if self.matches_head(x):
                return str, [y], 2
            case _:
                raise ArgParseError("Failed to parse key")

class RepeatableParam(KeyParam):
    """ TODO a repeatable key param """

    type_ : InstanceOf[type] = Field(default=list, alias="type")

    def next_value(self, args:list) -> tuple[str, list, int]:
        """ Get as many values as match
        eg: args[-test, 2, -test, 3, -test, 5, -nottest, 6]
        ->  [2,3,5], [-nottest, 6]
        """
        logging.debug("Getting until no more matches: %s : %s", self.name, args)
        assert(self.repeatable)
        result, consumed, remaining  = [], 0, args[:]
        while bool(remaining):
            head, val, *rest = remaining
            if not self.matches_head(head):
                break
            else:
                result.append(val)
                remaining = rest
                consumed += 2

        return self.name, result, consumed

class AssignParam(ParamSpecBase):
    """ TODO a joined --key=val param """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("prefix", "--")
        super().__init__(*args, **kwargs)

    def next_value(self, args:list) -> tuple[str, list, int]:
        """ get the value for a --key=val """
        logging.debug("Getting Key Assignment: %s : %s", self.name, args)
        if not (self.separator in args[0]):
            raise ArgParseError("Assignment param has no assignment", self.separator, args[0])
        key,val = self._split_assignment(args[0])
        return self.name, [val], 1

class WildcardParam(AssignParam):
    """ TODO a wildcard param that matches any --{key}={val} """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("type", str)
        kwargs['name'] = "*"
        super().__init__(**kwargs)

    def matches_head(self, val) -> bool:
        return (self.prefix == ASSIGN_PREFIX
                and val.startswith(self.prefix)
                and self.separator in val)

    def next_value(self, args:list) -> tuple[str, list, int]:
        logging.debug("Getting Wildcard Key Assingment: %s", args)
        assert(self.separator in args[0]), (self.separator, args[0])
        key,val = self._split_assignment(args[0])
        return key.removeprefix(self.prefix), [val], 1

class HelpParam(ImplicitParam[bool]):
    """ The --help flag that is always available """

    def __init__(self):
        super().__init__(name="help", default=False, prefix="--")

class VerboseParam(ImplicitParam[int]):
    """ The implicit -verbose flag """

    def __init__(self):
        super().__init__(name="verbose", default=0, prefix="-")

class SeparatorParam(LiteralParam):
    """ A Parameter to separate subcmds """

    def __init__(self):
        super().__init__(name=END_SEP)

class ChoiceParam(LiteralParam[str]):
    """ TODO A param that must be from a choice of literals """

    def __init__(self, name, choices:list[str], **kwargs):
        super().__init__(name=name, **kwargs)
        self._choices = choices

    def matches_head(self, val) -> bool:
        """ test to see if a cli argument matches this param

        Will match anything if self.positional
        Matchs {self.prefix}{self.name} if not an assignment
        Matches {self.prefix}{self.name}{separator} if an assignment
        """
        return val in self._choices

class EntryParam(LiteralParam):
    """ TODO a parameter that if it matches,
    returns list of more params to parse
    """
    pass

class ConstrainedParam(ParamSpecBase):
    """
    TODO a type of parameter which is constrained in the values it can take, beyond just type.

    eg: {name:amount, constraints={min=0, max=10}}
    """
    constraints : list[Any] = []

class ParamSpec(ParamSpecBase):
    """ A Top Level Access point for building param specs """

    @classmethod
    def build(cls:BaseModel, data:dict) -> ParamSpecBase:
        match data:
            case {"implicit":True}:
                return ImplicitParam.model_validate(data)
            case {"prefix":int()|None|""}:
                return PositionalParam.model_validate(data)
            case {"prefix":x, "type":y} if x == ASSIGN_PREFIX and y in [bool, "bool"]:
                return ToggleParam.model_validate(data)
            case {"prefix":x} if x == ASSIGN_PREFIX:
                return AssignParam.model_validate(data)
            case {"type":"list"|"set"}:
                return RepeatableParam.model_validate(data)
            case {"type":"bool"}:
                return ToggleParam.model_validate(data)
            case _:
                return KeyParam.model_validate(data)
