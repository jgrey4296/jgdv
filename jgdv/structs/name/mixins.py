#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from tomlguard import TomlGuard
from pydantic import BaseModel, Field, field_validator

def aware_splitter(x, sep=".") -> list[str]:
    match x:
        case str():
            return x.split(sep)
        case _:
            return [x]

class _StrStruct_cmp_m:

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return self._separator.join([self.head_str(), self.tail_str()])

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other) -> bool:
        """ test for hierarhical ordering of names
        eg: self(a.b.c) < other(a.b.c.d)
        ie: other ∈ self
        """
        match other:
            case StrStruct_m():
                pass
            case str():
                other = self.__class__.build(other)
            case _:
                return False

        if len(self.head) != len(other.head):
            return False
        if len(self.tail) >= len(other.tail):
            return False

        for x,y in zip(self.head, other.head):
            if x != y:
                return False

        for x,y in zip(self.tail, other.tail):
            if x != y:
                return False

        return True

    def __le__(self, other) -> bool:
        return (self == other) or (self < other)

    def __contains__(self, other) -> bool:
        """ test for conceptual containment of names
        other(a.b.c) ∈ self(a.b) ?
        ie: self < other
        """
        match other:
            case StrStruct_m() if len(self.tail) > len(other.tail):
                # a.b.c.d is not in a.b
                return False
            case StrStruct_m():
                head_matches = all(x==y for x,y in zip(self.head, other.head))
                tail_matches = all(x==y for x,y in zip(self.tail, other.tail))
                return head_matches and tail_matches
            case str():
                return other in str(self)
            case _:
                return False

class _StrStruct_substr_m:

    def tail_str(self) -> str:
        return self._subseparator.join(str(x) for x in self.tail)

    def head_str(self) -> str:
        return self._subseparator.join(str(x) for x in self.head)

class _StrStruct_validation_m:

    def _process_head(self, head:str) -> list[str]:
        result = []
        for part in [x for x in head.split(self._subseparator) if bool(x)]:
            result.append(part.removeprefix('"').removesuffix('"'))

        return result

    def _process_tail(self, tail:str) -> list[str]:
        result = []
        for part in [x for x in tail.split(self._subseparator)]:
            result.append(part.removeprefix('"').removesuffix('"'))

        return result

    def _process_params(self, params:str) -> None|list|dict|TomlGuard:
        if not bool(params):
            return None

        return TomlGuard.read(f"params = {params}").params

    def _process(self) -> tuple[list[str], list[str], list|dict]:
        raw_head, _, raw_tail_w_params = self.base.partition(self._separator)
        raw_tail, _, raw_params = raw_tail_w_params.partition(self._separator)
        return (self._process_head(raw_head.strip()),
                self._process_tail(raw_tail.strip()),
                self._process_params(raw_params.strip()))

    @classmethod
    def _pre_validate(cls, data:dict) -> None:
        if "base" not in data:
            raise KeyError("Base data not found", data)
        if not str.__contains__(data['base'], cls._separator):
            raise ValueError("Separator not found", data, cls._separator)

    def _tidy_up(self):
        """ for post-processing self.head and self.tail """
        self.tail = [x for x in self.tail if bool(x)]
        # subsplit values
        # check invariants
        # remove elements

class StrStruct_m(_StrStruct_validation_m, _StrStruct_substr_m, _StrStruct_cmp_m):
    pass
