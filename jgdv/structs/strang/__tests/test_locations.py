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

from jgdv.structs.strang.errors import DirAbsent, LocationExpansionError, LocationError
from jgdv.structs.strang.locations import JGDVLocations, _LocationsGlobal
from jgdv.structs.strang.location import Location
from jgdv.structs.dkey import DKey, NonDKey

logging = logmod.root

match JGDVLocations.Current:
    case None:
        initial_loc = JGDVLocations(pl.Path.cwd())
    case x:
        initial_loc = x

@pytest.fixture(scope="function")
def simple() -> JGDVLocations:
    return JGDVLocations(pl.Path.cwd())

class TestLocations:

    def test_initial(self):
        simple = JGDVLocations(pl.Path.cwd())
        assert(isinstance(simple, JGDVLocations))
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
        simple = JGDVLocations(pl.Path.cwd())
        simple.update({"blah": "dirr::bloo"})
        simple.update({"blah": "dir::>aweg"}, strict=False)
        assert("blah" in simple)
        assert(simple._data["blah"] == locstr)
        assert(simple.access('blah') == locstr)

    def test_empty_repr(self, simple):
        repr_str = repr(simple)
        assert(repr_str == f"<JGDVLocations (1) : {str(pl.Path.cwd())} : ()>")

    def test_non_empty_repr(self, simple):
        simple.update({"a": "dir::>blah", "b": "dir::>aweg", "awegewag": "dir::>jkwejgio"})
        repr_str = repr(simple)
        assert(repr_str == f"<JGDVLocations (1) : {str(pl.Path.cwd())} : (a, b, awegewag)>")

    def test_clear(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "dir::>blah"})
        assert("a" in simple)
        simple._clear()
        assert("a" not in simple)

class TestLocationsAccessLocation:

    def test_get_none(self, simple):
        """
          loc.access(None) -> None
        """
        simple.update({"a": "dir::>blah"})
        result = simple.access(None)
        assert(result is None)

    def test_get_nonkey(self, simple):
        """
          loc.access(NonDKey(simple)) -> pl.Path(.../simple)
        """
        simple.update({"a": "dir::>blah"})
        key = DKey("simple", implicit=False)
        assert(isinstance(key, NonDKey))
        assert(simple.access(key) is None)

    def test_get_no_entry_str(self, simple):
        """
          loc.access('simple') -> pl.Path(.../simple)
        """
        simple.update({"a": "dir::>blah"})
        key = "simple"
        assert(simple.access(key) is None)

    def test_get_entry_str(self, simple):
        """
          loc.access('simple') -> pl.Path(.../simple)
        """
        simple.update({"a": "dir::>blah"})
        key = "a"
        assert(simple.access(key) is not None)

    def test_get_fmtstr(self, simple):
        """
          loc.access('{simple}') -> pl.Path(.../{simple})
        """
        simple.update({"a": "dir::>blah", "simple":"dir::>bloo"})
        key = "{simple}"
        assert(simple.access(key) == None)

    def test_get_key_entry(self, simple):
        """
          loc.access(DKey('simple')) => pl.Path(...bloo)
        """
        simple.update({"a": "dir::>blah", "simple":"dir::>bloo"})
        key = DKey("simple")
        assert(simple.access(key) is not None)

    def test_get_missing(self, simple):
        """
          loc.access(DKey('simple')) => pl.Path(...{simple})
        """
        simple.update({"a": "dir::>blah"})
        key = DKey("simple", implicit=True)
        assert(simple.access(key) is None)

    def test_get_fallback(self, simple):
        simple.update({"a": "dir::>blah"})
        result = simple.access("{b}", "a")
        assert(result == "dir::>blah")

    def test_get_raise_error_with_false_fallback(self, simple):
        simple.update({"a": "dir::>blah"})
        with pytest.raises(KeyError):
            simple.access("badkey", False)

