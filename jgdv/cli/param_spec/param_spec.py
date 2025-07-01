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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Proto
from jgdv._abstract.pydantic_proto import ProtocolModelMeta
from jgdv.mixins.annotate import SubAlias_m
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from jgdv._abstract.protocols import Buildable_p
from jgdv.cli.errors import ArgParseError
from .. import _interface as API # noqa: N812
from .._interface import ParamSpec_p, ParamSpec_i

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any, Literal
from collections.abc import Callable
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from jgdv import Rx
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class _SortGroups_e(enum.IntEnum):
    head      = 0
    by_prefix = 10
    by_pos    = 20
    last      = 99

##--|

class ParamProcessor:
    """ Parses a name into its component parts.

    eg: --blah= -> {prefix:--, name:blah, assign:None}
    """
    __slots__                  = ()

    debug    : ClassVar[bool]  = False
    name_re  : ClassVar[Rx]    = API.FULLNAME_RE
    end_sep  : ClassVar[str]   = API.END_SEP

   ##--| parsing

    def parse_name(self, name:str) -> Maybe[dict]:
        """
        Parse a string into a dict of the params:
        - name
        - prefix
        - separator
        """
        matched  : re.Match
        result   : dict
        groups   : dict[str, Maybe[str]]
        ##--|

        match self.name_re.match(name):
            case None:
                return None
            case re.Match() as matched:
                groups = matched.groupdict()
            case x:
                raise TypeError(type(x))

        result = {"name": matched['name'], "prefix":False}
        match groups:
            case {"pos": None|"", "prefix": None|""}:
                result['prefix'] = 99
            case {"pos": str() as x, "prefix":None}: # type: ignore[misc]
                result['prefix'] = int(cast("str", x))
            case {"pos": None, "prefix":str() as x}: # type: ignore[misc]
                result['prefix'] = x

        match groups['assign']:
            case None:
                result['separator'] = False
            case str() as x: # type: ignore[misc]
                result['separator'] = cast("str", x)

        return result

    ##--| consuming

    def consume(self, obj:ParamSpec_i, args:list[str], *, offset:int=0) -> Maybe[tuple[dict, int]]:
        """
          Given a list of args, possibly add a value to the data.

          return maybe(newdata, amount_consumed)

          handles:
          ["--arg=val"],
          ["-arg", "val"],
          ["val"],     (if positional=True)
          ["-arg"],    (if type=bool)
          ["-no-arg"], (if type=bool)
          """
        result  : Maybe[tuple[dict, int]]  = None
        consumed, remaining                = 0, args[offset:]
        ##--|
        logging.debug("Trying to consume: %s : %s", obj.name, remaining)
        try:
            match remaining:
                case []:
                    result = None
                case [x, *xs] if not self.matches_head(obj, x):
                    result = None
                case [*xs]:
                    key, value, consumed = self.next_value(obj, xs)
                    result = self.coerce_types(obj, key, value), consumed
                case _:
                    msg = "Tried to consume a bad type"
                    raise ArgParseError(msg, remaining)  # noqa: TRY301
        except ArgParseError as err:
            logging.debug("Parsing Failed: %s : %s (%s)", obj.name, args, err)
            return None
        else:
            return result

    def next_value(self, obj:ParamSpec_i, args:list) -> tuple[str, list, int]:
        match getattr(obj, "next_value", None):
            case None:
                pass
            case x:
                assert(callable(x))
                return x(args)

        if obj.type_ is bool:
            return obj.name, [args[0]], 1
        if obj.separator and obj.separator not in args[0]:
            return obj.name, [args[1]], 2

        key, *vals = self.split_assignment(obj, args[0])
        if key != obj.name:
            msg = "Assignment doesn't match"
            raise ArgParseError(msg, key, obj.name)
        return obj.name, [vals[0]], 1

    ##--| utils

    def coerce_types(self, obj:ParamSpec_i, key:str, value:list[str]) -> dict:
        """ coerce the parsed values to the expected type """
        x       : Any
        result  : dict[str, Any]  = {}
        match obj.type_, value:
            case x, y if x is type(y):
                result[key] = y
            case builtins.bool, [bool() as y]:
                result[key] = y
            case builtins.bool, y:
                result[key] = bool(y)
            case builtins.int, [*xs]: # sum a list of numbers
                result[key] = ftz.reduce(lambda x, y: x+int(y), xs, 0)
            case builtins.list, str() as x:
                result[key] = [x]
            case builtins.list, [*xs]:
                result[key] = list(xs)
            case builtins.set, [*xs]:
                result[key] = set(xs)
            case _, [x]: # unwrap things if they are a single value and not lists/sets
                result[key] = x
            case _, val:
                 result[key] = val

        return result

    def matches_head(self, obj:ParamSpec_i, val:str) -> bool:
        """ test to see if a cli argument matches this param

        Matchs {self.prefix}{self.name} if not an assignment
        Matches {self.prefix}{self.name}{separator} if an assignment
        """
        result : bool = False
        match getattr(obj, "matches_head", None):
            case None:
                key, *_ = self.split_assignment(obj, val)
                assert(isinstance(obj.key_strs, list))
                result = key in obj.key_strs and key.startswith(str(obj.prefix))
            case x:
                assert(callable(x))
                result = x(val)

        if result and self.debug:
            logging.debug("Head Matches : %s : %s", obj.name, val)
        return result

    def match_on_end(self, val:str) -> bool:
        return val == self.end_sep

    def split_assignment(self, obj:ParamSpec_i, val:str) -> list[str]:
        if obj.separator:
            return val.split(obj.separator)
        return [val]

