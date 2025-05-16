#!/usr/bin/env python3
"""

"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
# ##-- end stdlib imports

from jgdv import Proto, Mixin
from jgdv.mixins.annotate import SubAnnotate_m
from . import _interface as API  # noqa: N812

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from collections.abc import Callable

if TYPE_CHECKING:
    import enum
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from ._interface import Strang_i
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Vars
HEAD_IDXS : Final[int] = 1
##--| funcs

def name_to_hook(val:str) -> str:
    return f"_{val}_h"

##--| Body

class StrangBasicProcessor(API.PreInitProcessed_p):
    """ A processor for basic strangs,
    the instance is assigned into Strang._processor

    If the strang type implements _{call}_h,
    the processor uses that for a stage instead
    """

    def pre_process(self, cls:type[Strang_i], data:str, *, strict:bool=False) -> str:
        """ run before str.__new__ is called,
        to do early modification of the string
        Filters out extraneous duplicated separators
        """
        # TODO expand <uuid> gen tags here
        match getattr(cls, name_to_hook("pre_process"), None):
            case x if callable(x):
                return x(cls, data, strict=strict)
            case None:
                pass

        if self._verify_structure(cls, data):
            clean = self._clean_separators(cls, data)
            return clean.strip()

        msg = "Base data malformed"
        raise ValueError(msg, data)

    def _verify_structure(self, cls:type[Strang_i], val:str) -> bool:
        seps = [x.end for x in cls._sections.order if x.end is not None]
        return all(x in val for x in seps)

    def _clean_separators(self, cls:type[Strang_i], val:str) -> str:
        """ Clean even repetitions of the separator down to single uses

        eg: for sep='.',
        a..b::c....d -> a.b::c.d
        but:
        a.b::c...d -> a.b::c..d
        """
        # TODO join the seps
        seps = [x.case for x in cls._sections.order]
        sep = seps[0]
        sep_double = re.escape(sep * 2)
        clean_re   = re.compile(f"{sep_double}+")
        # Don't reuse sep_double, as thats been escaped
        cleaned    = clean_re.sub(sep * 2, val)
        trimmed    = cleaned.removesuffix(sep).removesuffix(sep)
        return trimmed
    ##--|

    def process(self, obj:Strang_i) -> Maybe[Strang_i]:
        """ slice the sections of the strang and populate obj.data """
        offset      : int
        sec_slices  : list[slice]
        word_slices : list[tuple[slice, ...]]
        flat_slices : list[slice]
        match getattr(obj, name_to_hook("process"), None):
            case x if callable(x): # call the hook method
                return x()
            case None:
                pass

        logging.debug("Processing Strang: %s", str.__str__(obj))
        offset = 0
        sec_slices, word_slices, flat_slices = [], [], []
        for section in obj._sections:
            sec, words, extend = self._process_section(obj, section, offset=offset)
            sec_slices.append(sec)
            word_slices.append(words)
            flat_slices += words
            offset = sec.stop + extend
        else:
            obj.data.bounds = tuple(sec_slices)
            obj.data.slices = tuple(word_slices) # type: ignore[arg-type]
            obj.data.flat   = tuple(flat_slices)
            return None

    def _process_section(self, obj:Strang_i, section:API.Sec_d, offset:int=0) -> tuple[slice, tuple[slice], int]:
        """ Set the slices of a section, return the index where the section ends """
        sec_slice             : slice[int, int]
        word_slices           : tuple[slice]
        search_bound          : int = len(obj)
        bound_extend          : int = 0
        match section.end: # Calc Search boundary
            case str():
                search_bound  = obj.find(section.end, offset)
                bound_extend  = len(section.end)
            case None:
                search_bound  = len(obj)

        match search_bound: # Calc the Section Slice
            case -1:
                search_bound  = len(obj)
                sec_slice     = slice(offset, search_bound)
            case x:
                sec_slice = slice(offset, min(x, len(obj)))

        ##--|
        word_slices = self._slice_section(obj,
                                          case=section.case,
                                          start=offset,
                                          max=search_bound)

        return sec_slice, word_slices, bound_extend

    def _slice_section(self, obj:Strang_i, *, case:str, start:int=0, max:int=-1) -> tuple[slice]:  # noqa: A002
        """ Get a list of word slices of a section, with an offset. """
        index, end, offset = start, max or len(obj), len(case)
        slices : list[slice] = []
        while -1 < index:
            match obj.find(case, index, end):
                case -1 if index == end:
                    index = -1
                case -1:
                    slices.append(slice(index, end))
                    index = -1
                case x:
                    slices.append(slice(index, x))
                    index = x + offset
        else:
            return cast("tuple[slice]", tuple(slices))

    ##--|

    def post_process(self, obj:Strang_i) -> Maybe[Strang_i]:
        """ Abstract no-op to do additional post-processing extraction of metadata """
        match getattr(obj, name_to_hook("process"), None):
            case x if callable(x):
                return x()
            case _:
                self._default_post_process(obj)
                return None

    def _default_post_process(self, obj:Strang_i) -> None:
        """
        Extract meta information from words
        go through body elements, and parse UUIDs, markers, param
        setting obj._body_meta and obj._mark_idx
        """
        logging.debug("Post-processing Strang: %s", str.__str__(obj))
        body_marks      : Final[enum.EnumMeta]            = obj._sections[0].marks
        max_body        : int                             = len(obj.data.slices[1])
        body_meta       : list[Maybe[UUID|enum.EnumMeta]] = [None for x in range(max_body)]
        mark_idx        : tuple[int, int]                 = (max_body, -1)

        for i, elem_slice in enumerate(obj.data.slices[1]):
            elem = API.STRGET(obj, elem_slice)
            assert(isinstance(elem, str))
            match elem:
                case x if (uuid_elem:=self._make_uuid(x)) is not None:
                    logging.debug("Found UUID: %s", i)
                    body_meta[i] = uuid_elem
                    obj.meta.update({
                        API.INST_K : min(i, obj.meta.get(API.INST_K, max_body)), # type: ignore
                        API.GEN_K: True,
                    })
                case x if (mark_elem:=self._explicit_mark(x, body_marks)) is not None:
                    logging.debug("(%s) Found Named Marker: %s", i, mark_elem)
                    body_meta[i] = mark_elem
                    mark_idx = (min(mark_idx[0], i), max(mark_idx[1], i)) # update
                case x if self._is_head_elem("_", x, i):
                    # TODO move this to doot strang processor
                    body_meta[i] = body_marks.hide # type: ignore[attr-defined]
                    mark_idx = (mark_idx[0], max(mark_idx[1], i)) # update
                case x if self._is_head_elem("+", x, i):
                    # TODO move this to doot strang processor
                    body_meta[i] = body_marks.extend # type: ignore[attr-defined]
                    mark_idx = (mark_idx[0], max(mark_idx[1], i)) # update
                case x if x == body_marks.mark:
                    # TODO move to doot strang processor
                    body_meta[i] = body_marks.mark # type: ignore[attr-defined]
                    mark_idx = (min(mark_idx[0], i), max(mark_idx[1], i)) # update
                case x if (int_elem:=self._make_int(x)) is not None:
                    body_meta[i] = int_elem
                case _: # nothing special
                    pass
        else:
            # Set the root and last mark_idx for popping
            match mark_idx:
                case (int() as i, -1):
                    assert(isinstance(i, int))
                    mark_idx = (i, i)
                case (int() as i, 0):
                    assert(isinstance(i, int))
                    mark_idx = (i, i)
                case (int() as i, int() as y):
                    assert(isinstance(i, int))
                    assert(isinstance(y, int))
                    mark_idx   = (i, y)

            obj.data.meta      = (None,tuple(body_meta))  # type: ignore[assignment]
            obj.data.mark_idx  = tuple(mark_idx)          # type: ignore[assignment]

    def _make_uuid(self, val:str) -> Maybe[UUID]:
        if not (data:=API.UUID_RE.match(val)):
            return None

        match data.groups():
            case None, *_:
                return uuid1()
            case [str() as full_spec]:
                return UUID(full_spec)

        return None

    def _explicit_mark(self, val:str, marks:enum.EnumMeta) -> Maybe[enum.EnumMeta]:
        if (data:=API.MARK_RE.match(val)) is None:
            return None

        if (x_l:=data[1].lower()) not in marks.__members__:
            return  None

        # Get explicit mark,
        return marks[x_l]

    def _is_head_elem(self, cmp:str, val:str, idx:int) -> bool:
        return val == cmp and idx <= HEAD_IDXS

    def _make_int(self, val:str) -> Maybe[int]:
        try:
            return int(val)
        except ValueError:
            return None
