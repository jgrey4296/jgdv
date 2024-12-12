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

import sys

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

if sys.version_info.minor < 12:
    raise RuntimeError("Location Path needs 3.12+")

FILE_PREFIX : Final[str] = "file:>"

class LocationMeta_e(enum.Enum):
    Dir  = enum.auto()
    File = enum.auto()
    Path = enum.auto()
    Loc  = enum.auto()

class LocationMeta(type(pl.Path)):
    """ Meta class for building the right type of location """

    _registry : dict[LocationMeta_e, pl.Path] = {LocationMeta_e.Path: pl.Path}

    def __call__(cls, *args, _form_:LocationMeta_e=LocationMeta_e.Loc, **kwargs):
        cls = LocationMeta._registry.get(_form_, cls)
        obj = cls.__new__(cls, *args, **kwargs)
        obj.__init__(*args, **kwargs)
        return obj

class VarPath(pl.Path, metaclass=LocationMeta):
    """ A Path that can handle ?wildcards, *globs, and {keys} in it.
    eg: a/path/*/?.txt
    """

    def keys(self) -> set[str]:
        pass

class Location(VarPath):

    def __init__subclass__(cls):
        super().__init__subclass__()

    def __init__(self, path:str|pl.Path, key=None, **kwargs):
        super().__init__(path)
        self._meta        = {}
        self._key         = key
        self._toml_prefix = FILE_PREFIX

        self._meta.update(kwargs)

    def __contains__(self, other) -> bool:
        """ a/b/c.py ∈ a/*/?.py  """
        return False

    def __call__(self) -> pl.Path:
        """ fully expand and resolve the path """
        pass

class FileLocation(Location):
    """ a location of a file """
    pass

class DirLocation(Location):
    """ A location of a directory """
    pass
