#!/usr/bin/env python3
"""

"""
# ruff: noqa: B011
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

class TestLocator_Get:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_get_registered(self, simple):
        simple.update({"blah":"bloo/blee"})
        match simple.get("blah"):
            case pl.Path() as x if x == pl.Path("bloo/blee"):
                assert(True)
            case x:
                assert(False), x

    def test_get_missing(self, simple):
        simple.update({"blah":"bloo/blee"})
        with pytest.raises(KeyError):
            simple.get("aweg")

    def test_get_fallback(self, simple):
        simple.update({"blah":"bloo/blee"})
        match simple.get("aweg", "bloo"):
            case pl.Path() as x if x == pl.Path("bloo"):
                assert(True)
            case x:
                assert(False), x

class TestLocator_Access:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_registered(self, simple):
        simple.update({"blah":"bloo/blee"})
        match simple.access("blah"):
            case Location():
                assert(True)
            case x:
                assert(False), x

    def test_missing(self, simple):
        simple.update({"blah":"bloo/blee"})
        match simple.access("aweg"):
            case None:
                assert(True)
            case x:
                assert(False), x

class TestLocator_Expand:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_nokey(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "aweg"
        match simple.expand("aweg", strict=False):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

    def test_single_registered(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "bloo/blee"
        match simple.expand("{blah}"):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

    def test_single_missing_strict(self, simple):
        simple.update({"blah":"bloo/blee"})
        with pytest.raises(KeyError):
            simple.expand("{aweg}", strict=True)

    def test_single_missing_not_strict(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "{aweg}"
        match simple.expand("{aweg}", strict=False):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_single_missing_fallback(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "bloo/blee"
        match simple.expand("{blah}"):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

    def test_multi_registered(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "bloo/blee"
        match simple.expand("{blah}"):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

    def test_multi_missing_strict(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "bloo/blee"
        match simple.expand("{blah}"):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

    def test_multi_missing_not_strict(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "bloo/blee"
        match simple.expand("{blah}"):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

    def test_multi_missing_fallback(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "bloo/blee"
        match simple.expand("{blah}"):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

    def test_simple_recursion(self, simple):
        simple.update({"blah":"bloo/blee"})
        target = pl.Path.cwd() / "bloo/blee"
        match simple.expand("{blah}"):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

    def test_double_recursion(self, simple):
        simple.update({"blah":"{bloo}/blee", "bloo":"aweg"})
        target = pl.Path.cwd() / "aweg/blee"
        match simple.expand("{blah}", strict=False):
            case pl.Path() as x if x == target:
                assert(True)
            case x:
                assert(False), x

class TestLocator_MainAccess:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_attr_basic_dir(self, simple):
        """Locator.blah            -> {cwd}/ex/dir"""
        target = Location("ex/dir")
        simple.update({"blah": "ex/dir"})
        assert("blah" in simple)
        assert(simple.blah == target)

    def test_item_basic_dir(self, simple):
        """Locator['{blah}']       -> {cwd}/ex/dir"""
        target = pl.Path.cwd() / "ex/dir"
        simple.update({"blah": "ex/dir"})
        assert("blah" in simple)
        assert(simple['{blah}'] == target)

    def test_item_join_dir(self, simple):
        """Locator['{blah}/blee']  -> {cwd}/ex/dir/blee"""
        target = pl.Path.cwd() / "ex/dir/blee"
        simple.update({"blah": "ex/dir"})
        assert("blah" in simple)
        assert(simple['{blah}/blee'] == target)

    def test_attr_basic_file(self, simple):
        """Locator.bloo            -> {cwd}/a/b/c.txt"""
        target = Location("file::>a/b/c.txt")
        simple.update({"bloo": "file::>a/b/c.txt"})
        assert("bloo" in simple)
        assert(simple.bloo == target)

    def test_item_basic_file(self, simple):
        """Locator['{bloo}']       -> {cwd}/a/b/c.txt"""
        target = pl.Path.cwd() / "a/b/c.txt"
        simple.update({"bloo": "file::>a/b/c.txt"})
        assert("bloo" in simple)
        assert(simple['{bloo}'] == target)

    def test_item_dir_file_join(self, simple):
        """ Locator[a/b/c] -> {cwd}/a/b/c """
        target = pl.Path.cwd() / "a/b/c"
        simple.update({"bloo": "dir::>a/b/c"})
        assert("bloo" in simple)
        assert(simple['{bloo}'] == target)

    def test_item_nonkey(self, simple):
        """ Locator[bloo/blah] -> {cwd}/bloo/blah """
        target = pl.Path.cwd() / "bloo/blah"
        simple.update({"bloo": "dir::>a/b/c"})
        assert("bloo" in simple)
        assert(simple['bloo/blah'] == target)

class TestLocation_ExpansionConflict:

    @pytest.mark.xfail
    def test_item_file_join_fail(self, simple):
        """Locator['{bloo}/blee']  -> Error"""
        simple.update({"bloo": "file::>a/b/c.txt"})
        assert("bloo" in simple)
        with pytest.raises(LocationError):
            simple['{bloo}/blah']
