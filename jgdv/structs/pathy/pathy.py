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
import sys
import time as time_
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
    Self,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Maybe, DateTime, TimeDelta
from jgdv.mixins.annotate import SubRegistry_m

# ##-- end 1st party imports

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

    def __init__(self, *paths:str|pl.Path, key=None, **kwargs):
        super().__init__(*paths)
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

    def __lt__(self, other:Pathy|DateTime) -> bool:
        """ do self<other for paths,
        and compare against modification time if given a datetime
        """
        match other:
            case datetime.datetime():
                return self._newer_than(other)
            case Pathy() | pl.Path():
                return super().__lt__(other)

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
        if symlinks and result.is_symlink():
            raise NotImplementedError("symlink normalization", result)

        match result.parts:
            case ["~", *_]:
                result = result.expanduser().resolve()
            case ["/", *_]:
                result = result
            case _ if root:
                result = (root / result).expanduser().resolve()
            case _:
                result = result.expanduser().resolve()

        return result

    def format(self, *args, **kwargs) -> Self:
        as_str = str(self)
        formatted = as_str.format(*args, **kwargs)
        return type(self)(formatted)

    def with_suffix(self, suffix):
        return Pathy['file'](super().with_suffix(suffix))

    def time_created(self) -> DateTime:
        stat = self.stat()
        try:
            return datetime.datetime.fromtimestamp(stat.st_birthtime)
        except AttributeError:
            return datetime.datetime.fromtimestamp(stat.st_ctime)

    def time_modified(self) -> DateTime:
        return datetime.datetime.fromtimestamp(self.stat().st_mtime)

    def _newer_than(self, time:DateTime, *, tolerance:TimeDelta=None) -> bool:
        if not self.exists():
            return False

        match tolerance:
            case datetime.timedelta():
                mod_time = self.time_modified()
                diff = mod_time - time
                return tolerance < diff
            case None:
                return time < self.time_modified()

class PathyFile(Pathy['file']):
    """ a location of a file """

    def glob(self, *args, **kwargs):
        raise NotImplementedError()

    def walk(self, *args, **kwargs):
        raise NotImplementedError()

    def mkdir(self, *args):
        return self.parent.mkdir(*args)

class PathyDir(Pathy['dir']):
    """ A location of a directory """

class WildPathy(Pathy['*']):
    """ A Path that can handle ?wildcards, *globs, and {keys} in it.
    eg: a/path/*/?.txt
    """

    def keys(self) -> set[str]:
        raise NotImplementedError()

    def normalize(self, *, root=None, symlinks:bool=False) -> pl.Path:
        pass

    def glob(self, pattern, *, case_sensitive=None, recurse_symlinks=True):
        pass

    def rglob(self, pattern, *, case_sensitive=None, recurse_symlinks=True):
        """Recursively yield all existing files (of any kind, including
        directories) matching the given relative pattern, anywhere in
        this subtree.
        """
        if not isinstance(pattern, pl.Path):
            pattern = self.with_segments(pattern)
        pattern = '**' / pattern
        return self.glob(pattern, case_sensitive=case_sensitive, recurse_symlinks=recurse_symlinks)

    def walk_files(self, *, d_skip=None, f_skip=None, depth=None) -> iter[PathyFile]:
        """
        Walk a Path, returning applicable files
        filters directories using fn. lambda x -> bool. True skips
        filters file using f_skip(lambda x: bool), True ignores
        """
        d_skip = d_skip or (lambda x: [])
        f_skip = f_skip or (lambda x: False)
        for root, dirs, files in self.walk():
            for i in sorted((i for i,x in enumerate(dirs) if d_skip(x)), reverse=True):
                logging.debug("Removing: %s : %s", i, dirs[i])
                del dirs[i]

            for fpath in [root / f for f in files]:
                if f_skip(fpath):
                    continue
                yield Pathy['file'](fpath)

    def walk_dirs(self, *, d_skip=None, depth=None) -> iter[Pathy['dir']]:
        """
        Walk the directory tree, to a certain depth.
        d_skip: lambda x: -> bool. True skip

        returns an iterator of the available paths
        """
        d_skip = d_skip or (lambda x: False)
        for root, dirs, files in self.walk():
            for i in sorted((i for i,x in enumerate(dirs) if d_skip(x)), reverse=True):
                logging.debug("Removing: %s : %s", i, dirs[i])
                del dirs[i]
            yield from [x for x in dirs]

    def with_segments(self, *segments) -> Self:
        return Pathy['*'](*segments)
