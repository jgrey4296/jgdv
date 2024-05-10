#!/usr/bin/env python3
"""
Types that help add clarity

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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match, NewType,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload, Optional,
                    runtime_checkable)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
# import more_itertools as mitz
# from boltons import
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# TODO when in py3.12 use 'type' kw

T                       = TypeVar("T")

Stack                   = NewType("Stack", list[T])
Queue                   = NewType("Queue", list[T])
Vector                  = NewType("Vector", list[float])

Identifier              = NewType("Identifier", str)

Depth                   = NewType("Depth", int)
Seconds                 = NewType("Seconds", int)

Maybe         TypeAlias = Optional
