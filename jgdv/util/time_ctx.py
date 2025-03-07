#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
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
from uuid import UUID, uuid1

# ##-- end stdlib imports

from jgdv._types import Maybe
from typing import Any
type Logger = logmod.Logger

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class TimeCtx:
    """
    A Simple Timer Ctx class to log how long things take
    Give it a logger, a message, and a level.
    The message doesn't do any interpolation

    """

    def __init__(self, logger:Logger=None, entry_msg:Maybe[str]=None, exit_msg:Maybe[str]=None, level:Maybe[int|str]=None):
        self._start_time = None
        self._logger     = logger or logging
        self._level      = level or 10
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
