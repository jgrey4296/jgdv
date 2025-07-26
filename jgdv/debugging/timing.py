#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from time import sleep
import timeit
import time
from random import random

autorange_fmt : Final[str] = "%-*10s : %-*5d calls took: %-*8.2f seconds"
result_fmt    : Final[str] = "Attempt %-*5d : %-*8.2f seconds"
block_fmt     : Final[str] = "%-*10s : %-*8.2f seconds"
once_fmt      : Final[str] = "%-*10s : %-*8.2f seconds"

class JGDVTimer:
    """ Utility Class to time code execution.

      see https://docs.python.org/3/library/timeit.html
    """

    def __init__(self, count=10, repeat=5, keep_gc=False, group:None|str=None):
        self.level            = level
        self.count            = count
        self.repeat           = repeat
        self.keep_gc          = keep_gc
        self.group : str      = f"{group}::" if group else ""
        self.total            = 1.0
        self.once_log         = []

    def msg(self, str, *args):
        logging.debug(str, *args)

    def _set_name(self, name, stmt):
        match name, stmt:
            case str(), _:
                self.current_name = self.group + name
            case _:
                self.current_name = self.group + stmt.__qualname__

    def autorange_cb(self, number, took):
        self.msg(autorange_fmt, self.current_name, number, took)
        self.total += took

    def auto(self, stmt, name=None):
        self._set_name(name, stmt)
        self.msg("-- Autoranging: %s", self.current_name")
        timer = timeit.Timer(stmt, globals=globals())
        timer.autorange(self.autorange_cb)

    def repeats(self, stmt, name=None):
        self._set_name(name, stmt)
        self.msg("-- Repeating %s : Timing %s repeats of %s trials", self.current_name, self.repeat, self.count)
        timer  = timeit.Timer(stmt, globals=globals())
        results = timer.repeat(repeat=self.repeat, number=self.count)
        for i, result in enumerate(results):
            self.msg(result_fmt, i, result)

    def block(self, stmt, name=None):
        self._set_name(name, stmt)
        self.msg("-- Running Block %s : Timing block of %-*5f trials", self.current_name, self.count)
        timer  = timeit.Timer(stmt, globals=globals())
        result = timer.timeit(self.count)
        self.msg(block_fmt, self.current_name, result)

    def once(self, stmt, name=None):
        self._set_name(name, stmt)
        self.msg("-- Running Call Once: %s", self.current_name)
        timer  = timeit.Timer(stmt, globals=globals())
        result = timer.timeit(1)
        self.once_log.append((self.current_name, result))
        self.msg(once_fmt, self.current_name, result)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.msg("-- Finished %s : %-*8.2f", self.group, self.total)
        if self.once_log:
            self.msg("-- Largest Single Call: %s", max(self.once_log, key=lambda x: x[1]))

        return


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


class TimeBlock_ctx(jgdv.protos.DILogger_p):
    """
    A Simple Timer Ctx class to log how long things take
    Give it a logger, a message, and a level.
    The message doesn't do any interpolation

    eg: With TimeBlock():...

    """
    start_time   : Maybe[float]
    end_time     : Maybe[float]
    elapsed_time : Maybe[float]

    def __init__(self, *, logger:Maybe[Logger|Literal[False]]=None, enter:Maybe[str]=None, exit:Maybe[str]=None, level:Maybe[int|str]=None) -> None: # noqa: A002
        self.start_time      = None
        self.end_time        = None
        self.elapsed_time    = None
        self._enter_msg      = enter or "Starting Timer"
        self._exit_msg       = exit or "Time Elapsed"

        match level:
            case int() as x:
                self._level = x
            case str() as x if x in logmod._nameToLevel:
                self._level = logmod._nameToLevel[x]
            case _:
                self._level = logmod.INFO

        match logger:
            case False:
                self._logger = logmod.getLogger("null")
                self._logger.propagate = False
                pass
            case logmod.Logger() as l:
                self._logger = l
            case _:
                self._logger = logging

    @override
    def logger(self) -> logmod.Logger:
        return self._logger

    def __enter__(self) -> Self:
        self._logger.log(self._level, self._enter_msg)
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type:Maybe[type], exc_value:Maybe, exc_traceback:Maybe[Traceback]) -> bool: # type: ignore[exit-return]
        assert(self.start_time)
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time
        self._logger.log(self._level, "%s : %s", self._exit_msg, f"{self.elapsed_time:0.4f} Seconds")
        # return False to reraise errors
        return False


class TrackTime(MetaDec):
    """ Decorate a callable to track its timing """

    def __init__(self, logger:Maybe[Logger]=None, level:Maybe[int|str]=None, enter:Maybe[str]=None, exit:Maybe[str]=None, **kwargs:Any) -> None:  # noqa: ANN401, A002
        kwargs.setdefault("mark", "_timetrack_mark")
        kwargs.setdefault("data", "_timetrack_data")
        super().__init__([], **kwargs)
        self._logger  = logger
        self._level   = level
        self._entry   = enter
        self._exit    = exit

    def wrap_fn[**I, O](self, fn:Func[I, O]) -> Func[I, O]:
        logger, enter, exit, level = self._logger, self._entry, self._exit, self._level  # noqa: A001

        def track_time_wrapper(*args:I.args, **kwargs:I.kwargs) -> O:
            with TimeBlock_ctx(logger=logger, enter=enter, exit=exit, level=level):
                return fn(*args, **kwargs)
            raise RuntimeError()

        return track_time_wrapper

    def wrap_method[**I, O](self, fn:Method[I, O]) -> Method[I, O]:
        return cast("Method", self.wrap_fn(fn))
