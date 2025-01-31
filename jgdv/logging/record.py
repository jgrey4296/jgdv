#!/usr/bin/env python3
"""



"""
# Import:
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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
# ##-- end stdlib imports

# ##-- typecheck imports
# isort: off
if typing.TYPE_CHECKING:
   from jgdv import Maybe

# isort: on
# ##-- end typecheck imports

##-- type aliases


##-- end type aliases

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class JGDVLogRecord(logmod.getLogRecordFactory()):
    """ A Basic extension of the log record

    needs the signature:
    factory(name, level, fn, lno, msg, args, exc_info, func=None, sinfo=None, **kwargs)
"""
    pass
