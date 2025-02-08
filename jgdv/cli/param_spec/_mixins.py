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

from jgdv.cli.errors import ArgParseError

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

