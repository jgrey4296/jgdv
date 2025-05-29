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

from jgdv.structs.strang import _interface as StrangAPI # noqa: N812
from jgdv.structs.strang._interface import Strang_p

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
    import pathlib as pl
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Ident, Traceback
    from jgdv.structs.dkey._interface import Key_p

    type TimeDelta = datetime.timedelta
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

class WildCard_e(StrangAPI.StrangMarkAbstract_e):
    """ Ways a path can have a wildcard. """
    glob       = "*"
    rec_glob   = "**"
    select     = "?"
    key        = "{"

class LocationMeta_e(StrangAPI.StrangMarkAbstract_e):
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

    @classmethod
    def default(cls) -> Maybe:
        return cls.location

##--|

LocationSections : Final[StrangAPI.Sections_d] = StrangAPI.Sections_d(
    StrangAPI.Sec_d("head", ".", LOC_SEP, str|LocationMeta_e, LocationMeta_e, False),  # noqa: FBT003
    StrangAPI.Sec_d("body", LOC_SUBSEP, None, str|WildCard_e, WildCard_e, True),  # noqa: FBT003
)
##--|

@runtime_checkable
class Location_p(Strang_p, Protocol):
    """ Something which describes a file system location,
    with a possible identifier, and metadata
    """

    def __lt__(self, other:TimeDelta|str|pl.Path|Location_p) -> bool: ...

    @property
    def keys(self) -> set[str]: ...

    @property
    def path(self) -> pl.Path: ...

    @property
    def body_parent(self) -> list[str|WildCard_e]: ...

    @property
    def stem(self) -> Maybe[str|tuple[WildCard_e, str]]: ...

    @property
    def key(self) -> Maybe[str|Key_p]: ...

    def ext(self, *, last:bool=False) -> Maybe[str|tuple[WildCard_e, str]]: ...

    def check_wildcards(self, other:pl.Path|Location_p) -> bool: ...

    def is_concrete(self) -> bool: ...

@runtime_checkable
class Locator_p(Protocol):

    def __getattr__(self, key:str) -> Location_p: ...

    def __getitem__(self, val:str|pl.Path|Location_p|Key_p) -> pl.Path: ...

    def __contains__(self, key:str|pl.Path|Location_p|Key_p) -> bool: ...

    def __bool__(self) -> bool: ...

    def __len__(self) -> int: ...

    def __iter__(self) -> Generator[str|Key_p]: ...

    def __call__(self, new_root:Maybe[pl.Path]=None) -> Locator_p: ...

    def __enter__(self) -> Locator_p: ...

    def __exit__(self, etype:Maybe[type[Exception]], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool: ...

    def clear(self) -> None: ...

    def update(self, extra:dict|Location_p|Locator_p, *, strict:bool=True) -> Self: ...
