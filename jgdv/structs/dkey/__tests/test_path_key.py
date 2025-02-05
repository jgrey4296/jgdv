#!/usr/bin/env python4
"""

"""
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast, Self, Final)
import warnings

import pytest


from jgdv.structs.strang.errors import DirAbsent, LocationExpansionError, LocationError
from jgdv._abstract.protocols import Key_p
from jgdv.structs.dkey import DKey
from jgdv.structs.dkey.path_key import PathDKey
from jgdv.structs.strang.locations import JGDVLocations, _LocationsGlobal

logging = logmod.root

IMP_KEY_BASES               : Final[list[str]]           = ["bob", "bill", "blah", "other", "23boo", "aweg2531", "awe_weg", "aweg-weji-joi"]
EXP_KEY_BASES               : Final[list[str]]           = [f"{{{x}}}" for x in IMP_KEY_BASES]
EXP_P_KEY_BASES             : Final[list[str]]           = ["{bob:wd}", "{bill:w}", "{blah:wi}", "{other:i}"]
PATH_KEYS                   : Final[list[str]]           = ["{bob}/{bill}", "{blah}/{bloo}", "{blah}/{bloo}"]
MUTI_KEYS                   : Final[list[str]]           = ["{bob}_{bill}", "{blah} <> {bloo}", "! {blah}! {bloo}!"]
IMP_IND_KEYS                : Final[list[str]]           = ["bob_", "bill_", "blah_", "other_"]
EXP_IND_KEYS                : Final[list[str]]           = [f"{{{x}}}" for x in IMP_IND_KEYS]

VALID_KEYS                                           = IMP_KEY_BASES + EXP_KEY_BASES + EXP_P_KEY_BASES + IMP_IND_KEYS + EXP_IND_KEYS
VALID_MULTI_KEYS                                     = PATH_KEYS + MUTI_KEYS

match JGDVLocations.Current:
    case None:
        initial_loc = JGDVLocations(pl.Path.cwd())
    case x:
        initial_loc = x

@pytest.fixture(scope="function")
def simple() -> JGDVLocations:
    return JGDVLocations(pl.Path.cwd())

class TestPathKey:

    def test_mark(self):
        assert(DKey.MarkOf(PathDKey) is DKey.mark.PATH)

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
