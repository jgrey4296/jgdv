#!/usr/bin/env python3
"""

"""
# ruff: noqa:

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import enum
import functools as ftz
import itertools as itz
import logging as logmod
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

from jgdv.structs.strang._interface import Strang_i, Strang_p

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
    import datetime
    from jgdv.structs.dkey._interface import Key_i
    import pathlib as pl
    from jgdv import Maybe, Ident
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    TimeDelta = datetime.timedelta
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
CWD_MARKER : Final[Ident] = "__cwd"
LOC_SEP    : Final[str]   = "::>"
LOC_SUBSEP : Final[str]   = "/"

# Body:

class WildCard_e(enum.StrEnum):
    """ Ways a path can have a wildcard. """
    glob       = "*"
    rec_glob   = "**"
    select     = "?"
    key        = "{"

class LocationMeta_e(enum.StrEnum):
    """ Available metadata attachable to a location """

    location     = "location"
    directory    = "directory"
    file         = "file"

    abstract     = "abstract"
    artifact     = "artifact"
    clean        = "clean"
    earlycwd     = "earlycwd"
    protect      = "protect"
    expand       = "expand"
    remote       = "remote"
    partial      = "partial"

    # Aliases
    dir          = directory
    loc          = location

    default      = loc

##--|

##--|

@runtime_checkable
class Location_p(Strang_p, Protocol):
    """ Something which describes a file system location,
    with a possible identifier, and metadata
    """

    @override
    def __getitem__(self, i:int|slice) -> str|WildCard_e: ...

    def __lt__(self, other:TimeDelta|str|pl.Path|Location_p) -> bool: ...

    @property
    def keys(self) -> set[str]: ...

    @property
    def path(self) -> pl.Path: ...

    @property
    def body_parent(self) -> list[str|WildCard_e]: ...

    @property
    def stem(self) -> Maybe[str|tuple[WildCard_e, str]]: ...

    def ext(self, *, last:bool=False) -> Maybe[str|tuple[WildCard_e, str]]: ...

    def check_wildcards(self, other:Self) -> bool: ...

    def is_concrete(self) -> bool: ...

class Location_i(Location_p, Protocol):
    key   : Maybe[str|Key_i]
    path  : pl.Path
    meta  : enum.EnumMeta

@runtime_checkable
class Locator_p(Protocol):
    pass
