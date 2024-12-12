#!/usr/bin/env python3
"""
Subclasses of pathlib.Path for working with typesafe:
- Directories,
- Files, and
- Abstract paths that will be expanded
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
from jgdv.mixins.annotate import SubRegistry_m

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

if sys.version_info.minor < 12:
    raise RuntimeError("Path Path needs 3.12+")

class PathyTypes_e(enum.StrEnum):
    """ An Enum of available Path+ types"""
    Dir      = "dir"
    File     = "file"
    Path     = "path"
    Loc      = "loc"
    Wildcard = "*"

    default  = Loc

class PathyMeta(type(pl.Path)):
    """ Meta class for building the right type of location """

    _registry : dict[PathyTypes_e, pl.Path] = {PathyTypes_e.Path: pl.Path}

    def __call__(cls, *args, **kwargs):
        logging.debug("PathyMeta Call: %s : %s : %s", cls, args, kwargs)
        cls = cls._get_subclass_form()
        obj = cls.__new__(cls, *args, **kwargs)
        obj.__init__(*args, **kwargs)
        return obj

class Pathy(SubRegistry_m, pl.Path, AnnotateTo="pathy_type", metaclass=PathyMeta):

    mark_e : ClassVar[enum.Enum] = PathyTypes_e

    @classmethod
    def __class_getitem__(cls, param) -> Self:
        param = cls.mark_e(param)
        return super().__class_getitem__(param)

    def __init__(self, path:str|pl.Path, *paths, key=None, **kwargs):
        super().__init__(path, *paths)
        self._meta        = {}
        self._key         = key

        self._meta.update(kwargs)

    def __contains__(self, other) -> bool:
        """ a/b/c.py ∈ a/*/?.py  """
        match other:
            case str():
                return other in str(self)
            case pl.Path() if not other.is_absolute():
                return str(other) in str(self)
            case Pathy():
                pass
            case _:
                raise NotImplementedError()

    def __call__(self, **kwargs) -> pl.Path:
        """ fully expand and resolve the path """
        return self.normalize(**kwargs)

    def __eq__(self, other) -> bool:
        match other:
            case pl.Path() | Pathy():
                return self == other
            case str():
                return str(self) == other
            case _:
                raise NotImplementedError()

    def __rtruediv__(self, other):
        match other:
            case str():
                return Pathy(other, self)
            case Pathy():
                return other / self

    def with_segments(self, *segments) -> Self:
        if self._get_annotation() is self.mark_e.File:
            raise ValueError("Can't subpath a file")
        match segments:
            case [*_, PathyFile()]:
                return Pathy['file'](*segments)
            case [*_, pl.Path()|str() as x] if pl.Path(x).suffix != "":
                return Pathy['file'](*segments)
            case _:
                return Pathy['dir'](*segments)

    def normalize(self, *, root=None, symlinks:bool=False) -> pl.Path:
        """
          a basic path normalization
          expands user, and resolves the location to be absolute
        """
        result = pl.Path(self)
        if symlinks and path.is_symlink():
            raise NotImplementedError("symlink normalization", path)

        match result.parts:
            case ["~", *xs]:
                result = result.expanduser().resolve()
            case ["/", *xs]:
                result = result
            case _ if root:
                result = (root / path).expanduser().resolve()
            case _:
                result = result.expanduser().resolve()

        return result

    def format(self, *args, **kwargs) -> Self:
        as_str = str(self)
        formatted = as_str.format(*args, **kwargs)
        return type(self)(formatted)

class PathyFile(Pathy['file']):
    """ a location of a file """
    pass

class PathyDir(Pathy['dir']):
    """ A location of a directory """
    pass

class WildPathy(Pathy['*']):
    """ A Path that can handle ?wildcards, *globs, and {keys} in it.
    eg: a/path/*/?.txt
    """

    def keys(self) -> set[str]:
        raise NotImplementedError()
