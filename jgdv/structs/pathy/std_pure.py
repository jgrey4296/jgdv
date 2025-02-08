#!/usr/bin/env python3
"""

"""
# ruff: noqa:

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import atexit# for @atexit.register
import collections
import contextlib
import datetime
import enum
import errno
import faulthandler
import functools as ftz
import hashlib
import io
import itertools as itz
import logging as logmod
import ntpath
import operator
import os
import pathlib as pl
import posixpath
import re
import sys
import time
import types
from copy import deepcopy
from glob import _no_recurse_symlinks, _StringGlobber
from itertools import chain
from pathlib._abc import (
    CopyReader,
    CopyWriter,
    JoinablePath,
    ReadablePath,
    WritablePath,
    _PathParents,
)
from pathlib._os import copyfile
from stat import S_IMODE, S_ISBLK, S_ISCHR, S_ISDIR, S_ISFIFO, S_ISREG, S_ISSOCK
from urllib.parse import quote_from_bytes
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 3rd party imports
from _collections_abc import Sequence

# ##-- end 3rd party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
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

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class PureDunders_m:

    def __reduce__(self):
        return self.__class__, tuple(self._raw_paths)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.as_posix())

    def __fspath__(self):
        return str(self)

    def __bytes__(self):
        """Return the bytes representation of the path.  This is only
        recommended to use under Unix."""
        return os.fsencode(self)

    def __hash__(self):
        try:
            return self._hash
        except AttributeError:
            self._hash = hash(self._str_normcase)
            return self._hash

    def __truediv__(self, key):
        try:
            return self.with_segments(self, key)
        except TypeError:
            return NotImplemented

    def __rtruediv__(self, key):
        try:
            return self.with_segments(key, self)
        except TypeError:
            return NotImplemented

    def __eq__(self, other):
        if not isinstance(other, PurePath):
            return NotImplemented
        return self._str_normcase == other._str_normcase and self.parser is other.parser

    def __lt__(self, other):
        if not isinstance(other, PurePath) or self.parser is not other.parser:
            return NotImplemented
        return self._parts_normcase < other._parts_normcase

    def __le__(self, other):
        if not isinstance(other, PurePath) or self.parser is not other.parser:
            return NotImplemented
        return self._parts_normcase <= other._parts_normcase

    def __gt__(self, other):
        if not isinstance(other, PurePath) or self.parser is not other.parser:
            return NotImplemented
        return self._parts_normcase > other._parts_normcase

    def __ge__(self, other):
        if not isinstance(other, PurePath) or self.parser is not other.parser:
            return NotImplemented
        return self._parts_normcase >= other._parts_normcase

    def __str__(self):
        """Return the string representation of the path, suitable for
        passing to system calls."""
        try:
            return self._str
        except AttributeError:
            self._str = self._format_parsed_parts(self.drive, self.root,
                                                  self._tail) or '.'
            return self._str

