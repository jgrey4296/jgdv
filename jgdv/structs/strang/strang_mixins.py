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
    Annotated,
    Any,
    Callable,
    Self,
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

from pydantic import BaseModel, Field, field_validator

BodyEntry      : TypeAlias                 = str|int|UUID
UUID_RE        : Final[re.Pattern]         = re.compile(r"<uuid(?::(.+?))?>")
MARK_RE        : Final[re.Pattern]         = re.compile(r"\$(.+?)\$")
INST_K         : Final[str]                = "instanced"
GEN_K          : Final[str]                = "gen_uuid"

class StrangMarker_e(enum.StrEnum):
    """ Markers Used in a Strang """

    head     = "$head$"
    gen      = "$gen$"
    mark     = ""
    hide     = "_"
    extend   = "+"

class _Strang_validation_m:

    @classmethod
    def pre_process(cls, data:str) -> str:
        """ run before str.__new__ is called, so can do early modification of the string """
        # TODO expand <uuid> tags here
        # TODO chop off tail [param] here
        match data:
            case cls() | str() if 0 < str.count(data, cls._separator):
                return str(data).removesuffix(cls._subseparator).removesuffix(cls._subseparator)
            case _:
                raise ValueError("Base data malformed", data)

    def _process(self) -> tuple[list[slice], list[slice], list|dict]:
        """ Get slices of the strang to describe group and body components """
        logging.debug("Processing Strang: %s", self)
        index     = 0
        sep_index = self.find(self._separator)
        if sep_index == -1:
            raise ValueError("Strang lacks a group{sep}body structure", str(self))

        self._group += self._get_slices(0, sep_index)
        self._body  += self._get_slices(sep_index, add_offset=True)
        self._base_slices = (slice(self._group[0].start, self._group[-1].stop),
                             slice(self._body[0].start, self._body[-1].stop))

    def _get_slices(self, start:int=0, max:None|int=None, add_offset:bool=False):
        index, end, offset = start, max or len(self), len(self._subseparator)
        if add_offset:
            index += len(self._separator)
        slices    = []
        # Get the group slices:
        while -1 < index:
            match self.find(self._subseparator, index, end):
                case -1 if index == end:
                    index = -1
                case -1:
                    slices.append(slice(index, end))
                    index = -1
                case x:
                    slices.append(slice(index, x))
                    index = x + offset
        else:
            return slices

    def _post_process(self) -> None:
        """
        go through body elements, and parse UUIDs, markers, param
        """
        logging.debug("Post-processing Strang: %s", self)
        max_body = len(self._body)
        self._body_objs = [None for x in range(max_body)]
        mark_idx : tuple[int, int] = (max_body, -1)
        for i, elem in enumerate(self.body()):
            match elem:
                case x if (match:=UUID_RE.match(x)):
                    self.metadata[INST_K] = min(i, self.metadata.get(INST_K, max_body))
                    hex, *_ = match.groups()
                    if hex is not None:
                        logging.debug("(%s) Found UUID", i)
                        self._body_objs[i] = UUID(match[1])
                    else:
                        logging.debug("(%s) Generating UUID", i)
                        self._body_objs[i] = uuid1()
                        self.metadata[GEN_K] = True
                case x if (match:=MARK_RE.match(x)) and (x_l:=match[1].lower()) in self.mark_e.__members__:
                    # Get explicit mark,
                    logging.debug("(%s) Found Named Marker: %s", i, x_l)
                    self._body_objs[i] = self.mark_e[x_l]
                    mark_idx = (min(mark_idx[0], i), max(mark_idx[1], i))
                case "_" if i < 2: # _ and + coexist
                    self._body_objs[i] = self.mark_e.hide
                    mark_idx = (min(mark_idx[0], i), max(mark_idx[1], i))
                case "+" if i < 2: # _ and + coexist
                    self._body_objs[i] = self.mark_e.extend
                    mark_idx = (min(mark_idx[0], i), max(mark_idx[1], i))
                case "":
                    self._body_objs[i] = self.mark_e.mark
                    mark_idx = (min(mark_idx[0], i), max(mark_idx[1], i))
                case _:
                    self._body_objs[i] = None
        else:
            # Set the root and last mark_idx for popping
            match mark_idx:
                case (x, -1):
                    mark_idx = (x, x)
                case (x, y):
                    pass

            self._mark_idx = mark_idx

