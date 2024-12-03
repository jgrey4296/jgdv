#!/usr/bin/env python3
"""

"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
# import abc
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
import weakref
# from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports

# ##-- end 3rd party imports

from jgdv.structs.strang import strang_mixins as mixins

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

FMT_PATTERN    : Final[re.Pattern]         = re.compile("^(h?)(t?)(p?)")
SEP_DEFAULT    : Final[str]                = "::"
SUBSEP_DEFAULT : Final[str]                = "."
GEN_K          : Final[str]                = mixins.GEN_K
INST_K                                     = mixins.INST_K
UUID_RE        : Final[re.Pattern]         = re.compile(r"<uuid(?::(.+?))?>")
MARK_RE        : Final[re.Pattern]         = re.compile(r"\$(.+?)\$")

STRGET                                     = str.__getitem__
StrangMarker_e                             = mixins.StrangMarker_e

class _StrangMeta(type(str)):

    def __call__(cls, data, *args, **kwargs):
        """ Overrides normal str creation to allow passing args to init """
        return cls.__new__(cls, data, *args, **kwargs)

class Strang(mixins.Strang_m, str, metaclass=_StrangMeta):
    """
      A Structured String Baseclass.
      A Normal str, but is parsed on construction to extract and validate
      certain form and metadata.

    Form: group{sep}body
    body objs can be marks (Strang.mark_e), and UUID's as well as str's

    strang[x] and strang[x:y] are changed.

    """

    _separator       : ClassVar[str]  = SEP_DEFAULT
    _subseparator    : ClassVar[str]  = SUBSEP_DEFAULT
    _body_types      : ClassVar[Any]  = str|UUID|StrangMarker_e
    _typevar         : ClassVar[type] = None
    mark_e           : enum.Enum      = StrangMarker_e

    def __new__(cls, data, *args, **kwargs):
        """ Overrides normal str creation to allow passing args to init """
        data = cls.pre_process(data)
        result = str.__new__(cls, data)
        result.__init__(*args, **kwargs)
        # TODO don't call process and post_process if given the metadata in kwargs
        result._process()
        # TODO allow post-process to override and return a different object?
        result._post_process()
        return result

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.metadata                                           = dict(kwargs)
        # For easy head and body str's
        self._base_slices : tuple[slice, slice]                 = (None,None)
        self._mark_idx    : tuple[int, int]                     = (None,None)
        self._group       : list[slice]                         = []
        self._body        : list[slice]                         = []
        self._body_objs   : list[None|Strang._body_types]       = []

    def __str__(self):
        match self.metadata.get(GEN_K, False):
            case False:
                return super().__str__()
            case True:
                return self._expanded_str()

    def __repr__(self):
        body = self._subjoin(self.body(no_expansion=True))
        cls = self.__class__.__name__
        return f"<{cls}: {self[0:]}{self._separator}{body}>"

    def __iter__(self) -> iter[Strang._body_types]:
        """ iterate the body *not* the group """
        for x in range(len(self._body)):
            yield self[x]

    def __getitem__(self, i) -> Strang._body_types|Strang:
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
                return self._body_objs[i] or super().__getitem__(self._body[i])
            case slice(start=0, stop=None):
                return super().__getitem__(self._base_slices[0])
            case slice(start=1, stop=None):
                return super().__getitem__(self._base_slices[1])
            case slice(start=0, stop=x):
                return super().__getitem__(self._group[x])
            case slice(start=1, stop=x):
                return self._body_objs[x] or super().__getitem__(self._body[x])
            case slice(start=2, stop=x):
                return self.__class__(self._expanded_str(stop=x))
            case slice(start=int()):
                raise KeyError("Slicing a Strang only supports a start of 0 (group), 1 (body), and 2 (clone)", i)

    @property
    def base(self) -> Self:
        return self

    @property
    def group(self) -> list[str]:
        return [STRGET(self, x) for x in self._group]

    def body(self, *, reject:None|callable=None, no_expansion:bool=False) -> list[str]:
        """ Get the body, as a list of str's,
        with values filtered out if a rejection fn is used
        """
        body = [self._body_objs[i] or STRGET(self, x) for i, x in enumerate(self._body)]
        if reject:
            body = [x for x in body if not reject(x)]

        return [self._format_subval(x, no_expansion=no_expansion) for x in body]

    @property
    @ftz.cache
    def shape(self) -> tuple[int, int]:
        return (len(self._group), len(self._body))

    def _format_subval(self, val, no_expansion:bool=False) -> str:
        match val:
            case str():
                return val
            case UUID() if no_expansion:
                return "<uuid>"
            case UUID():
                return f"<uuid:{val}>"
            case _:
                raise TypeError("Unknown body type", val)

    def _expanded_str(self, *, stop:None|int=None):
        """ Create a str of the Strang with gen uuid's replaced with actual uuids """
        group = self[0:]
        body = []
        for val in self.body()[:stop]:
            match val:
                case str():
                    body.append(val)
                case UUID():
                    body.append(f"<uuid:{val}>")
                case _:
                    raise TypeError("Unknown body type", val)

        body_str = self._subjoin(body)
        return f"{group}{self._separator}{body_str}"

    def _post_process(self) -> None:
        """
        go through body elements, and parse UUIDs, markers, param
        setting self._body_objs and self._mark_idx
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