class PureParsing_m:

    @property
    def _str_normcase(self):
        # String with normalized case, for hashing and equality checks
        try:
            return self._str_normcase_cached
        except AttributeError:
            if self.parser is posixpath:
                self._str_normcase_cached = str(self)
            else:
                self._str_normcase_cached = str(self).lower()
            return self._str_normcase_cached

    @property
    def _parts_normcase(self):
        # Cached parts with normalized case, for comparisons.
        try:
            return self._parts_normcase_cached
        except AttributeError:
            self._parts_normcase_cached = self._str_normcase.split(self.parser.sep)
            return self._parts_normcase_cached

    @classmethod
    def _format_parsed_parts(cls, drv, root, tail):
        if drv or root:
            return drv + root + cls.parser.sep.join(tail)
        elif tail and cls.parser.splitdrive(tail[0])[0]:
            tail = ['.'] + tail
        return cls.parser.sep.join(tail)

    def _from_parsed_parts(self, drv, root, tail):
        path = self._from_parsed_string(self._format_parsed_parts(drv, root, tail))
        path._drv = drv
        path._root = root
        path._tail_cached = tail
        return path

    def _from_parsed_string(self, path_str):
        path = self.with_segments(path_str)
        path._str = path_str or '.'
        return path

    @classmethod
    def _parse_path(cls, path):
        if not path:
            return '', '', []
        sep = cls.parser.sep
        altsep = cls.parser.altsep
        if altsep:
            path = path.replace(altsep, sep)
        drv, root, rel = cls.parser.splitroot(path)
        if not root and drv.startswith(sep) and not drv.endswith(sep):
            drv_parts = drv.split(sep)
            if len(drv_parts) == 4 and drv_parts[2] not in '?.':
                # e.g. //server/share
                root = sep
            elif len(drv_parts) == 6:
                # e.g. //?/unc/server/share
                root = sep
        return drv, root, [x for x in rel.split(sep) if x and x != '.']

    @classmethod
    def _parse_pattern(cls, pattern):
        """Parse a glob pattern to a list of parts. This is much like
        _parse_path, except:

        - Rather than normalizing and returning the drive and root, we raise
          NotImplementedError if either are present.
        - If the path has no real parts, we raise ValueError.
        - If the path ends in a slash, then a final empty part is added.
        """
        drv, root, rel = cls.parser.splitroot(pattern)
        if root or drv:
            raise NotImplementedError("Non-relative patterns are unsupported")
        sep = cls.parser.sep
        altsep = cls.parser.altsep
        if altsep:
            rel = rel.replace(altsep, sep)
        parts = [x for x in rel.split(sep) if x and x != '.']
        if not parts:
            raise ValueError(f"Unacceptable pattern: {str(pattern)!r}")
        elif rel.endswith(sep):
            # GH-65238: preserve trailing slash in glob patterns.
            parts.append('')
        return parts

    def with_segments(self, *pathsegments):
        """Construct a new path object from any number of path-like objects.
        Subclasses may override this method to customize how new path objects
        are created from methods like `iterdir()`.
        """
        return type(self)(*pathsegments)

class PureAccess_m:

    def _raw_path(self):
        paths = self._raw_paths
        if len(paths) == 1:
            return paths[0]
        elif paths:
            # Join path segments from the initializer.
            path = self.parser.join(*paths)
            # Cache the joined path.
            paths.clear()
            paths.append(path)
            return path
        else:
            paths.append('')
            return ''

    @property
    def _tail(self):
        try:
            return self._tail_cached
        except AttributeError:
            self._drv, self._root, self._tail_cached = self._parse_path(self._raw_path)
            return self._tail_cached

    @property
    def as_posix(self):
        """Return the string representation of the path with forward (/)
        slashes."""
        return str(self).replace(self.parser.sep, '/')

    @property
    def drive(self):
        """The drive prefix (letter or UNC path), if any."""
        try:
            return self._drv
        except AttributeError:
            self._drv, self._root, self._tail_cached = self._parse_path(self._raw_path)
            return self._drv

    @property
    def root(self):
        """The root of the path, if any."""
        try:
            return self._root
        except AttributeError:
            self._drv, self._root, self._tail_cached = self._parse_path(self._raw_path)
            return self._root

    @property
    def anchor(self):
        """The concatenation of the drive and root, or ''."""
        return self.drive + self.root

    @property
    def parts(self):
        """An object providing sequence-like access to the
        components in the filesystem path."""
        if self.drive or self.root:
            return (self.drive + self.root,) + tuple(self._tail)
        else:
            return tuple(self._tail)

    @property
    def parent(self):
        """The logical parent of the path."""
        drv = self.drive
        root = self.root
        tail = self._tail
        if not tail:
            return self
        return self._from_parsed_parts(drv, root, tail[:-1])

    @property
    def parents(self):
        """A sequence of this path's logical parents."""
        # The value of this property should not be cached on the path object,
        # as doing so would introduce a reference cycle.
        return _PathParents(self)

    @property
    def name(self):
        """The final path component, if any."""
        tail = self._tail
        if not tail:
            return ''
        return tail[-1]

    @property
    def stem(self):
        """The final path component, minus its last suffix."""
        name = self.name
        i = name.rfind('.')
        if i != -1:
            stem = name[:i]
            # Stem must contain at least one non-dot character.
            if stem.lstrip('.'):
                return stem
        return name

    @property
    def suffix(self):
        """
        The final component's last suffix, if any.

        This includes the leading period. For example: '.txt'
        """
        name = self.name.lstrip('.')
        i = name.rfind('.')
        if i != -1:
            return name[i:]
        return ''

    @property
    def suffixes(self):
        """
        A list of the final component's suffixes, if any.

        These include the leading periods. For example: ['.tar', '.gz']
        """
        return ['.' + ext for ext in self.name.lstrip('.').split('.')[1:]]

