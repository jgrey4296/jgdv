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
import re
import time
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

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
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from ._interface import Logger
    from jgdv import Maybe, Traceback
## isort: on
# ##-- end type checking


##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class LogContext:
    """
      a really simple wrapper to set a logger's level, then roll it back

    use as:
    with LogContext(logger, level=logmod.INFO) as ctx:
    ctx.log("blah")
    # or
    logger.info("blah")
    """

    def __init__(self, logger:Logger, level:Maybe[int]=None) -> None:
        self._logger          = logger
        self._original_level  = self._logger.level
        self._level_stack     = [self._original_level]
        self._temp_level      = level or self._original_level

    def __call__(self, level:int) -> Self:
        self._temp_level = level
        return self

    def __enter__(self) -> Self:
        match self._temp_level:
            case int() | str():
                self._level_stack.append(self._logger.level)
                self._logger.setLevel(self._temp_level)
        return self

    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool:
        if bool(self._level_stack):
            self._logger.setLevel(self._level_stack.pop())
        else:
            self._logger.setLevel(self._original_level)
        return False

    def __getattr__(self, key:str) -> Logger:
        return cast("Logger", getattr(self._logger, key))

    def log(self, msg:str, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        self._logger.log(self._temp_level, msg, *args, **kwargs)

class TempLogger:
    """ For using a specific type of logger in a context, or getting
    a custom logger class without changing it globally

    use as:
    with TempLogger(MyLoggerClass) as ctx:
    # Either:
    ctx['name'].info(...)
    # or:
    logmod.getLogger('name').info(...)
    """
    _target_cls  : type[Logger]
    _original    : Maybe[type[Logger]]

    def __init__(self, logger:type[Logger]) -> None:
        self._target_cls  = logger
        self._original    = None

    def __enter__(self) -> Self:
        self._original = logmod.getLoggerClass()
        logmod.setLoggerClass(self._target_cls)
        return self

    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool:
        if self._original is not None:
            logmod.setLoggerClass(self._original)

        return False
