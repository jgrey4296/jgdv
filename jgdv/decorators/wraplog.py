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
from jgdv.util.time_ctx import TimeCtx

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


def wraplog(logger, level, enter, exit):
    """ TODO decorator to log entry and exit of a function,
      and its time taken
      """

    def applicator(fn):
        @ftz.wraps(fn)
        def wrapper(*args, **kwargs):
            with TimeCtx(logger, enter, exit, level):
                return fn(*args, **kwargs)

        return wrapper

    return applicator
