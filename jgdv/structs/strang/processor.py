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
from . import errors
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

class StrangBasicProcessor(API.PreProcessor_p):
    """ A processor for basic strangs,
    the instance is assigned into Strang._processor

    If the strang type implements _{call}_h,
    the processor uses that for a stage instead
    """

    def pre_process[T:Strang_i](self, cls:type[Strang_i], data:Any, *args:Any, strict:bool=False, **kwargs:Any) -> tuple[str, dict]: # noqa: ANN401
        """ run before str.__new__ is called,
        to do early modification of the string
        Filters out extraneous duplicated separators
        """
        text : str
        match getattr(cls, name_to_hook("pre_process"), None):
            case x if callable(x):
                return x(cls, data, *args, strict=strict, **kwargs)
            case None:
                pass

        case = cls.section(-1).case
        text = case.join(str(x) for x in [data, *args])

        if not self._verify_structure(cls, text):
            raise ValueError(errors.MalformedData, text)

        clean = self._clean_separators(cls, text).strip()
        return self._compress_types(cls, clean)

    def _verify_structure(self, cls:type[Strang_i], val:str) -> bool:
        """ Verify basic strang structure.

        ie: all necessary sections are, provisionally, there.
        """
        seps = [x.end for x in cls._sections.order if x.end is not None and x.required]
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
    def _compress_types(self, cls:type[Strang_i], val:str) -> tuple[str, dict]:  # noqa: ARG002
        """ if there's an explicit uuid, extract its value and build it """
        curr       : re.Match
        text       : list  = []
        extracted  : dict  = {}
        idx        : int   = 0
        for curr in API.TYPE_ITER_RE.finditer(val):
            match curr.groups():
                case ["<", "uuid", *_] if "uuid" in extracted:
                    raise errors.StrangError(errors.TooManyUUIDs)
                case ["<", str() as key, full_spec, ">"] if key == "uuid":
                    if bool(full_spec):
                        extracted[key]  = UUID(full_spec)
                    else:
                        extracted[key] = uuid1()
                    _,start         = curr.span(2)
                    rest,end        = curr.span(4)
                    text.append(val[idx:start])
                    text.append(val[rest:end])
                    idx = end
                case ["<", str() as other, str() as oval, ">"]:  # noqa: F841
                    pass
        else:
            text.append(val[idx:])
            return "".join(text), extracted

    ##--|

    def process(self, obj:Strang_i) -> Maybe[Strang_i]:
        """ slice the sections of the strang

        populates obj.data:
        - slices
        - flat
        - bounds
        """
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
            offset = sec.stop
            if bool(words):
                offset = sec.stop + extend
        else:
            obj.data.bounds = tuple(sec_slices)
            obj.data.slices = tuple(word_slices) # type: ignore[arg-type]
            obj.data.flat   = tuple(flat_slices)
            return None

    def _process_section(self, obj:Strang_i, section:API.Sec_d, offset:int=0) -> tuple[slice, tuple[slice], int]:
        """ Set the slices of a section, return the index where the section ends """
        sec_slice     : slice[int, int]
        word_slices   : tuple[slice]
        search_bound  : int  = offset
        bound_extend  : int  = 0
        match section.end:
            case None | "":
                search_bound = len(obj)
            case str() as x:
                try:
                    bound_extend  = len(x)
                    search_bound  = obj.index(x, start=offset)
                except (ValueError, TypeError):
                    pass
        ##--|
        word_slices = self._slice_section(obj,
                                          case=[section.case, section.end],
                                          start=offset,
                                          max=search_bound)
        sec_slice  = slice(offset, search_bound)

        return sec_slice, word_slices, bound_extend

    def _slice_section(self, obj:Strang_i, *, case:list[Maybe[str]], start:int=0, max:int=-1) -> tuple[slice]:  # noqa: A002
        """ Get a list of word slices of a section, with an offset. """
        curr    : re.Match
        slices  : list[slice]  = []
        end                    = max or len(obj)
        escaped                = "|".join(re.escape(x) for x in case if x is not None)
        reg                    = re.compile(f"(.*?)({escaped}|$)")
        words                  = []
        for curr in reg.finditer(cast("str", obj), start, end):
            span = curr.span(1)
            if span[0] == end:
                continue
            slices.append(slice(*span))
            words.append(obj[span[0]:span[1]])
        else:
            return cast("tuple[slice]", tuple(slices))

    ##--|

    def post_process(self, obj:Strang_i) -> Maybe[Strang_i]:
        """ Abstract no-op to do additional post-processing extraction of metadata """
        match getattr(obj, name_to_hook("process"), None):
            case x if callable(x):
                return x()
            case _:
                logging.debug("Post-processing Strang: %s", str.__str__(obj))
                metas : list = []
                for i in range(len(obj.sections())):
                    metas.append(self._post_process_section(obj, i))
                else:
                    obj.data.meta = tuple(metas)  # type: ignore[assignment]
                    self._validate_marks(obj)
                    self._calc_obj_meta(obj)
                    return None

    def _post_process_section(self, obj:Strang_i, idx:int) -> tuple:
        match obj.section(idx).marks:
            case None:
                return ()
            case type() as m if issubclass(m, API.StrangMarkAbstract_e):
                marks = m
            case m:
                raise TypeError(m)

        count     : int                                             = len(obj.data.slices[idx])
        meta      : list[Maybe[UUID|API.StrangMarkAbstract_e|int]]  = [None for x in range(count)]
        new_uuid  : Maybe[UUID]                                     = obj.data.uuid

        for i, elem_slice in enumerate(obj.data.slices[idx]):
            elem                                                    = obj[elem_slice]
            assert(isinstance(elem, str))
            # Discriminate the str
            match elem:
                case x if (uuid_mark:=self._make_uuid_mark(x)) is not None:
                    assert(obj.data.uuid)
                    meta[i] = uuid_mark
                case x if (mark_elem:=self._build_mark(x, marks)) is not None:
                    logging.debug("(%s) Found Named Marker: %s", i, mark_elem)
                    meta[i] = mark_elem
                case x if (mark_elem:=self._implicit_mark(x, marks, first_or_last=(i in {0,count-1}))) is not None:
                    logging.debug("(%s) Found Named Marker: %s", i, mark_elem)
                    meta[i] = mark_elem
                case x if (int_elem:=self._make_int(x)) is not None:
                    meta[i] = int_elem
                case _: # nothing special
                    pass
        else:
            obj.data.uuid = new_uuid
            return tuple(meta)

    def _calc_obj_meta(self, obj:Strang_i) -> None:
        """ Set object level meta dict

        ie: mark the obj as an instance
        """
        pass

    def _validate_marks(self, obj:Strang_i) -> None:
        """ Check marks make sense.
        eg: +|_ are only at obj[1:0]

        """
        pass

    ##--| utils

    def _make_uuid_mark(self, val:str) -> Maybe[API.StrangMarkAbstract_e]:
        """ Handle <uuid> and <uuid:{val}>.
        matches using strang._interface.TYPE_RE

        The former creates a new uuid1,
        The latter re-creates a specific uuid

        """
        if not (data:=API.TYPE_RE.match(val)):
            return None

        match data.groups():
            case ["uuid", None]:
                return API.DefaultBodyMarks_e.unique
            case x:
                raise TypeError(type(x))
        return None

    def _build_mark(self, val:str, marks:type[API.StrangMarkAbstract_e]) -> Maybe[API.StrangMarkAbstract_e]:
        """ converts applicable words to mark enum values
        Matches using strang._interface.MARK_RE

        """
        match API.MARK_RE.match(val):
            case re.Match() as x if (key:=x[1].lower()) in marks:
                return marks(key)
            case _:
                return None

    def _implicit_mark(self, val:str, marks:type[API.StrangMarkAbstract_e], *, first_or_last:bool) -> Maybe[API.StrangMarkAbstract_e]:
        """ Builds certain implicit marks,
        but only for the first and last words of a section

        # TODO handle combined marks like val::+_.blah

        """
        match marks.skip():
            case None:
                pass
            case x if val == x:
                return x

        if not (first_or_last and val in marks):
            return None
        return marks(val)

    def _make_int(self, val:str) -> Maybe[int]:
        try:
            return int(val)
        except ValueError:
            return None

class CodeRefProcessor(StrangBasicProcessor):
    pass
