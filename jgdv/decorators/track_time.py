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

# ##-- 1st party imports
from jgdv.util.time_ctx import TimeCtx
from jgdv.decorators.base import MetaDecorator

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class TrackTime(MetaDecorator):
    """ Decorate a callable to track its timing """

    def __init__(self, logger:None|logmod.Logger=None, level:None|int|str=None, entry:str=None, exit:str=None, **kwargs):
        kwargs.setdefault("mark", "_timetrack_mark")
        kwargs.setdefault("data", "_timetrack_data")
        super().__init__([], **kargs)
        self._logger = logger
        self._level  =  level
        self._entry  = entry
        self._exit   = exit
    
    def wrap_fn(self, fn):

        def track_time_wrapper(*args, **kwargs):
            with TimeCtx(logger, enter, exit, level):
                return fn(*args, **kwargs)

        return track_time_wrapper

    def wrap_method(self, fn):
        return self._wrap_fn(fn)
