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
import typing
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
# ##-- end stdlib imports

from .core import DecoratorBase

# ##-- type aliases
# isort: off
if typing.TYPE_CHECKING:
   from jgdv import Maybe

# isort: on
# ##-- end type aliases

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class SideEffectFree(DecoratorBase):
    """ Mark a Target as not modifying external variables """
    pass
