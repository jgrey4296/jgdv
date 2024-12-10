#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
# import abc
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
import weakref
# from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from types import GenericAlias
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match, Self,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from pydantic import (BaseModel, Field, InstanceOf,
                      field_validator, model_validator)

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv.structs.chainguard import ChainGuard
from jgdv._abstract.protocols import ParamStruct_p, ProtocolModelMeta, Buildable_p
from jgdv.mixins.annotate import AnnotateSubclass_m

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

NON_ASSIGN_PREFIX : Final[str] = "-"
ASSIGN_PREFIX     : Final[str] = "--"
END_SEP           : Final[str] = "--"

class ArgParseError(Exception):
    pass

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

    def consume(self, args:list[str], *, offset:int=0) -> None|tuple[dict, int]:
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
                case [x, *xs] if not self._match_on_head(x):
                    return None
                case [*xs] if self.repeatable:
                    value, consumed = self._get_while_matching(xs)
                case [x, *xs] if self.is_toggle and self.inverse in x:
                    value, consumed = self.default_value, 1
                case [x, *xs] if self.is_toggle:
                    value, consumed = not self.default_value, 1
                case [*xs] if bool(self.positional):
                    value, consumed = self._get_next_value(xs)
                case [x, *xs] if self.is_assignment_param and self.separator in x:
                    value, consumed = self._get_matching_assignment(x)
                case [*xs]:
                    value, consumed = self._get_matching_key_value(xs)
                case _:
                    raise ArgParseError("Tried to consume a bad type", remaining)
        except ArgParseError as err:
            logging.debug("Parsing Failed: %s : %s (%s)", self.name, args, err)
            return None

        return self._process_types(value), consumed

    def _process_types(self, value) -> dict:
        """ process the parsed values """
        result = {}
        match self.type_(), value:
            case _, None | []:
                pass
            case int(), [*xs]:
                result[self.name] = ftz.reduce(lambda x, y: x+int(y), xs, 0)
            case list(), list():
                result[self.name] = value
            case set(), list():
                result[self.name] = set(value)
            case _, [x]:
                result[self.name] = x
            case _, val:
                result[self.name] = val

        return result

    def _split_assignment(self, val) -> tuple[str, str]:
        assert(not self.positional)
        assert(val.startswith(self.prefix))
        assert(self.separator in val)
        key, val = val.split(self.separator)
        return key, val

    def _match_on_head(self, val) -> bool:
        """ test to see if a cli argument matches this param

        Will match anything if self.positional
        Matchs {self.prefix}{self.name} if not an assignment
        Matches {self.prefix}{self.name}{separator} if an assignment
        """
        match val, self.positional:
            case _, True:
                return True
            case _, int() as x if bool(x):
                return True
            case str(), False if val in self.key_strs:
                return True
            case str(), False if self.prefix == ASSIGN_PREFIX and val.startswith(self.prefix) and self.separator in val:
                key, _ = self._split_assignment(val)
                return key in self.key_strs
            case _, _:
                return False

    def _match_on_end(self, val) -> bool:
        return val == END_SEP

    def _get_while_matching(self, args:list) -> tuple[list, int]:
        """ Get as many values as match
        eg: args[-test, 2, -test, 3, -test, 5, -nottest, 6]
        ->  [2,3,5], [-nottest, 6]
        """
        logging.debug("Getting until no more matches: %s : %s", self.name, args)
        assert(self.repeatable)
        result, consumed, remaining  = [], 0, args[:]
        while bool(remaining):
            if self.is_assignment_param and self._match_on_head(remaining[0]):
                vals, count = self._get_matching_assignment(remaining[0])
                result   += vals
                consumed += count
                remaining = remaining[1:]
                continue
            elif self.is_assignment_param:
                break

            match self.positional:
                case _, _, if self._match_on_end(remaining[0]):
                    break
                case True:
                    vals, count = self._get_next_value(remaining)
                    result   += vals
                    consumed += count
                    remaining = remaining[count:]
                case False:
                    head, val, *rest = remaining
                    if not self._match_on_head(head):
                        break
                    else:
                        result.append(val)
                        remaining = rest
                        consumed += 2
                case int() as x if x <= len(remaining):
                    vals, rest = remaining[:x], remaining[x+1:]
                    result += vals
                    consumed += x

        return result, consumed

    def _get_next_value(self, args:list) -> tuple[list, int]:
        return [args[0]], 1

    def _get_matching_key_value(self, args:list) -> tuple[list, int]:
        """ get the value for a -key val """
        logging.debug("Getting Key/Value: %s : %s", self.name, args)
        match args:
            case [x, y, *_] if self._match_on_head(x):
                return [y], 2
            case _:
                raise ArgParseError("Failed to parse key")

    def _get_matching_assignment(self, arg) -> tuple[list, int]:
        """ get the value for a --key=val """
        logging.debug("Getting Key Assingment: %s : %s", self.name, arg)
        assert(self.separator in arg), (self.separator, arg)
        key,val = self._split_assignment(arg)
        return [val], 1

