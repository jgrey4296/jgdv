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
from typing import Any
from uuid import UUID, uuid1

# ##-- end stdlib imports


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
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type Logger = logmod.Logger
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class TimeCtx:
    """
    A Simple Timer Ctx class to log how long things take
    Give it a logger, a message, and a level.
    The message doesn't do any interpolation

    """

    def __init__(self, logger:Logger=None, entry_msg:Maybe[str]=None, exit_msg:Maybe[str]=None, level:Maybe[int|str]=None) -> None:
        self._start_time = None
        self._logger     = logger or logging
        self._level      = level or 10
        self._entry_msg  = entry_msg or "Starting Timer"
        self._exit_msg   = exit_msg  or "Time Elapsed"

    def __enter__(self) -> Any:  # noqa: ANN401
        self._logger.log(self._level, self._entry_msg)
        self._start_time = time.perf_counter()
        return

    def __exit__(self, exc_type:Any, exc_value:Any, exc_traceback:Any) -> bool:  # noqa: ANN401
        end = time.perf_counter()
        elapsed = end - self._start_time
        self._logger.log(self._level, "%s : %s", self._exit_msg, f"{elapsed:0.4f} Seconds")
        # return False to reraise errors
        return False
