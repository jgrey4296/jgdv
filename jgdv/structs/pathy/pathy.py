#!/usr/bin/env python3
"""
Subclasses of pathlib.Path for working with type safe:
- Abstract paths that will be expanded
- Directories,
- Files
"""
# ruff: noqa: DTZ006
# mypy: disable-error-code="arg-type,attr-defined,call-arg,misc,type-arg,valid-type"
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
import time as time_
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import DateTime, TimeDelta, Proto, Mixin
from jgdv.mixins.annotate import SubRegistry_m
from ._interface import Pure, Real, File, Dir, Wild

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, NewType
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

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class _PathyExpand_m:
    """ Mixin for normalizing the Paths """

    def normalize(self, *, root:Maybe[pl.Path]=None, symlinks:bool=False) -> pl.Path:
        """
          a basic path normalization
          expands user, and resolves the location to be absolute
        """
        result = pl.Path(self)
        if symlinks and result.is_symlink():
            msg = "symlink normalization"
            raise NotImplementedError(msg, result)

        match result.parts:
            case ["~", *_]:
                result = result.expanduser().resolve()
            case ["/", *_]:
                pass
            case _ if root:
                result = (root / result).expanduser().resolve()
            case _:
                result = result.expanduser().resolve()

        return result

class _PathyTime_m:
    """ Mixin for getting time created and modified, and comparing two files """

    def time_created(self) -> DateTime:
        stat = self.stat()
        try:
            return datetime.datetime.fromtimestamp(stat.st_birthtime)
        except AttributeError:
            return datetime.datetime.fromtimestamp(stat.st_ctime)

    def time_modified(self) -> DateTime:
        return datetime.datetime.fromtimestamp(self.stat().st_mtime)

    def _newer_than(self, time:DateTime, *, tolerance:TimeDelta=None) -> bool:
        """ True if self.time_modified() < time,
        with a tolerance because some file systems have lower resolution
        """
        if not self.exists():
            return False

        match tolerance:
            case datetime.timedelta():
                mod_time = self.time_modified()
                diff = mod_time - time
                return tolerance < diff
            case None:
                return time < self.time_modified()
            case _:
                return False

##--|
class Pathy(SubRegistry_m, annotate_to="pathy_type"):
    """
    The Main Accessor to Pathy.
    You don't build Pathy's directly eg: Pathy("a/loc/test.txt"),
    but using Subtypes: Pathy[File]("a/loc/test.txt")

    The subtypes are: Pure, Real, File, Dir, Wild
    They are class attrs of Pathy, and in the pathy module.

    Also: Pathy.cwd() and Pathy.home()
    """
    _registry : ClassVar[dict[type, pl.PurePath|pl.Path]] = {}
    __match_args__ = ("pathy_type",)
    # Standard Pathy Subtypes
    Pure = Pure
    Real = Real
    File = File
    Dir  = Dir
    Wild = Wild

    @classmethod
    def __class_getitem__(cls, param:Any) -> Self:  # noqa: ANN401
        if not isinstance(param, NewType):
            msg = "Bad Pathy Subtype"
            raise TypeError(msg, param)
        return super().__class_getitem__(param)

    @staticmethod
    def cwd() -> Pathy[Real]:
        return Pathy[Real](pl.Path.cwd())

    @staticmethod
    def home() -> Pathy[Real]:
        return Pathy[Real](pl.Path.home())

    def __new__(cls, *args, **kwargs) -> Pathy:
        """ When instantiating a Pathy, get the right subtype """
        use_cls = cls._maybe_subclass_form() or PathyPure
        if use_cls is Pathy:
            use_cls = PathyPure

        obj = object.__new__(use_cls)
        obj.__init__(*args, **kwargs)
        return obj

    def __init__(self, *paths:str|pl.Path, key=None, **kwargs):
        super().__init__(*paths)
        self._meta        = {}
        self._key         = key
        self._meta.update(kwargs)

##--|
@Mixin(_PathyExpand_m)
class PathyPure(Pathy[Pure], pl.PurePath):
    """
    A Pure Pathy, subclass of pathlib.PurePath with extra functionality
    """

    def __contains__(self, other) -> bool:
        """ a/b/c.py ∈ a/*/?.py  """
        match other:
            case str():
                return other in str(self)
            case pl.Path() if not other.is_absolute():
                return str(other) in str(self)
            case Pathy():
                msg = "TODO"
                raise NotImplementedError(msg)
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
                return other.joinpath(self)

    def __lt__(self, other:Pathy|DateTime) -> bool:
        """ do self<other for paths,
        and compare against modification time if given a datetime
        """
        match other:
            case datetime.datetime():
                return self._newer_than(other)
            case Pathy() | pl.Path():
                return super().__lt__(other)
            case _:
                return False

    def with_segments(self, *segments) -> Self:
        if isinstance(self, Pathy[File]):
            msg = "Can't subpath a file"
            raise TypeError(msg)
        match segments:
            case [*_, pl.PurePath() as x] if x.is_absolute():
                msg = "Can't join when rhs is absolute"
                raise ValueError(msg, segments)
            case [*_, PathyFile()]:
                return Pathy[File](*segments)
            case [*_, pl.Path()|str() as x] if pl.Path(x).suffix != "":
                return Pathy[File](*segments)
            case _:
                return Pathy[Dir](*segments)

    def format(self, *args, **kwargs) -> Self:
        as_str    = str(self)
        formatted = as_str.format(*args, **kwargs)
        return type(self)(formatted)

    def with_suffix(self, suffix):
        return Pathy[File](super().with_suffix(suffix))

@Mixin(_PathyTime_m)
class PathyReal(Pathy[Real], PathyPure, pl.Path):
    """
    The Pathy equivalent of pathlib.Path
    """
    pass

class PathyFile(Pathy[File], PathyReal):
    """ A Pathy for an existing File

    TODO disable:
    iterdir
    rglob
    """

    def glob(self, *args, **kwargs):
        raise NotImplementedError()

    def walk(self, *args, **kwargs):
        raise NotImplementedError()

    def mkdir(self, *args):
        return self.parent.mkdir(*args)

class PathyDir(Pathy[Dir], PathyReal):
    """ A Pathy for Directories, not files

    TODO disable:
    open, read_bytes/text, write_bytes/text
    """
    pass

class WildPathy(Pathy[Wild], PathyPure):
    """ A Pure Pathy that represents a location with wildcards and keys in it.

    ::

        Can handle wildcards (?), globs (* and **), and keys ({}) in it.
        eg: a/path/*/?.txt

    Converts to a List of PathReal's by calling 'expand'
    """

    def keys(self) -> set[str]:
        raise NotImplementedError()

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
        """ Walk a Path, returning applicable files

        | filters directories using fn. lambda x -> bool. True skips
        | filters file using f_skip(lambda x: bool), True ignores
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
        """ Walk the directory tree, to a certain depth.

        > d_skip: lambda x: -> bool. True skip

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