class ParamSpec(AnnotateSubclass_m, BaseModel, _ConsumerArg_m, _DefaultsBuilder_m, ParamStruct_p, Buildable_p, metaclass=ProtocolModelMeta, arbitrary_types_allowed=True):
    """ Declarative CLI Parameter Spec.

    Declared the param name (turns into {prefix}{name})
    The value will be parsed into a given {type_}, and lifted to a list or set if necessary
    If given, can have a {default} value.
    {insist} will cause an error if it isn't parsed

    If {positional} is True, then to parse it requires no -key.
    If {positional} is an int, then the parameter has to be in the correct place in the given args

    Can have a {desc} to help usage.
    Can be set using a short version of the name ({prefix}{name[0]}).
    If {implicit}, will not be listed when printing a param spec collection.

    """

    name                 : str
    type_                : InstanceOf[type]          = Field(default=bool, alias="type")

    insist               : bool                      = False
    default              : Any|Callable              = None
    desc                 : str                       = "An undescribed parameter"
    positional           : bool|int                  = False
    prefix               : str                       = NON_ASSIGN_PREFIX
    separator            : str                       = "="

    _short               : None|str                  = None
    _consumed            : int                       = 0
    _accumulation_types  : ClassVar[list[Any]]       = [int, list, set]
    _pad                 : ClassVar[int]             = 15

    @classmethod
    def build(cls:BaseModel, data:ChainGuard|dict) -> ParamSpec:
        match data:
            case {"implicit":True}:
                return ImplicitParam.model_validate(data)
            case _:
                return cls.model_validate(data)

    @staticmethod
    def key_func(x):
        """ Sort Parameters by:
        positional < int positional < len(prefix) < name
        """
        match x.positional:
            case False:
                return (1, 99, len(x.prefix), x.name)
            case True:
                return (-1, 0, len(x.prefix), x.name)
            case int() as p:
                return (-1, p, len(x.prefix), x.name)

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
            case type() if val is bool and (typevar:=cls.__dict__.get("_typevar", None)):
                # Handle annotation like ParamSpec[str]
                return typevar
            case type():
                return val
            case _:
                return Any

    @field_validator("default")
    def validate_default(cls, val):
        match val:
            case "None":
                return None
            case _:
                 return val

    @model_validator(mode="after")
    def validate_model (self) -> Self:
        if bool(self.prefix) and self.prefix in self.name:
            raise TypeError("Prefix was found in the base name", self)
        if bool(self.separator) and self.separator in self.name:
            raise TypeError("Separator was found in the base name", self)
        match self.type_():
            case bool():
                self.default = self.default or False
            case int():
                self.default = self.default or 0
            case str():
                self.default = self.default or ""
            case list():
                self.default = self.default or list
            case set():
                self.default = self.default or set

        return self

    @ftz.cached_property
    def short(self) -> None|str:
        if self.positional:
            return None

        return self._short or self.name[0]

    @ftz.cached_property
    def inverse(self) -> None:
        if not self.is_toggle:
            return None

        return f"no-{self.name}"

    @ftz.cached_property
    def repeatable(self):
        return self.type_ in ParamSpec._accumulation_types

    @ftz.cached_property
    def key_str(self) -> None|str:
        """ Get how the param needs to be written in the cli.
        eg: -test or --test

        """
        if self.positional:
            return None
        return f"{self.prefix}{self.name}"

    @ftz.cached_property
    def short_key_str(self) -> None|str:
        if self.positional:
            return None

        match self.short:
            case None:
                return None
            case x:
                return f"{self.prefix}{x}"

    @ftz.cached_property
    def key_strs(self) -> list[str]:
        return [x for x in [self.key_str, self.short_key_str, f"{self.prefix}{self.inverse}"] if x is not None]

    @property
    def is_assignment_param(self) -> bool:
        """ return True if param is of form --key=val """
        return self.prefix == ASSIGN_PREFIX

    @property
    def is_toggle(self) -> bool:
         return self.type_ is bool

    def __str__(self):
        match self.key_str:
            case None:
                parts = [f"[{self.name}]"]
            case str() as x:
                parts = [x]

        parts.append(" " * (self._pad - len(parts[0])))
        match self.type_:
            case type() if self.type_ == bool:
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