##--|

class _ParamClassMethods:

    @staticmethod
    def build_defaults(params:Iterable[ParamSpec_i]) -> dict:
        """ Given a list of params, create a mapping of {name} -> {default value} """
        result : dict = {}
        for p in params:
            assert(isinstance(p, ParamSpec_p)), repr(p)
            if p.name in result:
                msg = "Duplicate default key found"
                raise KeyError(msg, p, params)
            result.setdefault(*p.default_tuple)

        return result

    @staticmethod
    def check_insists(params:Iterable[ParamSpec_i], data:dict) -> None:
        missing = []
        for p in params:
            if p.insist and p.name not in data:
                missing.append(p.name)
        else:
            if bool(missing):
                msg = "Missing Required Params"
                raise ArgParseError(msg, missing)

    @classmethod
    def key_func(cls, x:ParamSpec_i) -> tuple:
        """ Sort Parameters

        -{prefix len} < name < int positional < positional < --help

        Positionals with explicit positions are sorted by that,
        With remaiing going after
        Help Always goes last.

        """
        match x.prefix:
            case _ if x.name == "help":
                return (_SortGroups_e.last, 99, x.prefix, x.name)
            case str():
                return (_SortGroups_e.by_prefix, len(x.prefix), x.prefix, x.name)
            case int() as p:
                return (_SortGroups_e.by_pos, p, x.prefix or 99, x.name)

