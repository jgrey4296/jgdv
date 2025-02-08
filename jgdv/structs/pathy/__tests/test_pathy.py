#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import logging as logmod
import datetime
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

import pytest

from jgdv._types import *
from jgdv.structs.pathy import Pathy, Pure, Real, File, Dir
import jgdv.structs.pathy.pathy as Pth

logging = logmod.root

class TestPathy:

    def test_sanity(self):
        assert(True is True)

    def test_subclassing(self):
        assert(not issubclass(Pathy, pl.PurePath))
        assert(issubclass(Pathy[Pure], Pathy))
        assert(issubclass(Pathy[Real], Pathy))
        assert(issubclass(Pathy[Pure], pl.PurePath))
        assert(issubclass(Pathy[Real], pl.Path))
        assert(issubclass(Pathy[Real], pl.PurePath))

        assert(not issubclass(pl.Path, Pathy))
        assert(not issubclass(Pathy[Pure], pl.Path))

    def test_pathy_build(self):
        val : Pathy = Pathy("a/test")
        assert(isinstance(val, pl.PurePath))
        assert(not isinstance(val, pl.Path))
        assert(isinstance(val, Pathy))
        assert(isinstance(val, Pathy[Pure]))
        assert(hasattr(val, "__dict__"))
        assert(not hasattr(val, "exists"))

    def test_pure(self):
        val : Pathy = Pathy[Pure]("a/test")
        assert(isinstance(val, pl.PurePath))
        assert(not isinstance(val, pl.Path))
        assert(hasattr(val, "__dict__"))
        assert(not hasattr(val, "exists"))

    def test_file(self):
        val : Pathy = Pathy[File]("a/test")
        assert(isinstance(val, pl.PurePath))
        assert(isinstance(val, pl.Path))
        assert(hasattr(val, "__dict__"))
        assert(hasattr(val, "exists"))
        assert(not val.exists())

    def test_dir(self):
        val : Pathy = Pathy[Dir]("a/test/")
        assert(isinstance(val, pl.PurePath))
        assert(isinstance(val, pl.Path))
        assert(hasattr(val, "__dict__"))
        assert(hasattr(val, "exists"))
        assert(not val.exists())

    def test_with_kwargs(self):
        val = Pathy("a/test", val="blah")
        assert(isinstance(val, pl.PurePath))
        assert(hasattr(val, "_meta"))
        assert(val._meta['val'] == 'blah')

    def test_bad_annotation(self):
        with pytest.raises(TypeError):
            Pathy['blah']

class TestPathyOps:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_get_tijme_modified(self):
        obj = Pathy.cwd()
        assert(isinstance(obj.time_modified(), datetime.datetime))

    def test_get_time_created(self):
        obj = Pathy.cwd()
        assert(isinstance(obj.time_created(), datetime.datetime))

    def test_lt(self):
        obj  = Pathy("a/b/c")
        obj2 = Pathy("a/b/c/d/e")
        assert(obj < obj2)

    def test_lt_datetime(self):
        obj  = Pathy("a/b/c")
        obj2 = Pathy("a/b/c/d/e")
        assert(obj < obj2)

    def test_contains_str(self):
        obj  = Pathy("a/b/c")
        assert("b" in obj)

    def test_contains_path(self):
        obj  = Pathy("a/b/c")
        sub  = pl.Path("b/c")
        assert(sub in obj)

    def test_format(self):
        obj  = Pathy("a/{b}/c")
        res  = obj.format(b="blah")
        assert(isinstance(res, Pathy))
        assert(res == "a/blah/c")

    def test_format_keep_filetype(self):
        obj  = Pathy[File]("a/{b}/c.txt")
        res  = obj.format(b="blah")
        assert(isinstance(res, Pathy[File]))
        assert(res == "a/blah/c.txt")

class TestPathyJoin:

    def test_join_file(self):
        obj = Pathy[Dir]("a/b/c")
        obj2 = Pathy[File]("test.txt")
        obj3 =  obj / obj2
        assert(isinstance(obj3, Pathy[File]))

    def test_join_dir(self):
        obj = Pathy[Dir]("a/b/c")
        obj2 = Pathy[Dir]("test/blah")
        obj3 =  obj / obj2
        assert(isinstance(obj3, Pathy[Dir]))
        assert(obj3 == "a/b/c/test/blah")

    def test_join_file_str(self):
        obj = Pathy[Dir]("a/b/c")
        obj2 = obj / "test.txt"
        assert(isinstance(obj2, Pathy[File]))

    def test_subpath_file_fail(self):
        obj = Pathy[File]("test.txt")
        obj2 = Pathy[Dir]("blah/bloo")
        with pytest.raises(TypeError):
            obj / obj2

    def test_rjoin_for_str(self):
        obj = "a/b/c"
        obj2 = obj / Pathy("test")
        assert(isinstance(obj2, Pathy))
        assert(obj2 == "a/b/c/test")

    def test_join_relative_to_absolute_fail(self):
        obj = Pathy[Dir]("a/b/c")
        obj2 = Pathy[Dir]("/test")
        with pytest.raises(ValueError):
            obj / obj2

    def test_join_absolute(self):
        obj  = Pathy[Dir]("a/b/c")
        obj2 = Pathy[Dir]("/test")
        match obj2 / obj:
            case Pathy(Pth.Dir) as obj3:
                assert(obj3 == "/test/a/b/c")
            case x:
                assert(False), x

