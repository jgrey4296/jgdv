#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

import copy
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import re
import time
import weakref
from uuid import UUID, uuid1

##-- end builtin imports

from time import sleep
import timeit
from random import random
import jgdv
from jgdv.decorators import MonotonicDec

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
# isort: on
# ##-- end types

# ##-- type checking
# isort: off
if typing.TYPE_CHECKING:
    import pathlib as pl
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Traceback, Func, Method
    from logging import Logger
## isort: on
# ##-- end type checking

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

autorange_fmt      : Final[str] = "%-*10s : %-*5d calls took: %-*8.2f seconds"
result_fmt         : Final[str] = "Attempt %-*5d : %-*8.2f seconds"
block_fmt          : Final[str] = "%-*10s : %-*8.2f seconds"
once_fmt           : Final[str] = "%-*10s : %-*8.2f seconds"

##--|
class TimeCtx:
    """ Utility Class to time code execution. """
    _logger      : Maybe[Logger]
    level        : int
    group        : str
    total        : int
    total_ms     : float
    total_s      : float
    _start       : int
    _stop        : int

    def __init__(self, *, logger:Maybe[Logger|Literal[False]]=None, level:int=logmod.INFO, group:Maybe[str]=None) -> None:
        self.level        = level
        self.group        = f"{group}::" if group else ""
        self._start       = 0
        self._stop        = 0
        self.total        = 0
        match logger:
            case None:
                self._logger = logging
            case False:
                self._logger = None
            case logmod.Logger() as l:
                self._logger = l

    def __enter__(self) -> Self:
        self._start = time.monotonic_ns()
        return self

    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool:
        self._stop     = time.monotonic_ns()
        self.total     = (self._stop - self._start)
        self.total_ms  = self.total * 0.0001
        self.total_s   = self.total / 1_000_000_000
        return False

    def _set_name(self, name:Maybe[str]) -> None:
        match name:
            case None:
                pass
            case str() as s:
                self.current_name = self.group + s

    def msg(self, msg:str, *args:Any) -> None:  # noqa: ANN401
        if self._logger is None:
            return

        self._logger.log(self.level, msg, *args)


class TimeDec(MonotonicDec):
    """ Decorate a callable to track its timing """
    _logger  : Maybe[Logger]
    _cache   : Maybe[pl.Path]

    def __init__(self, *, cache:Maybe[pl.Path]=None, logger:Maybe[Logger|Literal[False]]=None, level:Maybe[int]=None, **kwargs:Any) -> None:  # noqa: ANN401
        kwargs.setdefault("mark", "_timetrack_mark")
        kwargs.setdefault("data", "_timetrack_data")
        super().__init__([], **kwargs)
        self._level  = level
        self._cache  = cache
        match logger:
            case logmod.Logger() as l:
                self._logger = l
            case None:
                self._logger = logging
            case False:
                self._logger = None


    @override
    def _wrap_fn_h[**I, O](self, fn:Func[I, O]) -> Func[I, O]:
        logger, level = self._logger, self._level

        def track_time_wrapper(*args:I.args, **kwargs:I.kwargs) -> O:
            with TimeCtx(logger=logger, level=level or logmod.INFO) as timer:
                result = fn(*args, **kwargs)

            timer.msg("Timed: %s took %s seconds", fn.__qualname__, timer.total_s)
            if self._cache:
                now = datetime.datetime.now().strftime("%Y-%m-%d:%H-%M")
                line = f"{now} : {fn.__qualname__} : {timer.total_s}\n"
                with open(self._cache, "a") as f:
                    f.write(line)

            return result

        return track_time_wrapper

    @override
    def _wrap_method_h[**I, O](self, fn:Func[I, O]) -> Func[I, O]:
        return self._wrap_fn_h(fn)
