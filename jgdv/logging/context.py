#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
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
from jgdv import Maybe

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class JGDVLogContext:
    """
      a really simple wrapper to set a logger's level, then roll it back
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
