#!/usr/bin/env python3
"""

"""
# ruff: noqa: B019, PLR2004
# mypy: disable-error-code="attr-defined,misc,override"
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import functools as ftz
import importlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports

# ##-- end 3rd party imports

from jgdv import Proto, Mixin
from . import errors
from . import _mixins as s_mix
from ._interface import FMT_PATTERN, SEP_DEFAULT, SUBSEP_DEFAULT, StrangMarker_e, UUID_RE, INST_K, GEN_K, STRGET, MARK_RE

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    import enum
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
logging.disabled = True
##-- end logging

class StrangBuilder_m:

    @staticmethod
    def build(data:str, *args:Any, **kwargs:Any) -> Strang:  # noqa: ANN401
        """ Build an appropriate Strang subclass else a Strang,
        goes from newest to oldest
        eg: For when you might have a Location or a Name, and want to try to build both
        """
        for sub in StrangMeta._forms[::-1]:
            if sub._typevar is not None:
                # Skip annotated types for now
                continue
            try:
                return sub(data, *args, strict=True, **kwargs)
            except (errors.StrangError, ValueError, KeyError):
                pass
        else:
            return Strang(data, *args, **kwargs)
##--|

class StrangMeta(type(str)):
    """ A Metaclass for Strang
    It runs the pre-processsing and post-processing on the constructed str
    to turn it into a strang
    """

    _forms : ClassVar[list[type]] = []

    def __call__(cls:type[str], data:str, *args:Any, **kwargs:Any) -> str:  # noqa: ANN401
        """ Overrides normal str creation to allow passing args to init """
        match data:
            case pl.Path():
                data = str(data)
            case cls():
                data = str(data)
            case _:
                pass

        try:
            data = cls.pre_process(data, strict=kwargs.get("strict", False))
        except ValueError as err:
            msg = "Pre-Strang Error"
            raise errors.StrangError(msg, cls, err, data) from None

        obj  = str.__new__(cls, data)
        try:
            obj.__init__(*args, **kwargs)
        except ValueError as err:
            msg = "Strang Init Error"
            raise errors.StrangError(msg, cls, err, data) from None

        try:
            # TODO don't call process and post_process if given the metadata in kwargs
            obj._process()
        except ValueError as err:
            msg = "Strang Process Error"
            raise errors.StrangError(msg, cls, err, data) from None

        try:
            # TODO allow post-process to override and return a different object?
            obj._post_process()
        except ValueError as err:
            msg = "Post-Strang Error:"
            raise errors.StrangError(msg, cls, err) from None

        return obj

##--|

