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

BodyEntry      : TypeAlias                 = str|int|UUID

class _Strang_cmp_m:

    def __le__(self, other) -> bool:
        return (self == other) or (self < other)

    def __contains__(self, other) -> bool:
        """ test for conceptual containment of names
        other(a.b.c) ∈ self(a.b) ?
        ie: self < other
        """
        match other:
            case Strang_m() if len(self.body) > len(other.body):
                # a.b.c.d is not in a.b
                return False
            case Strang_m():
                group_matches = all(x==y for x,y in zip(self.group, other.group))
                body_matches = all(x==y for x,y in zip(self.body, other.body))
                return group_matches and body_matches
            case str():
                return other in str(self)
            case _:
                return False

    def match_version(self, other) -> bool:
        """ match version constraints of two task names against each other """
        raise NotImplementedError()

class _Strang_validation_m:

    def _process(self) -> tuple[list[slice], list[slice], list|dict]:
        """ Get slices of the strang to describe group and body components """
        group_slices, body_slices, params = [], [], {}
        index     = 0
        sep_index = self.find(self._separator)
        offset    = len(self._subseparator)
        if sep_index == -1 or self.count(self._separator) > 1:
            raise ValueError("Strang lacks a group{sep}body structure", str(self))
        # Get the group slices:
        while -1 < index:
            match self.find(self._subseparator, index, sep_index):
                case -1 if index == sep_index:
                    index = -1
                case -1:
                    group_slices.append(slice(index, sep_index))
                    index = -1
                case x:
                    group_slices.append(slice(index, x))
                    index = x + offset

        # And the body
        index     = sep_index + offset
        end       = len(self)
        while -1 < index:
            match self.find(self._subseparator, index):
                case -1 if index == end:
                    index = -1
                case -1:
                    body_slices.append(slice(index, len(self)))
                    index = -1
                case x:
                    body_slices.append(slice(index, x))
                    index = x + offset

        return (group_slices, body_slices, params)

    def _post_process(self) -> None:
        """
        go through body elements, and parse UUIDs, markers, params
        """
        raise NotImplementedError()

    def _build_uuids(self):
        pass

    def _build_marks(self):
        pass

    @classmethod
    def _pre_validate(cls, data:str|dict) -> None:
        match data:
            case str() if 1 < str.count(data, cls._separator) < 2:
                pass
            case {"base": base} if 1 <= str.count(base, cls._separator) < 2:
                pass
            case _:
                raise ValueError("Base data not malformed", data)

class _Strang_test_m:

    def is_instantiated(self) -> bool:
        """ utility method to test if this name refers to a concrete task """
        raise NotImplementedError()

    def has_root(self) -> bool:
        """ Test for if the name has a a root marker, not at the end of the name"""
        raise NotImplementedError()

class _Strang_subgen_m:
    """ Operations Mixin for manipulating TaskNames """

    def head(self) -> Strang:
        """ generate a canonical group/completion task name for this name
        eg: (concrete) group::simple.task..$gen$.<UUID> ->  group::simple.task..$gen$.<UUID>..$group$
        eg: (abstract) group::simple.task. -> group::simple.task..$group$

        """
        raise NotImplementedError()

    def canon(self) -> Strang:
        """ canonical cleanup name """
        raise NotImplementedError()

    def root(self):
        return self.pop(top=True)

    def pop(self, *, top=False) -> Strang:
        """
        Strip off one root marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub.
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c.

        """
        raise NotImplementedError()

    def push(self) -> TaskName:
        """ Add a root marker if the last element isn't already a root marker
        eg: group::a.b.c => group.a.b.c.
        (note the trailing '.')
        """
        raise NotImplementedError()

    def extend(self, *subtasks, **kwargs) -> Strang:
        """ generate an extended name, with more information
        eg: a.group::simple.task
        ->  a.group::simple.task..targeting.something

        adds a root marker to recover the original
        """
        raise NotImplementedError()

    def instantiate(self, *, prefix=None) -> Strang:
        """ Generate a concrete instance of this name with a UUID appended,
        optionally can add a prefix
          # TODO possibly do $gen$.{prefix?}.<UUID>

          ie: a.task.group::task.name..{prefix?}.$gen$.<UUID>
        """
        raise NotImplementedError()

    def uninstantiate(self) -> Strang:
        """ take a name and remove the $gen$.{prefix?}.<UUID> parts """
        raise NotImplementedError()

    def last(self) -> None|BodyEntry:
        """
        Get the last value of the task/body
        """
        return self.body[-1]

class _Strang_format_m:

    def __format__(self, spec) -> str:
        """ format additions for structured strings:
          {:h} = print only the group_str
          {:t} = print only the body_str
          {:p} = print only the params_str

          """
        relevant   = FMT_PATTERN.search(spec)
        remaining  = FMT_PATTERN.sub("", spec)
        result     = []
        if bool(relevant[1]):
            result.append(self.group_str())
        if bool(relevant[2]):
            result.append(self.body_str())
        if bool(relevant[3]) and bool(self.params):
            result.append(str(self.params))

        return format(self._sep.join(result), remaining)

class Strang_m(_Strang_validation_m, _Strang_cmp_m, _Strang_subgen_m, _Strang_test_m, _Strang_format_m):
    pass