class PureTests_m:

    def relative_to(self, other, *, walk_up=False):
        """Return the relative path to another path identified by the passed
        arguments.  If the operation is not possible (because this is not
        related to the other path), raise ValueError.

        The *walk_up* parameter controls whether `..` may be used to resolve
        the path.
        """
        if not isinstance(other, PurePath):
            other = self.with_segments(other)
        parent_step = 0
        for step, path in enumerate(chain([other], other.parents)):
            parent_step = step
            if path == self or path in self.parents:
                break
            elif not walk_up:
                raise ValueError(f"{str(self)!r} is not in the subpath of {str(other)!r}")
            elif path.name == '..':
                raise ValueError(f"'..' segment in {str(other)!r} cannot be walked")
        else:
            raise ValueError(f"{str(self)!r} and {str(other)!r} have different anchors")

        parts = ['..'] * parent_step + self._tail[len(path._tail):]
        return self._from_parsed_parts('', '', parts)

    def is_relative_to(self, other):
        """Return True if the path is relative to another path or False.
        """
        if not isinstance(other, PurePath):
            other = self.with_segments(other)
        return other == self or other in self.parents

    def is_absolute(self):
        """True if the path is absolute (has both a root and, if applicable,
        a drive)."""
        if self.parser is posixpath:
            # Optimization: work with raw paths on POSIX.
            for path in self._raw_paths:
                if path.startswith('/'):
                    return True
            return False
        return self.parser.isabs(self)

    def full_match(self, pattern, *, case_sensitive=None):
        """
        Return True if this path matches the given glob-style pattern. The
        pattern is matched against the entire path.
        """
        if not isinstance(pattern, PurePath):
            pattern = self.with_segments(pattern)
        if case_sensitive is None:
            case_sensitive = self.parser is posixpath

        # The string representation of an empty path is a single dot ('.'). Empty
        # paths shouldn't match wildcards, so we change it to the empty string.
        path = str(self) if self.parts else ''
        pattern = str(pattern) if pattern.parts else ''
        globber = _StringGlobber(self.parser.sep, case_sensitive, recursive=True)
        return globber.compile(pattern)(path) is not None

    def match(self, path_pattern, *, case_sensitive=None):
        """
        Return True if this path matches the given pattern. If the pattern is
        relative, matching is done from the right; otherwise, the entire path
        is matched. The recursive wildcard '**' is *not* supported by this
        method.
        """
        if not isinstance(path_pattern, PurePath):
            path_pattern = self.with_segments(path_pattern)
        if case_sensitive is None:
            case_sensitive = self.parser is posixpath
        path_parts = self.parts[::-1]
        pattern_parts = path_pattern.parts[::-1]
        if not pattern_parts:
            raise ValueError("empty pattern")
        if len(path_parts) < len(pattern_parts):
            return False
        if len(path_parts) > len(pattern_parts) and path_pattern.anchor:
            return False
        globber = _StringGlobber(self.parser.sep, case_sensitive)
        for path_part, pattern_part in zip(path_parts, pattern_parts, strict=False):
            match = globber.compile(pattern_part)
            if match(path_part) is None:
                return False
        return True

class PureManip_m:

    def joinpath(self, *pathsegments):
        """Combine this path with one or several arguments, and return a
        new path representing either a subpath (if all arguments are relative
        paths) or a totally different path (if one of the arguments is
        anchored).
        """
        return self.with_segments(self, *pathsegments)

    def with_name(self, name):
        """Return a new path with the file name changed."""
        p = self.parser
        if not name or p.sep in name or (p.altsep and p.altsep in name) or name == '.':
            raise ValueError(f"Invalid name {name!r}")
        tail = self._tail.copy()
        if not tail:
            raise ValueError(f"{self!r} has an empty name")
        tail[-1] = name
        return self._from_parsed_parts(self.drive, self.root, tail)

    def as_uri(self):
        """Return the path as a URI."""
        if not self.is_absolute():
            raise ValueError("relative path can't be expressed as a file URI")

        drive = self.drive
        if len(drive) == 2 and drive[1] == ':':
            # It's a path on a local drive => 'file:///c:/a/b'
            prefix = 'file:///' + drive
            path = self.as_posix()[2:]
        elif drive:
            # It's a path on a network drive => 'file://host/share/a/b'
            prefix = 'file:'
            path = self.as_posix()
        else:
            # It's a posix path => 'file:///etc/hosts'
            prefix = 'file://'
            path = str(self)
        return prefix + quote_from_bytes(os.fsencode(path))

