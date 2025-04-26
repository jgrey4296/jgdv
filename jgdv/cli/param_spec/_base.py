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

# ##-- 3rd party imports
from pydantic import BaseModel, Field, InstanceOf, field_validator, model_validator

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Proto
from jgdv._abstract.pydantic_proto import ProtocolModelMeta
from jgdv.mixins.annotate import SubAnnotate_m
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from jgdv.cli.errors import ArgParseError
from .._interface import ParamStruct_p, DEFAULT_PREFIX
from ._mixins import _ConsumerArg_m, _DefaultsBuilder_m, _ParamNameParser_m

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any, Callable, Literal
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
from jgdv import Maybe
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
PSpecMixins                    = [
    SubAnnotate_m,
    _ParamNameParser_m,
    _ConsumerArg_m,
    _DefaultsBuilder_m,
]

@Proto(ParamStruct_p)
class ParamSpecBase(*PSpecMixins, BaseModel, metaclass=ProtocolModelMeta, arbitrary_types_allowed=True, extra="allow"):
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

    name                 : str
    type_                : InstanceOf[type]          = Field(default=bool, alias="type")

    insist               : bool                      = False
    default              : Any|Callable              = None
    desc                 : str                       = "An Base Parameter"
    count                : int                       = 1
    prefix               : int|str                   = DEFAULT_PREFIX
    separator            : str|Literal[False]        = False

    implicit             : bool                      = False
    _short               : Maybe[str]                = None
    _accumulation_types  : ClassVar[list[Any]]       = [int, list, set]
    _pad                 : ClassVar[int]             = 15

    _subtypes            : dict[type, type]          = {}


    @staticmethod
    def key_func(x):
        """ Sort Parameters

        > -{prefix len} < name < int positional < positional < --help

        """
        match x.prefix:
            case _ if x.name == "help":
                return (_SortGroups_e.last, 99, x.prefix, x.name)
            case str():
                return (_SortGroups_e.by_prefix, len(x.prefix), x.prefix, x.name)
            case int() as p:
                return (_SortGroups_e.by_pos, p, x.prefix or 99, x.name)

    @field_validator("type_", mode="before")
    def validate_type(cls, val:str|type) -> type:
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
            case types.GenericAlias():
                return val.__origin__
            case typing.Any:
                return Any
            case type() as x if not issubclass(x, ParamSpecBase):
                return x
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
    def validate_model(self) -> Self:
        match self.prefix:
            case str() if bool(self.prefix) and self.name.startswith(self.prefix):
                raise TypeError("Prefix was found in the base name", self, self.prefix)

        match self._get_annotation():
            case None:
                pass
            case x:
                self.type_ = self.validate_type(x)


        if self.type_ is bool and (override_type:=getattr(self.__class__, self.__class__._annotate_to, None)):
            self.type_ = override_type

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

        | eg: -test or --test
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

    def help_str(self, *, force=False):
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

    def __repr__(self):
        if self.positional:
            return f"<{self.__class__.__name__}: {self.name}>"
        return f"<{self.__class__.__name__}: {self.prefix}{self.name}>"