@Mixin(s_mix.PreStrang_m, None, s_mix.PostStrang_m, allow_inheritance=True)
class Strang(str, metaclass=StrangMeta):
    """
      A Structured String Baseclass.
      A Normal str, but is parsed on construction to extract and validate
      certain form and metadata.

    Form: group{sep}body
    body objs can be marks (Strang.bmark_e), and UUID's as well as str's

    strang[x] and strang[x:y] are changed.

    """

    _separator        : ClassVar[str]                    = SEP_DEFAULT
    _subseparator     : ClassVar[str]                    = SUBSEP_DEFAULT
    _body_types       : ClassVar[Any]                    = str|UUID|StrangMarker_e
    _typevar          : ClassVar[Maybe[type]]            = None
    bmark_e           : ClassVar[enum.StrEnum]           = StrangMarker_e
    gmark_e           : ClassVar[enum.IntEnum|type[int]] = int

    metadata          : dict
    _base_slices      : tuple[Maybe[slice], Maybe[slice]]
    _mark_idx         : tuple[Maybe[int], Maybe[int]]
    _group            : list[slice]
    _body             : list[slice]
    _body_meta        : list[Maybe[Strang._body_types]]
    _group_meta       : set[enum.member]

    @classmethod
    def __init_subclass__(cls, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        StrangMeta._forms.append(cls)

    def _post_process(self) -> None:  # noqa: PLR0912
        """
        go through body elements, and parse UUIDs, markers, param
        setting self._body_meta and self._mark_idx
        """
        logging.debug("Post-processing Strang: %s", str.__str__(self))
        max_body        : int                    = len(self._body)
        self._body_meta : list[Maybe[UUID|str]]  = [None for x in range(max_body)]
        mark_idx        : tuple[int, int]        = (max_body, -1)
        for i, elem in enumerate(self.body()):
            match elem:
                case x if (match:=UUID_RE.match(x)):
                    self.metadata[INST_K] = min(i, self.metadata.get(INST_K, max_body))
                    hex, *_ = match.groups()  # noqa: A001
                    self.metadata[GEN_K] = True
                    if hex is not None:
                        logging.debug("(%s) Found UUID", i)
                        self._body_meta[i] = UUID(match[1])
                    else:
                        logging.debug("(%s) Generating UUID", i)
                        self._body_meta[i] = uuid1()
                case x if (match:=MARK_RE.match(x)) and (x_l:=match[1].lower()) in self.bmark_e.__members__:
                    # Get explicit mark,
                    logging.debug("(%s) Found Named Marker: %s", i, x_l)
                    self._body_meta[i] = self.bmark_e[x_l]  # type: ignore[index]
                    mark_idx = (min(mark_idx[0], i), max(mark_idx[1], i))
                case "_" if i < 2: # _ and + coexist
                    self._body_meta[i] = self.bmark_e.hide
                    mark_idx = (mark_idx[0], max(mark_idx[1], i))
                case "+" if i < 2: # _ and + coexist
                    self._body_meta[i] = self.bmark_e.extend
                    mark_idx = (mark_idx[0], max(mark_idx[1], i))
                case "":
                    self._body_meta[i] = self.bmark_e.mark
                    mark_idx = (min(mark_idx[0], i), max(mark_idx[1], i))
                case _:
                    self._body_meta[i] = None
        else:
            # Set the root and last mark_idx for popping
            match mark_idx:
                case (int() as x, -1):
                    self._mark_idx = (x, x)  # type: ignore[assignment]
                case (int() as x, 0):
                    self._mark_idx = (x, x)  # type: ignore[assignment]
                case (_, _):
                    self._mark_idx = mark_idx


    def __init__(self, *_:Any, **kwargs:Any) -> None:  # noqa: ANN401
        super().__init__()
        self.metadata     = dict(kwargs)
        # For easy head and body str's
        self._base_slices = (None,None)
        self._mark_idx    = (None,None)
        self._group       = []
        self._body        = []
        self._body_meta   = []
        self._group_meta  = set()

    def __str__(self) -> str:
        match self.metadata.get(GEN_K, False):
            case False:
                return super().__str__()
            case _:
                return self._expanded_str()

    def __repr__(self) -> str:
        body = self._subjoin(self.body(no_expansion=True))
        cls = self.__class__.__name__
        return f"<{cls}: {self[0:]}{self._separator}{body}>"

    def __iter__(self) -> Iterator[Strang._body_types]:
        """ iterate the body *not* the group """
        for x in range(len(self._body)):
            yield self[x]

    def __getitem__(self, i:int|slice) -> Strang._body_types|Strang:  # noqa: PLR0911
        """
        strang[x] -> get a body obj or str
        strang[0:x] -> a head str
        strang[0:] -> the entire head str
        strang[1:x] -> a body obj
        strang[1:] -> the entire body str
        strang[2:x] -> clone up to x of body
        """
        match i:
            case int():
                return self._body_meta[i] or super().__getitem__(self._body[i])
            case slice(start=0, stop=None):
                return super().__getitem__(self._base_slices[0])
            case slice(start=1, stop=None, step=None):
                return super().__getitem__(self._base_slices[1])
            case slice(start=0, stop=x):
                return super().__getitem__(self._group[x])
            case slice(start=1, stop=int() as x):
                return self._body_meta[x] or super().__getitem__(self._body[x])
            case slice(start=1, stop=x, step=y):
                return super().__getitem__(slice(self._body[x or 0].start, self._body[y].stop))
            case slice(start=2, stop=x):
                return self.__class__(self._expanded_str(stop=x))
            case slice(start=int()):
                msg = "Slicing a Strang only supports a start of 0 (group), 1 (body), and 2 (clone)"
                raise KeyError(msg, i)
            case x:
                raise TypeError(type(x))


    @property
    def base(self) -> Self:
        return self

    @property
    def group(self) -> list[str]:
        return [STRGET(self, x) for x in self._group]

    def body(self, *, reject:Maybe[callable]=None, no_expansion:bool=False) -> list[str]:
        """ Get the body, as a list of str's,
        with values filtered out if a rejection fn is used
        """
        if not bool(self._body_meta):
            return [self._format_subval(STRGET(self, x), no_expansion=no_expansion) for x in self._body]

        body = [self._body_meta[i] or STRGET(self, x) for i, x in enumerate(self._body)]
        if reject:
            body = [x for x in body if not reject(x)]

        return [self._format_subval(x, no_expansion=no_expansion) for x in body]

    @property
    @ftz.cache
    def shape(self) -> tuple[int, int]:
        return (len(self._group), len(self._body))

    def uuid(self) -> Maybe[UUID]:
        if bool(uuids:=[x for x in self._body_meta if isinstance(x, UUID)]):
            return uuids[0]
        return None