class TestLocationsExpandLocation:

    def test_expand_str_no_expansion(self, simple):
        """
          loc[b] => pl.Path(.../b)
        """
        simple.update({"a": "dir::>blah"})
        result        = simple.expand("b")
        assert(isinstance(result, pl.Path))
        assert(result == simple.normalize(pl.Path("b")))

    def test_expand_str_matching_loc(self, simple):
        """
          loc[a] => pl.Path(.../a)
        """
        simple.update({"a": "dir::>blah"})
        result        = simple.expand("a")
        assert(isinstance(result, pl.Path))
        assert(result == simple.normalize(pl.Path("a")))

    def test_expand_dkey(self, simple):
        """
          loc[a] => pl.Path(.../a)
        """
        simple.update({"a": "dir::>blah"})
        the_key = DKey("{a}")
        result        = simple.expand(the_key)
        assert(isinstance(result, pl.Path))
        assert(result == simple.normalize(pl.Path("blah")))

    def test_expand_fmtstr(self, simple):
        """
          loc[{a}] -> pl.Path(.../blah)
        """
        simple.update({"a": "dir::>blah"})
        result = simple.expand("{a}")
        assert(result == simple.normalize(pl.Path("blah")))

    def test_expand_fmtstr_fail(self, simple):
        """
          loc[{b}] -> pl.Path(.../{b})
        """
        simple.update({"a": "dir::>blah"})
        with pytest.raises(KeyError):
            simple.expand("{b}")

    def test_expand_path_passthrough(self, simple):
        """
          loc[pl.Path(a/b/c)] -> pl.Path(.../a/b/c)
        """
        simple.update({"a": "dir::>blah"})
        result = simple.expand(pl.Path("a/b/c"))
        assert(result == simple.normalize(pl.Path("a/b/c")))

    def test_expand_path_with_keys(self, simple):
        """
          loc[pl.Path({a}/b/c)] -> pl.Path(.../blah/b/c)
        """
        simple.update({"a": "dir::>blah"})
        result = simple.expand(pl.Path("{a}/b/c"))
        assert(result == simple.normalize(pl.Path("blah/b/c")))

    def test_expand_multikey(self, simple):
        simple.update({"a": "dir::>base/blah", "b": "dir::>bloo"})
        key = DKey("{a}/{b}", ctor=pl.Path)
        result = simple.expand(key)
        assert(result == simple.normalize(pl.Path("base/blah/bloo")))

    def test_expand_trailing_slash(self):
        simple = JGDVLocations(pl.Path.cwd()).update({"a": "dir::>base/blah/", "b": "dir::>bloo"})
        key = DKey("{a}/{b}", ctor=pl.Path)
        result = simple.expand(key)
        assert(result == simple.normalize(pl.Path("base/blah/bloo")))

    @pytest.mark.xfail
    def test_expand_prefix_slash_not_root_fail(self):
        """ Error if trying to use a path that has a root, as a not-root
        Eg: a/b/c + /d/e
        or: a/b/c + ~/d/e
        """
        simple = JGDVLocations(pl.Path.cwd()).update({"a": "dir::>base/blah", "b": "dir::>/bloo"})
        key = DKey("{a}/{b}", ctor=pl.Path)
        with pytest.raises(LocationExpansionError):
            simple.expand(key)

    def test_expand_prefix_slash_when_root(self):
        """
        Eg: /a/b/c/ + d/e = /a/b/c/d/e
        """
        simple = JGDVLocations(pl.Path.cwd()).update({"a": "dir::>/base/blah", "b": "dir::>bloo"})
        key = DKey("{a}/{b}", ctor=pl.Path)
        assert(simple.expand(key) == pl.Path("/base/blah/bloo"))

    def test_expand_with_multikey(self):
        simple = JGDVLocations(pl.Path.cwd()).update({"a": "dir::>{other}/blah", "other": "dir::>bloo"})
        key = DKey("{a}", ctor=pl.Path)
        result = simple[key]
        assert(result == simple.normalize(pl.Path("bloo/blah")))

    def test_expand_subkey(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "dir::>{other}/aweg", "other": "dir::>bloo"})
        assert(simple.expand("{a}") == simple.normalize(pl.Path("bloo/aweg")))

    def test_expand_rec_subkey(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "dir::>{other}/aweg",
                       "other": "dir::>bloo/{blah}",
                       "blah":"qqqq"})
        assert(simple.expand("{a}") == simple.normalize(pl.Path("bloo/qqqq/aweg")))

    def test_expand_expansion_multi_recursive(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "dir::>{other}",
                       "other": "dir::>{aweg}/bloo",
                       "aweg":"dir::>aweg/{blah}",
                       "blah":"dir::>blah/jojo"})
        assert(bool(simple._data))

        assert(isinstance(simple['{a}'], pl.Path))
        assert(simple['{a}'] == simple.normalize(pl.Path("aweg/blah/jojo/bloo")))

    def test_expand_expansion_in_item(self, simple):
        assert(not bool(simple._data))
        simple.update({"other": "dir::>bloo"})
        assert(bool(simple._data))

        assert(isinstance(simple['{other}'], pl.Path))
        assert(simple['{other}'] == simple.normalize(pl.Path("bloo")))

