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

import tomlguard
from jgdv.structs.strang.errors import DirAbsent, LocationExpansionError, LocationError
from jgdv.structs.strang.locations import JGDVLocations, _LocationsGlobal
from jgdv.structs.dkey import DKey, NonDKey

logging = logmod.root

match JGDVLocations.Current:
    case None:
        initial_loc = JGDVLocations(pl.Path.cwd())
    case x:
        initial_loc = x

class TestLocations:

    def test_initial(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(isinstance(simple, JGDVLocations))
        assert(not bool(simple._data))

    def test_update(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"blah": "file::bloo"})
        assert(bool(simple._data))
        assert("blah" in simple)

    def test_registered(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "file::blah"})
        assert(bool(simple._data))
        simple.registered("a")

    def test_registered_fail(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "file::blah"})
        assert(bool(simple._data))

        with pytest.raises(DirAbsent):
            simple.registered("b")

    def test_update_conflict(self):
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"blah": "dir::bloo"})
        with pytest.raises(LocationError):
            simple.update({"blah": "dir::blah"})

    def test_update_non_strict(self):
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"blah": "dir::bloo"})
        simple.update({"blah": "dir::bloo"}, strict=False)

    def test_update_overwrite(self):
        target = pl.Path("aweg")
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"blah": "dir::bloo"})
        simple.update({"blah": "dir::aweg"}, strict=False)
        assert("blah" in simple)
        assert(simple._data["blah"].path == target)
        assert(simple.get('blah') == target)
        result = simple['{blah}']
        assert(result == target.resolve())

    def test_empty_repr(self):
        simple = JGDVLocations(pl.Path.cwd())
        repr_str = repr(simple)
        assert(repr_str == f"<JGDVLocations (1) : {str(pl.Path.cwd())} : ()>")

    def test_non_empty_repr(self):
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah", "b": "dir::aweg", "awegewag": "dir::wejgio"})
        repr_str = repr(simple)
        assert(repr_str == f"<JGDVLocations (1) : {str(pl.Path.cwd())} : (a, b, awegewag)>")

    def test_clear(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "dir::blah"})
        assert("a" in simple)
        simple._clear()
        assert("a" not in simple)

class TestLocationsBasicGet:

    def test_get_none(self):
        """
          loc.get(None) -> None
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        result = simple.get(None)
        assert(result is None)

    def test_get_nonkey(self):
        """
          loc.get(NonDKey(simple)) -> pl.Path(.../simple)
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        key = DKey("simple", implicit=False)
        assert(isinstance(key, NonDKey))
        result = simple.get(key)
        assert(result == pl.Path("simple"))

    def test_get_str(self):
        """
          loc.get('simple') -> pl.Path(.../simple)
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        key = "simple"
        result = simple.get(key)
        assert(result == pl.Path("simple"))

    def test_get_str_key_no_expansion(self):
        """
          loc.get('{simple}') -> pl.Path(.../{simple})
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah", "simple":"dir::bloo"})
        key = "{simple}"
        result = simple.get(key)
        assert(result == pl.Path("{simple}"))

    def test_get_key_direct_expansion(self):
        """
          loc.get(DKey('simple')) => pl.Path(...bloo)
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah", "simple":"dir::bloo"})
        key = DKey("simple")
        result = simple.get(key)
        assert(result == pl.Path("bloo"))

    def test_get_missing(self):
        """
          loc.get(DKey('simple')) => pl.Path(...{simple})
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        key = DKey("simple", implicit=True)
        result = simple.get(key)
        assert(result == pl.Path("{simple}"))

    def test_get_fallback(self):
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        result = simple.get("{b}", pl.Path("bloo"))
        assert(result == pl.Path("bloo"))

    def test_get_raise_error_with_false_fallback(self):
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        with pytest.raises(LocationError):
            simple.get("badkey", False)

