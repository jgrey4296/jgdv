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
from pydantic import BaseModel

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe, Proto, Mixin
from jgdv._abstract.protocols import Buildable_p
from jgdv.mixins.annotate import SubAnnotate_m, Subclasser
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from jgdv.mixins.annotate import Subclasser
from jgdv.cli.errors import ArgParseError
from ._mixins import _DefaultsBuilder_m, _ParamNameParser_m
from ._base import ParamSpecBase
from . import core
from . import assignment
from . import defaults
from . import positional

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any
from types import GenericAlias
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
from .._interface import ParamStruct_p
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(Buildable_p)
@Mixin(None, SubAnnotate_m, _DefaultsBuilder_m, _ParamNameParser_m)
class ParamSpec:
    """ A Top Level Access point for building param specs """
    _override_type  : ClassVar[type|str]    = None
    __builder       : ClassVar[Subclasser]  = Subclasser()

    def __subclasscheck__(self, subclass):
        return issubclass(subclass, ParamSpecBase)

    def __instancecheck__(self, instance):
        return isinstance(instance, ParamSpecBase)

    @staticmethod
    def _discrim_to_type(data:Maybe[type|str|tuple[str,type]]) -> Maybe[type]:
        """
        Determine what sort of parameter to use.
        Literals: assign, position, "toggle"

        Default: KeyParam

        """
        match data:
            case type() as x if x is ParamSpec:
                raise TypeError("Can't use ParamSpec as a param type, use an implementation")
            case builtins.bool|"bool"|"toggle":
                return core.ToggleParam
            case "assign":
                return assignment.AssignParam
            case "position" | int():
                return positional.PositionalParam
            case "list"|"set":
                return core.RepeatableParam
            case builtins.list|builtins.set:
                return core.RepeatableParam
            case _:
                return core.KeyParam

    @staticmethod
    def _discrim_data(data:dict) -> Maybe[type]:
        """
        Extract from data dict values to determine sort of param
        """
        match data:
            case {"separator": str(), "type": "bool"|builtins.bool}:
                raise ValueError("Don't use an assignment param for bools, use a toggle")
            case {"separator": False, "prefix":False}:
                type_param = ParamSpec._discrim_to_type("position")
            case {"separator": str()}:
                type_param = ParamSpec._discrim_to_type("assign")
            case {"prefix":int() as x}:
                type_param = ParamSpec._discrim_to_type(x)
            case {"prefix": "+"}:
                type_param = ParamSpec._discrim_to_type("toggle")
            case {"type":x}:
                type_param = ParamSpec._discrim_to_type(x)
            case _:
                type_param = ParamSpec._discrim_to_type(None)
                ##--|
        return type_param

    @classmethod
    def __class_getitem__(cls, *params):
        """ Don't parameterize this ParamSpec accessor,
        parameterize an implementation
        """
        match params:
            case []:
                return cls
            case [x, *_]:
                subtype = ParamSpec._discrim_to_type(x)
                p_sub = subtype[x]
                new_name = cls.__builder.decorate_name(cls, f"{p_sub.__name__}")
                subdata = {"_override_type": p_sub,
                           "__module__" : cls.__module__,
                           }
                new_ps  = cls.__builder.make_subclass(new_name, cls, namespace=subdata)
                assert(new_ps._override_type is p_sub)
                return new_ps

    def __new__(cls, *args, **kwargs):
        return cls.build(*args, kwargs)

    @classmethod
    def build(cls:BaseModel, data:dict) -> ParamSpecBase:
        data = dict(data)
        match cls._parse_name(data.get("name")):
            case dict() as ns:
                data.update(ns)
            case _:
                pass

        match data:
            case _ if cls._override_type:
                type_param = cls._override_type
            case dict():
                type_param = ParamSpec._discrim_data(data)
            case x:
                raise TypeError("Unexpected data type", x)

        match type_param:
            case type() as t:
                return t.model_validate(data)
            case None:
                raise TypeError("Couldn't determine type for data", data)


    @classmethod
    def key_func(cls, x):
        return x.key_func(x)
