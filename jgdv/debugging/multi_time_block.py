#!/usr/bin/env python3
"""

"""
# ruff: noqa:

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
import types
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
import timeit
# ##-- end stdlib imports

import jgdv

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
    from jgdv import Maybe, Traceback
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type Logger    = logmod.Logger
    type Statement = str | Callable
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

# @Proto(CtxManager_p)
class MultiTimeBlock_ctx:
    """ CtxManager for timing statements multiple times

    see https://docs.python.org/3/library/timeit.html
    """
    count              : int
    repeat             : int
    keep_gc            : bool
    group              : str
    autorange_total    : float
    once_log           : list[tuple[str, float]]
    log_level          : int
    _logger            : Maybe[Logger]
    _current_name      : Maybe[str]

    def __init__(self, *, count:int=10, repeat:int=5, keep_gc:bool=False, group:Maybe[str]=None, logger:Maybe[Logger]=None, level:Maybe[int|str]=None) -> None:  # noqa: PLR0913
        self.count            = count
        self.repeat           = repeat
        self.keep_gc          = keep_gc
        self.group : str      = group if group else ""
        self.autorange_total  = 0.0
        self.once_log         = []
        self._logger          = logger
        match level:
            case None:
                self.log_level = logmod._nameToLevel["info"]
            case int() as x:
                self.log_level = x
            case str():
                self.log_level            = logmod._nameToLevel[level or "info"]

    def _set_name(self, *, name:str, stmt:Callable) -> None:
        """ Default Name builder """
        match name, stmt:
            case str(), str():
                self._current_name = f"{self.group}::{name}"
            case str(), x if hasattr(x, "__qualname__"):
                self._current_name = "::".join(self.group, name, stmt.__qualname__) #type:ignore
            case str(), _:
                self._current_name = f"{self.group}::{name}"

    def autorange_cb(self, number:int, took:float) -> None:
        """ Callback for autorange.
        Called after each trial.
        """
        self._log("%-*10s : %-*5d calls took:", self._current_name, number, time=took)
        self.autorange_total += took

    def auto(self, stmt:Callable, *, name:Maybe[str]=None) -> float:
        """ Try the statement with larger trial sizes until it takes at least 0.2 seconds """
        self._set_name(name=name, stmt=stmt)
        self._log("Autoranging: %s", self._current_name)
        timer = timeit.Timer(stmt, globals=globals())
        timer.autorange(self.autorange_cb)
        return self.autorange_total

    def repeats(self, stmt:Callable, *, name:Maybe[str]=None) -> list[float]:
        """
        Repeat the stmt and report the results
        """
        self._set_name(name=name, stmt=stmt)
        self._log("Repeating %s : Timing %s repeats of %s trials",
                  self._current_name, self.repeat, self.count)
        timer  = timeit.Timer(stmt, globals=globals())
        results = timer.repeat(repeat=self.repeat, number=self.count)
        for i, result in enumerate(results):
            self._log("Attempt %-*5d : %-*8.2f seconds", i, time=result, prefix="----")
        else:
            return results

    def block(self, stmt:Callable, *, name:Maybe[str]=None) -> float:
        """ Run the stmt {count} numnber of times and report the time it took"""
        self._set_name(name=name, stmt=stmt)
        self._log("Running Block %s : Timing block of %-*5f trials",
                  self._current_name, self.count)
        timer  = timeit.Timer(stmt, globals=globals())
        result = timer.timeit(self.count)
        self._log("%-*10s : %-*8.2f seconds", self._current_name, time=result, prefix="----")
        return result

    def once(self, stmt:Callable, *, name:Maybe[str]=None) -> float :
        """ Run the statement once, and return the time it took """
        self._set_name(name=name, stmt=stmt)
        self._log("Running Call Once: %s", self._current_name)
        timer  = timeit.Timer(stmt, globals=globals())
        result = timer.timeit(1)
        self.once_log.append((self._current_name, result))
        self._log("%-*10s", self._current_name, time=result, prefix="----")
        return result

    def _log(self, msg:str, *args:Any, time:Maybe[float]=None, prefix:Maybe[str]=None) -> None:  # noqa: ANN401
        """ The internal log method """
        match self._logger:
            case None:
                pass
            case logmod.Logger() if time is None:
                prefix = prefix or "--"
                msg_format = f"%s {msg}"
                self._logger.log(self.log_level, msg_format, prefix, *args)
            case logmod.Logger():
                prefix = prefix or "--"
                msg_format = f"%s {msg} : %-*8.2f seconds"
                self._logger.log(self.log_level, msg_format, prefix, *args, time)

    def __enter__(self) -> Self:
        """ Return a copy of this obj for a with block """
        match self.group:
            case str() as x:
                self._log("Entering: %s", x)
            case None:
                pass
        return deepcopy(self)

    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool:
        """ On exiting the block, reports the time the block took """
        match self.autorange_total:
            case float()as x if 0 < x:
                self._log("Finished Block %s", self.group, time=x)
            case _:
                self._log("Finished Block %s", self.group)

        match self.once_log:
            case []:
                pass
            case [*xs]:
                long_name, time_taken = max(xs, key=lambda x: x[1])
                self._log("-- Longest Single Call: %s : %-*8.2fs seconds", long_name, time_taken )

        return False