class TestLocationsGetItem:

    def test_getitem_str_no_expansion(self):
        """
          loc[a] => pl.Path(.../a)
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        result        = simple.__getitem__("a")
        result_alt    = simple['a']
        assert(result == result_alt)
        assert(isinstance(result, pl.Path))
        assert(result == simple.normalize(pl.Path("a")))

    def test_getitem_str_key_expansion(self):
        """
          loc[{a}] -> pl.Path(.../blah)
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        result = simple.__getitem__("{a}")
        assert(result == simple.normalize(pl.Path("blah")))

    def test_getitem_str_key_no_match_errors(self):
        """
          loc[{b}] -> pl.Path(.../{b})
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        with pytest.raises(LocationError):
            simple.__getitem__("{b}")

    def test_getitem_path_passthrough(self):
        """
          loc[pl.Path(a/b/c)] -> pl.Path(.../a/b/c)
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        result = simple.__getitem__(pl.Path("a/b/c"))
        assert(result == simple.normalize(pl.Path("a/b/c")))

    def test_getitem_path_with_keys(self):
        """
          loc[pl.Path({a}/b/c)] -> pl.Path(.../blah/b/c)
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        result = simple.__getitem__(pl.Path("{a}/b/c"))
        assert(result == simple.normalize(pl.Path("blah/b/c")))

    def test_getitem_fail_with_multikey(self):
        simple = JGDVLocations(pl.Path.cwd()).update({"a": "dir::{other}/blah", "other": "dir::bloo"})
        key = DKey("{a}", ctor=pl.Path)
        with pytest.raises(TypeError):
            simple[key]

    def test_getitem_expansion_item(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "dir::{other}", "other": "dir::bloo"})
        assert(bool(simple._data))

        assert(isinstance(simple['{a}'], pl.Path))
        assert(simple['{a}'] == simple.normalize(pl.Path("bloo")))

    def test_getitem_expansion_multi_recursive(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "dir::{other}", "other": "dir::{aweg}/bloo", "aweg":"dir::aweg/{blah}", "blah":"dir::blah/jojo"})
        assert(bool(simple._data))

        assert(isinstance(simple['{a}'], pl.Path))
        assert(simple['{a}'] == simple.normalize(pl.Path("aweg/blah/jojo/bloo")))

    def test_getitem_expansion_in_item(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"other": "dir::bloo"})
        assert(bool(simple._data))

        assert(isinstance(simple['{other}'], pl.Path))
        assert(simple['{other}'] == simple.normalize(pl.Path("bloo")))

class TestLlocationsGetAttr:

    def test_attr_access_success(self):
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        result = simple.a
        assert(simple.a == pl.Path("blah").absolute())
        assert(isinstance(simple.a, pl.Path))

    def test_attr_access_simple_expansion(self):
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::{other}/blah", "other": "dir::bloo"})
        assert(simple.a == simple.normalize(pl.Path("{other}/blah")))
        assert(isinstance(simple.a, pl.Path))

    def test_attr_expansion_simple(self):
        """
          locs.a => pl.Path(.../{other})
        """
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::{other}", "other": "dir::bloo"})

        assert(isinstance(simple.a, pl.Path))
        assert(simple.a == pl.Path("{other}").absolute())

    def test_attr_access_non_existing_path(self):
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"a": "dir::blah"})
        with pytest.raises(LocationError):
            simple.b

class TestLocationsFails:

    def test_getitem_expansion_missing_key(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"other": "dir::bloo"})
        assert(bool(simple._data))

        with pytest.raises(LocationError):
            simple['{aweg}']

    def test_attr_access_doesnt_expand_subkeys(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "dir::{other}/blah", "other": "dir::{aweg}/bloo/{awog}", "aweg": "dir::first", "awog": "dir::second"})
        assert(bool(simple._data))
        result = simple.a
        assert(result != pl.Path("first/bloo/second/blah").resolve())
        assert(result == pl.Path("{other}/blah").resolve())
        assert(isinstance(simple.a, pl.Path))

    def test_item_access_expansion_recursion_fail(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "dir::{other}/blah", "other": "dir::/bloo/{a}"})
        with pytest.raises(LocationExpansionError):
            simple['{a}']

    def test_get_returns_path(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "dir::blah"})
        assert(bool(simple._data))

        assert(isinstance(simple.get("b", pl.Path("bloo")), pl.Path))

class TestLocationsUtils:

    def test_normalize(self):
        simple = JGDVLocations(pl.Path.cwd())
        a_path = pl.Path("a/b/c")
        expected = a_path.absolute()
        result = simple.normalize(a_path)
        assert(result == expected)

    def test_normalize_tilde(self):
        simple = JGDVLocations(pl.Path.cwd())
        result = simple.normalize(pl.Path("~/blah"))
        assert(result.is_absolute())
        assert(result == pl.Path("~/blah").expanduser())

    def test_normalize_absolute(self):
        simple = JGDVLocations(pl.Path.cwd())
        result = simple.normalize(pl.Path("/blah"))
        assert(result.is_absolute())
        assert(result == pl.Path("/blah"))

    def test_normalize_relative(self):
        simple = JGDVLocations(pl.Path.cwd())
        result = simple.normalize(pl.Path("blah"))
        assert(result.is_absolute())
        assert(result == (pl.Path.cwd() / "blah").absolute())

    def test_normalize_relative_with_different_cwd(self):
        simple = JGDVLocations(pl.Path("~/desktop/"))
        result = simple.normalize(pl.Path("blah"))
        assert(result.is_absolute())
        assert(result == (pl.Path("~/desktop/") / "blah").expanduser().absolute())

class TestLocationsGlobal:

    def test_sanity(self):
        assert(True is not False)

    def test_global_Current(self):
        locs = JGDVLocations(pl.Path.cwd())
        assert(isinstance(JGDVLocations.Current, JGDVLocations))

    def test_ctx_manager_basic(self):
        assert(JGDVLocations.Current is initial_loc)
        with JGDVLocations.Current() as locs2:
            assert(JGDVLocations.Current is locs2)

        assert(JGDVLocations.Current is initial_loc)

    def test_ctx_manager_cwd_change(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(not bool(simple._data))
        simple.update({"a": "dir::blah"})
        assert(bool(simple._data))
        assert(simple.a == pl.Path("blah").resolve())

        with simple(pl.Path("~/Desktop")) as ctx:
            assert(ctx.a == pl.Path("~/Desktop/blah").expanduser().resolve())

    def test_stacklen(self):
        assert(_LocationsGlobal.stacklen() == 1)
        locs  = JGDVLocations(pl.Path.cwd())
        assert(_LocationsGlobal.stacklen() == 1)
        with locs() as locs2:
            assert(_LocationsGlobal.stacklen() == 2)
            with locs2() as locs3:
                assert(_LocationsGlobal.stacklen() == 3)

            assert(_LocationsGlobal.stacklen() == 2)

        assert(_LocationsGlobal.stacklen() == 1)
        assert(JGDVLocations.Current is initial_loc)
