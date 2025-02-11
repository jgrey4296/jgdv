#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

import pytest

from jgdv.structs.locator.errors import DirAbsent, LocationExpansionError, LocationError
from jgdv.structs.locator import JGDVLocator, Location
from jgdv.structs.locator.locator import _LocatorGlobal
from jgdv.structs.dkey import DKey, NonDKey

logging = logmod.root

match JGDVLocator.Current:
    case None:
        initial_loc = JGDVLocator(pl.Path.cwd())
    case x:
        initial_loc = x

@pytest.fixture(scope="function")
def simple() -> JGDVLocator:
    return JGDVLocator(pl.Path.cwd())

class TestLocator:

    def test_initial(self):
        simple = JGDVLocator(pl.Path.cwd())
        assert(isinstance(simple, JGDVLocator))
        assert(not bool(simple._data))

    def test_update(self, simple):
        assert(not bool(simple._data))
        simple.update({"blah": "file::>bloo"})
        assert(bool(simple._data))
        assert("blah" in simple)

    def test_data_stored_as_locations(self, simple):
        assert(not bool(simple._data))
        simple.update({"blah": "file::>bloo", "aweg":"aweg/abloo"})
        assert(bool(simple._data))
        for x in  simple._data.values():
            assert(isinstance(x, Location))

    def test_registered(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "file::>blah"})
        assert(bool(simple._data))
        simple.registered("a")

    def test_registered_fail(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "file::>blah"})
        assert(bool(simple._data))

        with pytest.raises(DirAbsent):
            simple.registered("b")

    def test_update_conflict(self, simple):
        simple.update({"blah": "dir::>bloo"})
        with pytest.raises(LocationError):
            simple.update({"blah": "dir::>blah"})

    def test_update_non_strict(self, simple):
        simple.update({"blah": "dir::>bloo"})
        simple.update({"blah": "dir::>bloo"}, strict=False)

    def test_update_overwrite(self, simple):
        locstr = "dir::>aweg"
        simple = JGDVLocator(pl.Path.cwd())
        simple.update({"blah": "dirr::bloo"})
        simple.update({"blah": "dir::>aweg"}, strict=False)
        assert("blah" in simple)
        assert(simple._data["blah"] == locstr)
        assert(simple.access('blah') == locstr)

    def test_empty_repr(self, simple):
        repr_str = repr(simple)
        assert(repr_str == f"<JGDVLocator (1) : {str(pl.Path.cwd())} : ()>")

    def test_non_empty_repr(self, simple):
        simple.update({"a": "dir::>blah", "b": "dir::>aweg", "awegewag": "dir::>jkwejgio"})
        repr_str = repr(simple)
        assert(repr_str == f"<JGDVLocator (1) : {str(pl.Path.cwd())} : (a, b, awegewag)>")

    def test_clear(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "dir::>blah"})
        assert("a" in simple)
        simple._clear()
        assert("a" not in simple)


    @pytest.mark.xfail
    def test_metacheck(self, simple):
        assert(False)

class TestLocatorUtils:

    def test_normalize(self, simple):
        a_path = pl.Path("a/b/c")
        expected = a_path.absolute()
        result = simple.normalize(a_path)
        assert(result == expected)

    def test_normalize_tilde(self, simple):
        result = simple.normalize(pl.Path("~/blah"))
        assert(result.is_absolute())
        assert(result == pl.Path("~/blah").expanduser())

    def test_normalize_absolute(self, simple):
        result = simple.normalize(pl.Path("/blah"))
        assert(result.is_absolute())
        assert(result == pl.Path("/blah"))

    def test_normalize_relative(self, simple):
        result = simple.normalize(pl.Path("blah"))
        assert(result.is_absolute())
        assert(result == (pl.Path.cwd() / "blah").absolute())

    def test_normalize_relative_with_different_cwd(self):
        simple = JGDVLocator(pl.Path("~/desktop/"))
        result = simple.normalize(pl.Path("blah"))
        assert(result.is_absolute())
        assert(result == (pl.Path("~/desktop/") / "blah").expanduser().absolute())

class TestLocatorGlobal:

    def test_sanity(self, simple):
        assert(True is not False)

    def test_global_Current(self, simple):
        locs = JGDVLocator(pl.Path.cwd())
        assert(isinstance(JGDVLocator.Current, JGDVLocator))

    def test_ctx_manager_basic(self, simple):
        assert(JGDVLocator.Current is initial_loc)
        with JGDVLocator.Current() as locs2:
            assert(JGDVLocator.Current is locs2)

        assert(JGDVLocator.Current is initial_loc)

    def test_ctx_manager_cwd_change(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "dir::>blah"})
        assert(bool(simple._data))
        assert(simple.root == pl.Path.cwd())
        target = pl.Path("~/Desktop").expanduser().resolve()
        with simple(pl.Path("~/Desktop")) as ctx:
            assert(ctx.root == target)

    def test_stacklen(self, simple):
        assert(_LocatorGlobal.stacklen() == 1)
        locs  = JGDVLocator(pl.Path.cwd())
        assert(_LocatorGlobal.stacklen() == 1)
        with locs() as locs2:
            assert(_LocatorGlobal.stacklen() == 2)
            with locs2() as locs3:
                assert(_LocatorGlobal.stacklen() == 3)

            assert(_LocatorGlobal.stacklen() == 2)

        assert(_LocatorGlobal.stacklen() == 1)
        assert(JGDVLocator.Current is initial_loc)