class BoolSpec(ParamSpec[bool]):
    pass

class LiteralParam(BoolSpec):
    """
    Match on a Literal Parameter.
    For command/subcmd names etc
    """
    prefix : str = ""

    def _match_on_head(self, val) -> bool:
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

class EntryParam(LiteralParam):
    """ TODO a parameter that if it matches,
    returns list of more params to parse
    """
    pass

class ImplicitParam(ParamSpec):
    """
    A Parameter that is implicit, so doesn't give a help description unless forced to
    """

    def __str__(self):
        return ""

class ConstrainedParam(ParamSpec):
    """
    TODO a type of parameter which is constrained in the values it can take, beyond just type.

    eg: {name:amount, constraints={min=0, max=10}}
    """
    constraints : list[Any] = []

class PositionalParam(ParamSpec):
    """ TODO a param that is specified by its position in the arg list """

    def _get_next_value(self, args:list) -> tuple[list, int]:
        return [args[0]], 1

class KeyParam(ParamSpec):
    """ TODO a param that is specified by a prefix key """

    def _match_on_head(self, val) -> bool:
        return val in self.key_strs

    def get_next_value(self, args:list) -> tuple[list, int]:
        """ get the value for a -key val """
        logging.debug("Getting Key/Value: %s : %s", self.name, args)
        match args:
            case [x, y, *_] if self._match_on_head(x):
                return [y], 2
            case _:
                raise ArgParseError("Failed to parse key")

class RepeatableParam(KeyParam):
    """ TODO a repeatable key param """

    def _get_next_value(self, args) -> tuple[list, int]:
        """ Get as many values as match
        eg: args[-test, 2, -test, 3, -test, 5, -nottest, 6]
        ->  [2,3,5], [-nottest, 6]
        """
        logging.debug("Getting until no more matches: %s : %s", self.name, args)
        assert(self.repeatable)
        result, consumed, remaining  = [], 0, args[:]
        while bool(remaining):
            head, val, *rest = remaining
            if not self._match_on_head(head):
                break
            else:
                result.append(val)
                remaining = rest
                consumed += 2

        return result, consumed


class AssignParam(ParamSpec):
    """ TODO a joined --key=val param """

    def _get_next_value(self, arg) -> tuple[list, int]:
        """ get the value for a --key=val """
        logging.debug("Getting Key Assingment: %s : %s", self.name, arg)
        assert(self.separator in arg), (self.separator, arg)
        key,val = self._split_assignment(arg)
        return [val], 1

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


    def _match_on_head(self, val) -> bool:
        """ test to see if a cli argument matches this param

        Will match anything if self.positional
        Matchs {self.prefix}{self.name} if not an assignment
        Matches {self.prefix}{self.name}{separator} if an assignment
        """
        return val in self._choices
