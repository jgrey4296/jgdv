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
import types
import weakref
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

    from ._interface import Logger
##--|

# isort: on
# ##-- end types

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

    def __init__(self, logger, level=None):
        self._logger          = logger
        self._original_level  = self._logger.level
        self._level_stack     = [self._original_level]
        self._temp_level      = level or self._original_level

    def __call__(self, level) -> Self:
        self._temp_level = level
        return self

    def __enter__(self) -> Self:
        match self._temp_level:
            case int() | str():
                self._level_stack.append(self._logger.level)
                self._logger.setLevel(self._temp_level)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        if bool(self._level_stack):
            self._logger.setLevel(self._level_stack.pop())
        else:
            self._logger.setLevel(self._original_level)

    def __getattr__(self, key):
        return getattr(self._logger, key)

    def log(self, msg, *args, **kwargs):
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

    def __init__(self, logger:type[Logger]):
        self._target_cls                        = logger
        self._original : Maybe[logmod.Logger]   = None

    def __enter__(self) -> Self:
        self._original = logmod.getLoggerClass()
        logmod.setLoggerClass(self._target_cls)
        return self

    def __exit(self, *exc):
        self.setLoggerClass(self._original)
        return False
