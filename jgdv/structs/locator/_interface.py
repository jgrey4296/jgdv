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

from jgdv.structs.dkey import Key_p

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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

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
class Location_d:
    key                 : Maybe[str|Key_p]
    path                : pl.Path
    meta                : enum.EnumMeta

##--|
@runtime_checkable
class Location_p(Protocol):
    """ Something which describes a file system location,
    with a possible identifier, and metadata
    """
    def keys(self) -> set[str]:
        pass

@runtime_checkable
class Locator_p(Protocol):
    pass