class TestPathy_Time:

    def test_newer_than(self):
        obj        = Pathy[File]("a/b/c.txt")
        obj.exists = lambda: True
        a_time     = datetime.datetime.fromtimestamp(pl.Path.cwd().stat().st_mtime)
        newer_time = a_time + datetime.timedelta(minutes=1)
        older_time = a_time - datetime.timedelta(minutes=1)
        assert(a_time < newer_time)
        obj.time_modified = lambda: a_time
        assert(obj.time_modified() is a_time)
        assert(not obj._newer_than(newer_time))

    def test_older_than(self):
        obj        = Pathy[File]("a/b/c.txt")
        obj.exists = lambda: True
        a_time     = datetime.datetime.fromtimestamp(pl.Path.cwd().stat().st_mtime)
        older_time = a_time - datetime.timedelta(minutes=1)
        assert(older_time < a_time)
        obj.time_modified = lambda: a_time
        assert(obj.time_modified() is a_time)
        assert(obj._newer_than(older_time))

    def test_newer_than_tolerance_fail(self):
        obj        = Pathy[File]("a/b/c.txt")
        obj.exists = lambda: True
        a_time     = datetime.datetime.fromtimestamp(pl.Path.cwd().stat().st_mtime)
        older_time = a_time - datetime.timedelta(minutes=1)
        tolerance = datetime.timedelta(days=1)
        assert(older_time < a_time)
        obj.time_modified = lambda: a_time
        assert(obj.time_modified() is a_time)
        assert(not obj._newer_than(older_time, tolerance=tolerance))

    def test_newer_than_tolerance_fail2(self):
        obj        = Pathy[File]("a/b/c.txt")
        obj.exists = lambda: True
        a_time     = datetime.datetime.fromtimestamp(pl.Path.cwd().stat().st_mtime)
        newer_time = a_time + datetime.timedelta(minutes=1)
        tolerance = datetime.timedelta(days=1)
        assert(a_time < newer_time)
        obj.time_modified = lambda: a_time
        assert(obj.time_modified() is a_time)
        assert(not obj._newer_than(newer_time, tolerance=tolerance))

    def test_newer_than_tolerance(self):
        obj        = Pathy[File]("a/b/c.txt")
        obj.exists = lambda: True
        a_time     = datetime.datetime.fromtimestamp(pl.Path.cwd().stat().st_mtime)
        older_time = a_time - datetime.timedelta(days=3)
        tolerance = datetime.timedelta(days=1)
        assert(older_time < a_time)
        obj.time_modified = lambda: a_time
        assert(obj.time_modified() is a_time)
        assert(obj._newer_than(older_time, tolerance=tolerance))

class TestPathy_Walking:

    @pytest.mark.skip
    def test_walk_dirs(self):

        def filter_fn(x):
            return x.startswith(".")

        obj = Pathy['*'].cwd()
        dirs = list(obj.walk_dirs(d_skip=filter_fn))

    @pytest.mark.skip
    def test_walk_files(self):

        def filter_fn(x):
            return x.startswith(".") or x in ["docs", "__data", "_pycache_"]

        def file_filter_fn(x):
            return x.suffix in [".py", ".pyc"]

        obj = Pathy['*'].cwd()
        files = list(obj.walk_files(d_skip=filter_fn, f_skip=file_filter_fn))

class TestPathyNormalize:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_call_normalize(self):
        obj    = Pathy("a/b/c")
        normed = obj()
        assert(isinstance(normed, pl.Path))
        assert(normed.is_absolute())

class TestPathyFile:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        val : Pathy['file'] = Pathy[File]("a/test.txt", val="blah")
        assert(val.pathy_type is File)
        assert(issubclass(Pathy[File], Pth.PathyFile))
        assert(isinstance(val, Pathy[File]))
        assert(isinstance(val, Pathy))
        assert(isinstance(val, pl.Path))
        assert(hasattr(val, "_meta"))
        assert(val._meta['val'] == 'blah')

class TestPathDir:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = Pathy[File]("blah/bloo")
        assert(isinstance(obj, pl.Path))

class TestMatching:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_match_to_pure_path(self):
        match Pathy("a/b/c"):
            case pl.PurePath():
                assert(True)
            case x:
                assert(False), x

    def test_match_to_real_path(self):
        match Pathy[Real]("a/b/c"):
            case pl.Path():
                assert(True)
            case x:
                assert(False), x

    def test_match_to_pathy(self):
        match Pathy[Real]("a/b/c"):
            case Pathy():
                assert(True)
            case x:
                assert(False), x

    def test_match_to_pathy_sub(self):
        match Pathy[Real]("a/b/c"):
            case Pth.PathyReal():
                assert(True)
            case x:
                assert(False), x

    def test_match_to_pathy_sub_2(self):
        """
        you can't do case Pathy[Real](),
        but you can do a postiional match:
        case Pathy(Pth.Real):
        """
        match Pathy[Real]("a/b/c"):
            case Pathy(Pth.Real):
                assert(True)
            case x:
                assert(False), x