class ParamSpec[*T](_ParamClassMethods, ParamSpec_i, SubAlias_m, fresh_registry=True):
    """ Declarative CLI Parameter Spec.

    | Declares the param name (turns into {prefix}{name})
    | The value will be parsed into a given {type}, and lifted to a list or set if necessary
    | If given, can have a {default} value.
    | {insist} will cause an error if it isn't parsed

    If {prefix} is a non-empty string, then its positional, and to parse it requires no -key.
    If {prefix} is an int, then the parameter has to be in the correct place in the given args.

    Can have a {desc} to help usage.
    Can be set using a short version of the name ({prefix}{name[0]}).
    If {implicit}, will not be listed when printing a param spec collection.

    """
    ##--| classvars
    _processor           : ClassVar[ParamProcessor]  = ParamProcessor()
    _accumulation_types  : ClassVar[list[Any]]       = [int, list, set]
    _pad                 : ClassVar[int]             = 15
    ##--| internal
    _short     : Maybe[str]
    _subtypes  : dict[type, type]

    def __init__(self, **kwargs:Any) -> None:  # noqa: ANN401
        if bool({"prefix", "separator"} & kwargs.keys()):
            msg = "Don't specify prefix or separator explicitly, format the 'name' fully"
            raise KeyError(msg)
        super().__init__()
        match self._processor.parse_name(cast("str", kwargs.get("name"))):
            case dict() as ns:
                kwargs.update(ns)
            case _:
                pass

        self.name       = kwargs.pop("name")
        self.prefix     = kwargs.pop("prefix", API.DEFAULT_PREFIX)
        self.separator  = kwargs.pop("separator", False)
        self.type_      = kwargs.pop("type", None)
        self.insist     = kwargs.pop("insist", False)
        self.default    = kwargs.pop("default", None)
        self.desc       = kwargs.pop("desc", API.DEFAULT_DOC)
        self.count      = kwargs.pop("count", API.DEFAULT_COUNT)
        self.implicit   = kwargs.pop("implicit", False)

        self._short     =  None
        self._subtypes  =  {}

        self.validate_type()
        self.validate_default()

    ##--| dunders

    @override
    def __hash__(self) -> int:
        return hash(repr(self))

    @override
    def __repr__(self) -> str:
        match self.prefix:
            case str():
                return f"<{self.__class__.__name__}: {self.prefix}{self.name}>"
            case int():
                return f"<{self.__class__.__name__}: <{self.prefix}>{self.name}>"
            case x:
                raise TypeError(type(x))

    @override
    def __eq__(self, other:object) -> bool:
        match other:
            case API.ParamSpec_p() if type(self) is not type(other):
                    return False
            case API.ParamSpec_p(name=self.name, prefix=self.prefix, type_=self.type_, separator=self.separator): # type: ignore[misc]
                return True
            case _:
                return False

    ##--| validators

    def validate_type(self) -> None:  # noqa: PLR0912
        """ """
        remap          : Any = None
        x              : Any
        override_type  : Maybe[type]  = getattr(self.__class__, self.__class__._annotate_to, None)
        match self.type_:
            case None | builtins.bool if override_type:
                self.type_ = override_type
            case typing.Any:
                self.type_ = None
                return
            case types.GenericAlias() as alias: # unwrap aliases
                self.type_ = alias.__origin__
                return
            case type() as x if isinstance(x, ParamSpec_p):
                msg = "Can't use a paramstruct as the type of a paramstruct"
                raise TypeError(msg, x)
            case type() as x if x is not bool:
                return
            case str() as x:
                remap = x
            case _:
                pass

        match self.cls_annotation():
            case _ if remap is not None:
                pass
            case None | ():
                remap = bool
            case [x]:
                remap = x
            case str() | type() | types.GenericAlias() as x:
                remap = x
            case x:
                raise TypeError(type(x))

        match API.TYPE_CONV_MAPPING.get(remap, remap):
            case types.GenericAlias() as x:
                self.type_ = x.__origin__
            case typing.Any:
                self.type_ = None
            case type() as x if not issubclass(x, ParamSpec):
                self.type_ = x
            case x:
                msg = "Bad Type for ParamSpec"
                raise TypeError(msg, x)

    def validate_default(self) -> None:
        match self.default:
            case "None":
                self.default = None
            case _:
                 pass

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
            case types.GenericAlias() as x:
                self.default = self.default or x.__origin__
            case _:
                self.default = None

    ##--| properties

    @override
    @ftz.cached_property
    def short(self) -> str:
        return self._short or self.name[0]

    @override
    @ftz.cached_property
    def inverse(self) -> str:
        return f"no-{self.name}"

    @override
    @ftz.cached_property
    def repeatable(self) -> bool:
        return self.type_ in ParamSpec._accumulation_types

    @override
    @ftz.cached_property
    def key_str(self) -> str:
        """ Get how the param needs to be written in the cli.

        | eg: -test or --test
        """
        match self.prefix:
            case str():
                return f"{self.prefix}{self.name}"
            case _:
                return self.name

    @override
    @ftz.cached_property
    def short_key_str(self) -> Maybe[str]:
        match self.prefix:
            case str():
                return f"{self.prefix}{self.short}"
            case _:
                return None

    @override
    @ftz.cached_property
    def key_strs(self) -> list[str]:
        """ all available key-str variations """
        result = [self.key_str]
        match self.short_key_str:
            case str() as x:
                result.append(x)
            case None:
                pass

        match self.prefix:
            case str():
                inv = f"{self.prefix}{self.inverse}"
                result.append(inv)
            case _:
                pass

        return result

    @override
    @ftz.cached_property
    def default_value(self) -> Any:
        match self.default:
            case type() as ctor:
                return ctor()
            case x if callable(x):
                return x()
            case x:
                return x

    @override
    @ftz.cached_property
    def default_tuple(self) -> tuple[str, Any]:
        return self.name, self.default_value

    ##--| methods

    @override
    def consume(self, args:list[str], *, offset:int=0) -> Maybe[tuple[dict, int]]:
        return self._processor.consume(self, args, offset=offset)

    def help_str(self, *, force:bool=False) -> str:
        parts : list
        if self.implicit and not force:
            return ""

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
