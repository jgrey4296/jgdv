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
from tomlguard import TomlGuard

# ##-- end 3rd party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv.structs.name import strang_mixins as mixins

FMT_PATTERN    : Final[re.Pattern]         = re.compile("^(h?)(t?)(p?)")
SEP_DEFAULT    : Final[str]                = "::"
SUBSEP_DEFAULT : Final[str]                = "."
GEN_K          : Final[str]                = mixins.GEN_K

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

    _separator       : ClassVar[str] = SEP_DEFAULT
    _subseparator    : ClassVar[str] = SUBSEP_DEFAULT
    _body_types      : ClassVar[Any] = str|UUID|StrangMarker_e
    mark_e          : enum.Enum     = StrangMarker_e

    def __new__(cls, data, *args, **kwargs):
        """ Overrides normal str creation to allow passing args to init """
        data = cls.pre_process(data)
        result = str.__new__(cls, data)
        result.__init__(*args, **kwargs)
        # TODO don't call process and post_process if given the metadata in kwargs
        result._process()
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
        return f"<Strang: {self[0:]}{self._separator}{body}>"

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
                return Strang(self._expanded_str(stop=x))
            case slice(start=int()):
                raise KeyError("Slicing a Strang only supports a start of 0 (group), 1 (body), and 2 (clone)", i)

    @property
    def base(self):
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