class _Strang_cmp_m:

    def __hash__(self):
        return str.__hash__(str(self))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, _Strang_cmp_m):
            raise NotImplementedError()

        if not len(self) < len(other):
            return False

        if not self[0:] == other[0:]:
            return False

        for x,y in zip(self.body(), other.body()):
            if x != y:
                return False

        return True

    def __le__(self, other) -> bool:
        return hash(self) == hash(other) or (self < other)

class _Strang_subgen_m:
    """ Operations Mixin for manipulating TaskNames """

    @classmethod
    def _subjoin(cls, lst) -> str:
        return cls._subseparator.join(lst)

    def canon(self) -> Self:
        """ canonical name. no UUIDs"""
        group = self[0:]
        canon_body = self._subjoin(self.body(reject=lambda x: isinstance(x, UUID)))

        return self.__class__(f"{group}{self._separator}{canon_body}")

    def pop(self, *, top=False) -> Self:
        """
        Strip off one marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c
        """
        group : str       = self[0:]
        end_id            = self._mark_idx[0 if top else 1]
        return self[2:end_id]

    def push(self, *vals:str) -> Self:
        """ Add a root marker if the last element isn't already a root marker
        eg: group::a.b.c => group.a.b.c.
        (note the trailing '.')
        """
        return self.__class__(self._subjoin(x for x in [self, "", *vals] if x is not None))

    def to_uniq(self, *, suffix=None) -> Self:
        """ Generate a concrete instance of this name with a UUID appended,
        optionally can add a prefix
          # TODO possibly do $gen$.{prefix?}.<UUID>

          ie: a.task.group::task.name..{prefix?}.$gen$.<UUID>
        """
        return self.push(self.mark_e.gen, "<uuid>", suffix)

    def de_uniq(self) -> Self:
        return self[2:self.metadata.get(INST_K, None)].pop()

    def with_head(self) -> Self:
        """ generate a canonical group/completion task name for this name
        eg: (concrete) group::simple.task..$gen$.<UUID> ->  group::simple.task..$gen$.<UUID>..$group$
        eg: (abstract) group::simple.task. -> group::simple.task..$group$

        """
        return self.push(self.mark_e.head)

    def root(self) -> Self:
        return self.pop(top=True)

class _Strang_test_m:

    @property
    def is_uniq(self) -> bool:
        """ utility method to test if this name refers to a name with a UUID """
        return INST_K in self.metadata

    def __contains__(self, other) -> bool:
        """ test for conceptual containment of names
        other(a.b.c) ∈ self(a.b) ?
        ie: self < other
        """
        match other:
            case UUID():
                return other in self._body_objs
            case str():
                return other in str(self)
            case _:
                return False

class _Strang_format_m:

    def __format__(self, spec) -> str:
        """ format additions for strangs:
          {strang:g} = print only the group
          {strang:b} = print only the body

          """
        match spec:
            case "g":
                return self[0:]
            case "b":
                return self[1:]

class _Strang_annotation_m:
    """
    Enable Strang[int] and Strang['blah'] subclasses variants,
    to annotate the purpose of the Strang

    TODO maybe use an explicit cache instead of ftz.cache
    """

    @classmethod
    @ftz.cache
    def __class_getitem__(cls, param) -> Annotated[_Strang_annotation_m]:
        """ Auto-subclass as {cls.__name__}[param]"""
        match param:
            case type():
                p_str = param.__name__
            case str():
                p_str = param

        sub = type(f"{cls.__name__}[{p_str}]", (cls,), {"_typevar":param})
        return sub


class Strang_m(_Strang_annotation_m, _Strang_validation_m, _Strang_cmp_m, _Strang_subgen_m, _Strang_test_m, _Strang_format_m):
    pass
