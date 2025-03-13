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
import weakref
from typing import Any
from uuid import UUID, uuid1

# ##-- end stdlib imports

import jgdv
from jgdv import Proto

##-- types
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
    from jgdv import Maybe, Traceback
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type Logger = logmod.Logger
##--|

# isort: on
##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(jgdv.protos.DILogger_p)
class TimeBlock_ctx:
    """
    A Simple Timer Ctx class to log how long things take
    Give it a logger, a message, and a level.
    The message doesn't do any interpolation

    eg: With TimeBlock():...

    """
    start_time   : Maybe[float]
    end_time     : Maybe[float]
    elapsed_time : Maybe[float]

    def __init__(self, *, logger:Maybe[Logger|False]=None, enter_msg:Maybe[str]=None, exit_msg:Maybe[str]=None, level:Maybe[int|str]=None) -> None:
        self.start_time      = None
        self.end_time        = None
        self.elapsed_time    = None
        self._level          = level or 10
        self._enter_msg      = enter_msg or "Starting Timer"
        self._exit_msg       = exit_msg  or "Time Elapsed"

        match logger:
            case False:
                self._logger = logmod.getLogger("null")
                self._logger.propagate = False
                pass
            case logmod.Logger() as l:
                self._logger = l
            case _:
                self._logger = logging


    def __enter__(self) -> Self:
        self._logger.log(self._level, self._enter_msg)
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type:Maybe[type], exc_value:Maybe, exc_traceback:Maybe[Traceback]) -> bool:
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time
        self._logger.log(self._level, "%s : %s", self._exit_msg, f"{self.elapsed_time:0.4f} Seconds")
        # return False to reraise errors
        return False
