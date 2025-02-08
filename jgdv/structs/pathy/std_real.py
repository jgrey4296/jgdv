#!/usr/bin/env python3jj
"""

"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import atexit# for @atexit.register
import collections
import contextlib
import datetime
import enum
import faulthandler
import functools as ftz
import hashlib
import io
import itertools as itz
import logging as logmod
import operator
import os
import pathlib as pl
import posixpath
import re
import shutil
import sys
import time
import types
from copy import deepcopy
from errno import EXDEV
from glob import _no_recurse_symlinks, _StringGlobber
from pathlib import (
    ReadablePath,
    UnsupportedOperation,
    WritablePath,
    _LocalCopyReader,
    _LocalCopyWriter,
    grp,
    pwd,
)
from stat import S_IMODE, S_ISBLK, S_ISCHR, S_ISDIR, S_ISFIFO, S_ISREG, S_ISSOCK
from urllib.parse import unquote_to_bytes
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

from  .std_pure import PurePath, PurePosixPath, PureWindowsPath

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

class RealClassMethod_m:

    @classmethod
    def cwd(cls):
        """Return a new path pointing to the current working directory."""
        cwd = os.getcwd()
        path = cls(cwd)
        path._str = cwd  # getcwd() returns a normalized path
        return path

    @classmethod
    def home(cls):
        """Return a new path pointing to expanduser('~').
        """
        homedir = os.path.expanduser("~")
        if homedir == "~":
            raise RuntimeError("Could not determine home directory.")
        return cls(homedir)

    @classmethod
    def from_uri(cls, uri):
        """Return a new path from the given 'file' URI."""
        if not uri.startswith('file:'):
            raise ValueError(f"URI does not start with 'file:': {uri!r}")
        path = uri[5:]
        if path[:3] == '///':
            # Remove empty authority
            path = path[2:]
        elif path[:12] == '//localhost/':
            # Remove 'localhost' authority
            path = path[11:]
        if path[:3] == '///' or (path[:1] == '/' and path[2:3] in ':|'):
            # Remove slash before DOS device/UNC path
            path = path[1:]
        if path[1:2] == '|':
            # Replace bar with colon in DOS drive
            path = path[:1] + ':' + path[2:]
        path = cls(os.fsdecode(unquote_to_bytes(path)))
        if not path.is_absolute():
            raise ValueError(f"URI is not absolute: {uri!r}")
        return path

class RealTests_m:

    def exists(self, *, follow_symlinks=True):
        """
        Whether this path exists.

        This method normally follows symlinks; to check whether a symlink exists,
        add the argument follow_symlinks=False.
        """
        if follow_symlinks:
            return os.path.exists(self)
        return os.path.lexists(self)

    def is_dir(self, *, follow_symlinks=True):
        """
        Whether this path is a directory.
        """
        if follow_symlinks:
            return os.path.isdir(self)
        try:
            return S_ISDIR(self.stat(follow_symlinks=follow_symlinks).st_mode)
        except (OSError, ValueError):
            return False

    def is_file(self, *, follow_symlinks=True):
        """
        Whether this path is a regular file (also True for symlinks pointing
        to regular files).
        """
        if follow_symlinks:
            return os.path.isfile(self)
        try:
            return S_ISREG(self.stat(follow_symlinks=follow_symlinks).st_mode)
        except (OSError, ValueError):
            return False

    def is_mount(self):
        """
        Check if this path is a mount point
        """
        return os.path.ismount(self)

    def is_symlink(self):
        """
        Whether this path is a symbolic link.
        """
        return os.path.islink(self)

    def is_junction(self):
        """
        Whether this path is a junction.
        """
        return os.path.isjunction(self)

    def is_block_device(self):
        """
        Whether this path is a block device.
        """
        try:
            return S_ISBLK(self.stat().st_mode)
        except (OSError, ValueError):
            return False

    def is_char_device(self):
        """
        Whether this path is a character device.
        """
        try:
            return S_ISCHR(self.stat().st_mode)
        except (OSError, ValueError):
            return False

    def is_fifo(self):
        """
        Whether this path is a FIFO.
        """
        try:
            return S_ISFIFO(self.stat().st_mode)
        except (OSError, ValueError):
            return False

    def is_socket(self):
        """
        Whether this path is a socket.
        """
        try:
            return S_ISSOCK(self.stat().st_mode)
        except (OSError, ValueError):
            return False

    def samefile(self, other_path):
        """Return whether other_path is the same or not as this file
        (as returned by os.path.samefile()).
        """
        st = self.stat()
        try:
            other_st = other_path.stat()
        except AttributeError:
            other_st = self.with_segments(other_path).stat()
        return (st.st_ino == other_st.st_ino and
                st.st_dev == other_st.st_dev)

class RealOpening_m:

    def _scandir(self):
        """Yield os.DirEntry-like objects of the directory contents.

        The children are yielded in arbitrary order, and the
        special entries '.' and '..' are not included.
        """
        return os.scandir(self)

    def stat(self, *, follow_symlinks=True):
        """
        Return the result of the stat() system call on this path, like
        os.stat() does.
        """
        return os.stat(self, follow_symlinks=follow_symlinks)

    def lstat(self):
        """
        Like stat(), except if the path points to a symlink, the symlink's
        status information is returned, rather than its target's.
        """
        return os.lstat(self)

    def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
        return io.open(self, mode, buffering, encoding, errors, newline)

    def read_bytes(self):
        """
        Open the file in bytes mode, read it, and close the file.
        """
        with self.open(mode='rb', buffering=0) as f:
            return f.read()

    def read_text(self, encoding=None, errors=None, newline=None):
        """
        Open the file in text mode, read it, and close the file.
        """
        # Call io.text_encoding() here to ensure any warning is raised at an
        # appropriate stack level.
        encoding = io.text_encoding(encoding)
        with self.open(mode='r', encoding=encoding, errors=errors, newline=newline) as f:
            return f.read()

    def write_bytes(self, data):
        """
        Open the file in bytes mode, write to it, and close the file.
        """
        # type-check for the buffer interface before truncating the file
        view = memoryview(data)
        with self.open(mode='wb') as f:
            return f.write(view)

    def write_text(self, data, encoding=None, errors=None, newline=None):
        """
        Open the file in text mode, write to it, and close the file.
        """
        # Call io.text_encoding() here to ensure any warning is raised at an
        # appropriate stack level.
        encoding = io.text_encoding(encoding)
        if not isinstance(data, str):
            raise TypeError('data must be str, not %s' %
                            data.__class__.__name__)
        with self.open(mode='w', encoding=encoding, errors=errors, newline=newline) as f:
            return f.write(data)

    _remove_leading_dot = operator.itemgetter(slice(2, None))
    _remove_trailing_slash = operator.itemgetter(slice(-1))

    def iterdir(self):
        """Yield path objects of the directory contents.

        The children are yielded in arbitrary order, and the
        special entries '.' and '..' are not included.
        """
        root_dir = str(self)
        with os.scandir(root_dir) as scandir_it:
            paths = [entry.path for entry in scandir_it]
        if root_dir == '.':
            paths = map(self._remove_leading_dot, paths)
        return map(self._from_parsed_string, paths)

    def glob(self, pattern, *, case_sensitive=None, recurse_symlinks=False):
        """Iterate over this subtree and yield all existing files (of any
        kind, including directories) matching the given relative pattern.
        """
        sys.audit("pathlib.Path.glob", self, pattern)
        if case_sensitive is None:
            case_sensitive = self.parser is posixpath
            case_pedantic = False
        else:
            # The user has expressed a case sensitivity choice, but we don't
            # know the case sensitivity of the underlying filesystem, so we
            # must use scandir() for everything, including non-wildcard parts.
            case_pedantic = True
        parts = self._parse_pattern(pattern)
        recursive = True if recurse_symlinks else _no_recurse_symlinks
        globber = _StringGlobber(self.parser.sep, case_sensitive, case_pedantic, recursive)
        select = globber.selector(parts[::-1])
        root = str(self)
        paths = select(root)

        # Normalize results
        if root == '.':
            paths = map(self._remove_leading_dot, paths)
        if parts[-1] == '':
            paths = map(self._remove_trailing_slash, paths)
        elif parts[-1] == '**':
            paths = self._filter_trailing_slash(paths)
        paths = map(self._from_parsed_string, paths)
        return paths

    def rglob(self, pattern, *, case_sensitive=None, recurse_symlinks=False):
        """Recursively yield all existing files (of any kind, including
        directories) matching the given relative pattern, anywhere in
        this subtree.
        """
        sys.audit("pathlib.Path.rglob", self, pattern)
        pattern = self.parser.join('**', pattern)
        return self.glob(pattern, case_sensitive=case_sensitive, recurse_symlinks=recurse_symlinks)

    def walk(self, top_down=True, on_error=None, follow_symlinks=False):
        """Walk the directory tree from this directory, similar to os.walk()."""
        sys.audit("pathlib.Path.walk", self, on_error, follow_symlinks)
        root_dir = str(self)
        if not follow_symlinks:
            follow_symlinks = os._walk_symlinks_as_files
        results = os.walk(root_dir, top_down, on_error, follow_symlinks)
        for path_str, dirnames, filenames in results:
            if root_dir == '.':
                path_str = path_str[2:]
            yield self._from_parsed_string(path_str), dirnames, filenames

    def owner(self, *, follow_symlinks=True):
        """
        Return the login name of the file owner.
        """
        if pwd:
            uid = self.stat(follow_symlinks=follow_symlinks).st_uid
            return pwd.getpwuid(uid).pw_name
        else:
            f = f"{type(self).__name__}.owner()"
            raise UnsupportedOperation(f"{f} is unsupported on this system")

    def group(self, *, follow_symlinks=True):
        """
        Return the group name of the file gid.
        """
        if grp:
            gid = self.stat(follow_symlinks=follow_symlinks).st_gid
            return grp.getgrgid(gid).gr_name
        else:
            f = f"{type(self).__name__}.group()"
            raise UnsupportedOperation(f"{f} is unsupported on this system")

    def readlink(self):
        """
        Return the path to which the symbolic link points.
        """
        if hasattr(os, "readlink"):
            return self.with_segments(os.readlink(self))
        else:
            f = f"{type(self).__name__}.readlink()"
            raise UnsupportedOperation(f"{f} is unsupported on this system")

class RealManip_m:

    def _delete(self):
        """
        Delete this file or directory (including all sub-directories).
        """
        if self.is_symlink() or self.is_junction():
            self.unlink()
        elif self.is_dir():
            shutil.rmtree(self)
        else:
            self.unlink()

    def _filter_trailing_slash(self, paths):
        sep = self.parser.sep
        anchor_len = len(self.anchor)
        for path_str in paths:
            if len(path_str) > anchor_len and path_str[-1] == sep:
                path_str = path_str[:-1]
            yield path_str

    def absolute(self):
        """Return an absolute version of this path
        No normalization or symlink resolution is performed.

        Use resolve() to resolve symlinks and remove '..' segments.
        """
        if self.is_absolute():
            return self
        if self.root:
            drive = os.path.splitroot(os.getcwd())[0]
            return self._from_parsed_parts(drive, self.root, self._tail)
        if self.drive:
            # There is a CWD on each drive-letter drive.
            cwd = os.path.abspath(self.drive)
        else:
            cwd = os.getcwd()
        if not self._tail:
            # Fast path for "empty" paths, e.g. Path("."), Path("") or Path().
            # We pass only one argument to with_segments() to avoid the cost
            # of joining, and we exploit the fact that getcwd() returns a
            # fully-normalized string by storing it in _str. This is used to
            # implement Path.cwd().
            return self._from_parsed_string(cwd)
        drive, root, rel = os.path.splitroot(cwd)
        if not rel:
            return self._from_parsed_parts(drive, root, self._tail)
        tail = rel.split(self.parser.sep)
        tail.extend(self._tail)
        return self._from_parsed_parts(drive, root, tail)

    def resolve(self, strict=False):
        """
        Make the path absolute, resolving all symlinks on the way and also
        normalizing it.
        """

        return self.with_segments(os.path.realpath(self, strict=strict))

    def touch(self, mode=0o666, exist_ok=True):
        """
        Create this file with the given access mode, if it doesn't exist.
        """

        if exist_ok:
            # First try to bump modification time
            # Implementation note: GNU touch uses the UTIME_NOW option of
            # the utimensat() / futimens() functions.
            try:
                os.utime(self, None)
            except OSError:
                # Avoid exception chaining
                pass
            else:
                return
        flags = os.O_CREAT | os.O_WRONLY
        if not exist_ok:
            flags |= os.O_EXCL
        fd = os.open(self, flags, mode)
        os.close(fd)

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """
        Create a new directory at this given path.
        """
        try:
            os.mkdir(self, mode)
        except FileNotFoundError:
            if not parents or self.parent == self:
                raise
            self.parent.mkdir(parents=True, exist_ok=True)
            self.mkdir(mode, parents=False, exist_ok=exist_ok)
        except OSError:
            # Cannot rely on checking for EEXIST, since the operating system
            # could give priority to other errors like EACCES or EROFS
            if not exist_ok or not self.is_dir():
                raise

    def chmod(self, mode, *, follow_symlinks=True):
        """
        Change the permissions of the path, like os.chmod().
        """
        os.chmod(self, mode, follow_symlinks=follow_symlinks)

    def lchmod(self, mode):
        """
        Like chmod(), except if the path points to a symlink, the symlink's
        permissions are changed, rather than its target's.
        """
        self.chmod(mode, follow_symlinks=False)

    def unlink(self, missing_ok=False):
        """
        Remove this file or link.
        If the path is a directory, use rmdir() instead.
        """
        try:
            os.unlink(self)
        except FileNotFoundError:
            if not missing_ok:
                raise

    def rmdir(self):
        """
        Remove this directory.  The directory must be empty.
        """
        os.rmdir(self)

    def rename(self, target):
        """
        Rename this path to the target path.

        The target path may be absolute or relative. Relative paths are
        interpreted relative to the current working directory, *not* the
        directory of the Path object.

        Returns the new Path instance pointing to the target path.
        """
        os.rename(self, target)
        return self.with_segments(target)

    def replace(self, target):
        """
        Rename this path to the target path, overwriting if that path exists.

        The target path may be absolute or relative. Relative paths are
        interpreted relative to the current working directory, *not* the
        directory of the Path object.

        Returns the new Path instance pointing to the target path.
        """
        os.replace(self, target)
        return self.with_segments(target)

    def move(self, target):
        """
        Recursively move this file or directory tree to the given destination.
        """
        # Use os.replace() if the target is os.PathLike and on the same FS.
        try:
            target_str = os.fspath(target)
        except TypeError:
            pass
        else:
            if not hasattr(target, '_copy_writer'):
                target = self.with_segments(target_str)
            target._copy_writer._ensure_different_file(self)
            try:
                os.replace(self, target_str)
                return target
            except OSError as err:
                if err.errno != EXDEV:
                    raise
        # Fall back to copy+delete.
        target = self.copy(target, follow_symlinks=False, preserve_metadata=True)
        self._delete()
        return target

    def move_into(self, target_dir):
        """
        Move this file or directory tree into the given existing directory.
        """
        name = self.name
        if not name:
            raise ValueError(f"{self!r} has an empty name")
        elif hasattr(target_dir, '_copy_writer'):
            target = target_dir / name
        else:
            target = self.with_segments(target_dir, name)
        return self.move(target)

    def symlink_to(self, target, target_is_directory=False):
        """
        Make this path a symlink pointing to the target path.
        Note the order of arguments (link, target) is the reverse of os.symlink.
        """
        if hasattr(os, "symlink"):
            os.symlink(target, self, target_is_directory)
        else:
            f = f"{type(self).__name__}.symlink_to()"
            raise UnsupportedOperation(f"{f} is unsupported on this system")

    def hardlink_to(self, target):
        """
        Make this path a hard link pointing to the same file as *target*.

        Note the order of arguments (self, target) is the reverse of os.link's.
        """
        if hasattr(os, "link"):
            os.link(target, self)
        else:
            f = f"{type(self).__name__}.hardlink_to()"
            raise UnsupportedOperation(f"{f} is unsupported on this system")

    def expanduser(self):
        """ Return a new path with expanded ~ and ~user constructs
        (as returned by os.path.expanduser)
        """
        if (not (self.drive or self.root) and
            self._tail and self._tail[0][:1] == '~'):
            homedir = os.path.expanduser(self._tail[0])
            if homedir[:1] == "~":
                raise RuntimeError("Could not determine home directory.")
            drv, root, tail = self._parse_path(homedir)
            return self._from_parsed_parts(drv, root, tail + self._tail[1:])

        return self

class Path(RealClassMethod_m, RealTests_m, RealOpening_m, RealManip_m,  WritablePath, ReadablePath, PurePath):
    """PurePath subclass that can make system calls.

    Path represents a filesystem path but unlike PurePath, also offers
    methods to do system calls on path objects. Depending on your system,
    instantiating a Path will return either a PosixPath or a WindowsPath
    object. You can also instantiate a PosixPath or WindowsPath directly,
    but cannot instantiate a WindowsPath on a POSIX system or vice versa.
    """
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        if cls is Path:
            cls = WindowsPath if os.name == 'nt' else PosixPath
        return object.__new__(cls)

    _copy_reader = property(_LocalCopyReader)
    _copy_writer = property(_LocalCopyWriter)

class PosixPath(Path, PurePosixPath):
    """Path subclass for non-Windows systems.

    On a POSIX system, instantiating a Path should return this object.
    """
    __slots__ = ()

    if os.name == 'nt':

        def __new__(cls, *args, **kwargs):
            raise UnsupportedOperation(
                f"cannot instantiate {cls.__name__!r} on your system")

class WindowsPath(Path, PureWindowsPath):
    """Path subclass for Windows systems.

    On a Windows system, instantiating a Path should return this object.
    """
    __slots__ = ()

    if os.name != 'nt':

        def __new__(cls, *args, **kwargs):
            raise UnsupportedOperation(
                f"cannot instantiate {cls.__name__!r} on your system")