class PurePath(JoinablePath, PureDunders_m, PureParsing_m, PureAccess_m, PureTests_m, PureManip_m):
    """Base class for manipulating paths without I/O.

    PurePath represents a filesystem path and offers operations which
    don't imply any actual filesystem I/O.  Depending on your system,
    instantiating a PurePath will return either a PurePosixPath or a
    PureWindowsPath object.  You can also instantiate either of these classes
    directly, regardless of your system.
    """

    __slots__ = (
        # The `_raw_paths` slot stores unjoined string paths. This is set in
        # the `__init__()` method.
        '_raw_paths',

        # The `_drv`, `_root` and `_tail_cached` slots store parsed and
        # normalized parts of the path. They are set when any of the `drive`,
        # `root` or `_tail` properties are accessed for the first time. The
        # three-part division corresponds to the result of
        # `os.path.splitroot()`, except that the tail is further split on path
        # separators (i.e. it is a list of strings), and that the root and
        # tail are normalized.
        '_drv', '_root', '_tail_cached',

        # The `_str` slot stores the string representation of the path,
        # computed from the drive, root and tail when `__str__()` is called
        # for the first time. It's used to implement `_str_normcase`
        '_str',

        # The `_str_normcase_cached` slot stores the string path with
        # normalized case. It is set when the `_str_normcase` property is
        # accessed for the first time. It's used to implement `__eq__()`
        # `__hash__()`, and `_parts_normcase`
        '_str_normcase_cached',

        # The `_parts_normcase_cached` slot stores the case-normalized
        # string path after splitting on path separators. It's set when the
        # `_parts_normcase` property is accessed for the first time. It's used
        # to implement comparison methods like `__lt__()`.
        '_parts_normcase_cached',

        # The `_hash` slot stores the hash of the case-normalized string
        # path. It's set when `__hash__()` is called for the first time.
        '_hash',
    )
    parser = os.path

    def __new__(cls, *args, **kwargs):
        """Construct a PurePath from one or several strings and or existing
        PurePath objects.  The strings and path objects are combined so as
        to yield a canonicalized path, which is incorporated into the
        new PurePath object.
        """
        if cls is PurePath:
            cls = PureWindowsPath if os.name == 'nt' else PurePosixPath
        return object.__new__(cls)

    def __init__(self, *args):
        paths = []
        for arg in args:
            if isinstance(arg, PurePath):
                if arg.parser is not self.parser:
                    # GH-103631: Convert separators for backwards compatibility.
                    paths.append(arg.as_posix())
                else:
                    paths.extend(arg._raw_paths)
            else:
                try:
                    path = os.fspath(arg)
                except TypeError:
                    path = arg
                if not isinstance(path, str):
                    raise TypeError(
                        "argument should be a str or an os.PathLike "
                        "object where __fspath__ returns a str, "
                        f"not {type(path).__name__!r}")
                paths.append(path)
        self._raw_paths = paths

class PurePosixPath(PurePath):
    """PurePath subclass for non-Windows systems.

    On a POSIX system, instantiating a PurePath should return this object.
    However, you can also instantiate it directly on any system.
    """
    parser = posixpath
    __slots__ = ()

class PureWindowsPath(PurePath):
    """PurePath subclass for Windows systems.

    On a Windows system, instantiating a PurePath should return this object.
    However, you can also instantiate it directly on any system.
    """
    parser = ntpath
    __slots__ = ()

# Subclassing os.PathLike makes isinstance() checks slower,
# which in turn makes Path construction slower. Register instead!
os.PathLike.register(PurePath)