class TestLlocationsGetAttr:

    def test_attr_access_success(self, simple):
        simple.update({"a": "dir::>blah"})
        result = simple.a
        assert(simple.a == "dir::>blah")
        assert(isinstance(simple.a, Location))

    def test_attr_access_no_expansion(self, simple):
        simple.update({"a": "dir::>{other}/blah", "other": "dir::>bloo"})
        assert(simple.a == "dir::>{other}/blah")
        assert(isinstance(simple.a, Location))

    def test_attr_access_non_existing_loc(self, simple):
        simple.update({"a": "dir::>blah"})
        with pytest.raises(AttributeError):
            simple.b

class TestLocationsFails:

    def test_getitem_expansion_missing_key(self, simple):
        assert(not bool(simple._data))
        simple.update({"other": "dir::>bloo"})
        assert(bool(simple._data))

        assert(simple.expand('{aweg}', strict=False) == simple.normalize(pl.Path("{aweg}")))

    def test_item_access_expansion_recursion_fail(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "dir::>{other}/blah", "other": "dir::>/bloo/{a}"})
        with pytest.raises(RecursionError):
            simple['{a}']

class TestLocationsUtils:

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
        simple = JGDVLocations(pl.Path("~/desktop/"))
        result = simple.normalize(pl.Path("blah"))
        assert(result.is_absolute())
        assert(result == (pl.Path("~/desktop/") / "blah").expanduser().absolute())

class TestLocationsGlobal:

    def test_sanity(self, simple):
        assert(True is not False)

    def test_global_Current(self, simple):
        locs = JGDVLocations(pl.Path.cwd())
        assert(isinstance(JGDVLocations.Current, JGDVLocations))

    def test_ctx_manager_basic(self, simple):
        assert(JGDVLocations.Current is initial_loc)
        with JGDVLocations.Current() as locs2:
            assert(JGDVLocations.Current is locs2)

        assert(JGDVLocations.Current is initial_loc)

    def test_ctx_manager_cwd_change(self, simple):
        assert(not bool(simple._data))
        simple.update({"a": "dir::>blah"})
        assert(bool(simple._data))
        assert(simple['{a}'] == pl.Path("blah").resolve())

        with simple(pl.Path("~/Desktop")) as ctx:
            assert(ctx['{a}'] == pl.Path("~/Desktop/blah").expanduser().resolve())

    def test_stacklen(self, simple):
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

class TestLocationsMixins:

    def test_sanity(self, simple):
        assert(True is not False) # noqa: PLR0133

    @pytest.mark.parametrize("key", ["blah", pl.Path("blah"), DKey("blah"), Location("blah")])
    def test_simple_coercions(self, key):
        locs = JGDVLocations(pl.Path.cwd())
        assert(isinstance(locs._coerce_key(key), str))

    def test_getattr_missing(self, simple):
        locs = JGDVLocations(pl.Path.cwd())
        with pytest.raises(AttributeError):
            locs.blah

    def test_expand_key_stack(self, simple):
        simple.update({"a":"blah"})
        assert(simple._expand_key("{a}") == "blah")

    def test_expand_key_stack_multi(self, simple):
        simple.update({"a":"blah", "b":"bloo"})
        assert(simple._expand_key("{a}/{b}") == "blah/bloo")

    def test_expand_key_stack_recursive(self, simple):
        simple.update({"a":"blah/{c}", "b":"bloo", "c":"aweg"})
        assert(simple._expand_key("{a}/{b}") == "blah/aweg/bloo")

    def test_extended_expand(self, simple):
        simple.update({"a":"blah/{c}",
                       "b":"bloo/{d}/aw/{e}",
                       "c":"aweg/{d}",
                       "d": "qqq/{e}",
                       "e": "www",
                       })
        target = "".join([
            # a = blah/ c
            "blah/",
            # c = aweg/ d
            "aweg/",
            # d = qqq/ e
            "qqq/",
            # e = www/
            "www/",
            # c
            "aweg/", "qqq/", "www/",
            # b = bloo / d /aw/ e
            "bloo/",
            # d
            "qqq/", "www/",
            # e
            "aw/", "www/",
            # d
            "qqq/", "www"

            ])
        assert(simple._expand_key("{a}/{c}/{b}/{d}") == target)
