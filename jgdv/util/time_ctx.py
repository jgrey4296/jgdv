#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

from __future__ import annotations

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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class TimeCtx:
    """
    A Simple Timer Ctx class to log how long things take
    Give it a logger, a message, and a level.
    The message doesn't do any interpolation
    """

    def __init__(self, logger=None, entry_msg=None, exit_msg=None, level=10):
        assert(isinstance(level, int))
        self._start_time = None
        self._logger     = logger or logging
        self._level      = level
        self._entry_msg  = entry_msg or "Starting Timer"
        self._exit_msg   = exit_msg  or "Time Elapsed"


    def __enter__(self) -> Any:
        self._logger.log(self._level, self._entry_msg)
        self._start_time = time.perf_counter()
        return


    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        end = time.perf_counter()
        elapsed = end - self._start_time
        self._logger.log(self._level, "%s : %s", self._exit_msg, f"{elapsed:0.4f} Seconds")
        # return False to reraise errors
        return False
