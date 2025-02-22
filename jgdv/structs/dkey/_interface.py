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
import time
import types
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from jgdv.mixins.enum_builders import EnumBuilder_m

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any
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

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
ARGS_K              : Final[Ident]     = "args"
DEFAULT_COUNT       : Final[int]       = 0
FMT_PATTERN         : Final[Rx]        = re.compile("[wdi]+")
INDIRECT_SUFFIX     : Final[Ident]     = "_"
KEY_PATTERN         : Final[RxStr]     = "{(.+?)}"
KWARGS_K            : Final[Ident]     = "kwargs"
MAX_DEPTH           : Final[int]       = 10
MAX_KEY_EXPANSIONS  : Final[int]       = 200
PAUSE_COUNT         : Final[int]       = 0
RECURSION_GUARD     : Final[int]       = 5
PARAM_IGNORES       : Final[list[str]] = ["_", "_ex"]
# Body:

class DKeyMark_e(EnumBuilder_m, enum.StrEnum):
    """
      Enums for how to use/build a dkey

    """
    FREE     = "free"
    PATH     = enum.auto() # -> pl.Path
    INDIRECT = "indirect"
    STR      = enum.auto() # -> str
    CODE     = enum.auto() # -> coderef
    IDENT    = enum.auto() # -> taskname
    ARGS     = enum.auto() # -> list
    KWARGS   = enum.auto() # -> dict
    POSTBOX  = enum.auto() # -> list
    NULL     = enum.auto() # -> None
    MULTI    = enum.auto()

    default  = FREE
##--|
@runtime_checkable
class Key_p(Protocol):
    """ The protocol for a Key, something that used in a template system"""

    @property
    def multi(self) -> bool: ...

    def keys(self) -> list[Key_p]: ...

    def redirect(self, spec=None) -> Key_p: ...

    def expand(self, spec=None, state=None, *, rec=False, insist=False, chain:list[Key_p]=None, on_fail=Any, locs:Mapping=None, **kwargs) -> str: ...
