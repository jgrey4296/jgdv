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

from jgdv.structs.dkey import DKey
from jgdv.structs.strang import Strang, StrangError
from jgdv.structs.locator import JGDVLocator, Location

logging = logmod.root

class TestLocation:

    def test_sanity(self):
        assert(True is not False)

    def test_simple_dir(self):
        loc = Location("dir::>test/path")
        assert(loc is not None)
        assert(isinstance(loc, Strang))
        assert(isinstance(loc, Location))
        assert(isinstance(loc, str))

    def test_simple_file(self):
        loc = Location("file::>test/path.py")
        assert(loc is not None)
        assert(isinstance(loc, Strang))
        assert(isinstance(loc, Location))
        assert(isinstance(loc, str))
        assert(Location.Marks.file in loc)

    def test_file_stem(self):
        loc = Location("file::>test/path.py")
        assert(loc.path.stem == "path")
        assert(loc.stem == "path")

    def test_file_ext(self):
        loc = Location("file::>test/path.py")
        assert(loc.ext() == ".py")

    def test_file_multi_ext(self):
        loc = Location("file::>test/path.py.bl.gz")
        assert(loc.ext() == ".py.bl.gz")

    def test_multi_ext_last(self):
        loc = Location("file::>test/path.py.bl.gz")
        assert(loc.ext(last=True) == ".gz")
        assert(loc.ext(last=False) == ".py.bl.gz")

    def test_bad_form_fail(self):
        # with pytest.raises(StrangError):
        #     Location("bad::test/path.py")
        val = Location("bad::test/path.py")

    def test_file_with_metadata(self):
        loc = Location("file/clean::>test/path.py")
        assert(isinstance(loc, Location))
        assert(Location.gmark_e.file in loc._group_meta)
        assert(Location.gmark_e.clean in loc._group_meta)
        assert(Location.gmark_e.abstract not in loc._group_meta)

    def test_glob_path(self):
        loc = Location("file::>test/*/path.py")
        assert(isinstance(loc, Location))
        assert(Location.gmark_e.abstract in loc._group_meta)
        assert(not loc.is_concrete())
        assert(loc[1:1] is loc.bmark_e.glob)

    def test_rec_glob_path(self):
        loc = Location("file::>test/**/path.py")
        assert(isinstance(loc, Location))
        assert(Location.gmark_e.abstract in loc._group_meta)
        assert(not loc.is_concrete())
        assert(loc[1:1] is loc.bmark_e.rec_glob)

    def test_select_path(self):
        loc = Location("file::>test/?/path.py")
        assert(isinstance(loc, Location))
        assert(Location.gmark_e.abstract in loc._group_meta)
        assert(not loc.is_concrete())
        assert(loc[1:1] is loc.bmark_e.select)

    def test_glob_stem(self):
        loc = Location("file::>test/blah/*ing.py")
        assert(isinstance(loc, Location))
        assert(Location.gmark_e.abstract in loc._group_meta)
        assert(not loc.is_concrete())
        assert(loc.stem == (loc.bmark_e.glob, "*ing"))

    def test_select_stem(self):
        loc = Location("file::>test/blah/?ing.py")
        assert(isinstance(loc, Location))
        assert(Location.gmark_e.abstract in loc._group_meta)
        assert(not loc.is_concrete())
        assert(loc.stem == (loc.bmark_e.select, "?ing"))

    def test_earlycwd_expansion(self):
        loc = Location("file/earlycwd::>a/b/c.py")
        assert(loc[1:] == "a/b/c.py")
        assert(loc.path == pl.Path("a/b/c.py"))

    def test_earlycwd_expansion_uses_initial_cwd(self):
        loc = Location("file/earlycwd::>a/b/c.py")
        orig_cwd = pl.Path.cwd()
        sub_cwd = [x for x in orig_cwd.iterdir() if not x.is_file()][0]
        with JGDVLocator(sub_cwd) as loclookup:
            assert(pl.Path.cwd() != orig_cwd)
            assert(pl.Path.cwd() == sub_cwd)
            expanded = loclookup.normalize(loc)
            assert(expanded.is_absolute())
            assert(not expanded.is_relative_to(sub_cwd))

class TestLocation_Definite:

    def test_definite(self):
        basic = Location(pl.Path("a/b/c"))
        assert(basic.is_concrete())

    def test_definite_contained_in_indefinite(self):
        definite = Location("a/b/c.py")
        indef    = Location("a/b/*.py")
        assert(definite in indef)

class TestLocation_Indefinite:

    def test_indef_stem_not_concrete(self):
        basic = Location(pl.Path("a/b/*.py"))
        assert(not basic.is_concrete())

    def test_indef_ext_not_concrete(self):
        basic = Location(pl.Path("a/b/c.*"))
        assert(basic.ext() == (Location.bmark_e.glob, ".*"))
        assert(not basic.is_concrete())

    def test_indef_path_not_concrete(self):
        basic = Location(pl.Path("a/*/c.py"))
        assert(basic.bmark_e.glob in basic.body())
        assert(not basic.is_concrete())

    def test_indef_path_not_concrete_2(self):
        basic = Location(pl.Path("a/**/c.py"))
        assert(basic.bmark_e.rec_glob in basic.body())
        assert(not basic.is_concrete())

    def test_indef_suffix_contains_definite(self):
        definite = Location(pl.Path("a/b/c.py"))
        indef    = Location(pl.Path("a/b/c.*"))
        assert(indef.ext() == (indef.bmark_e.glob, ".*"))
        assert(definite in indef)

    def test_indef_suffix_contain_fail(self):
        definite = Location(pl.Path("a/b/d.py"))
        indef    = Location(pl.Path("a/b/c.*"))
        assert(definite not in indef)

    def test_indef_path_contains(self):
        definite = Location(pl.Path("a/b/c.py"))
        indef    = Location(pl.Path("a/*/c.py"))
        assert(definite in indef)

    def test_indef_path_contain_fail(self):
        definite = Location(pl.Path("a/b/d/c.py"))
        indef    = Location(pl.Path("a/*/e/c.py"))
        assert(indef not in definite)

    def test_indef_stem_contains_definite(self):
        definite = Location(pl.Path("a/b/c.py"))
        indef    = Location(pl.Path("a/b/*.py"))
        assert(definite in indef)

    def test_indef_stem_contains_fail(self):
        definite = Location(pl.Path("a/b/c.bib"))
        indef    = Location(pl.Path("a/b/*.py"))
        assert(definite not in indef)

    def test_indef_recursive_contains(self):
        definite = Location(pl.Path("a/b/d/c.py"))
        indef    = Location(pl.Path("a/**/c.py"))
        assert(definite in indef)

    def test_indef_recursive_contain_fail(self):
        definite = Location(pl.Path("b/b/c.py"))
        indef    = Location(pl.Path("a/**/c.py"))
        assert(definite not in indef)

    def test_indef_multi_recursive_contains(self):
        definite = Location(pl.Path("a/b/d/e/f/c.py"))
        indef    = Location(pl.Path("a/**/c.py"))
        assert(definite in indef)

    def test_indef_root_recursive_contains(self):
        definite = Location(pl.Path("a/b/d/e/f/c.py"))
        indef    = Location(pl.Path("**/c.py"))
        assert(definite in indef)

    def test_indef_multi_component_contains(self):
        definite = Location(pl.Path("a/b/d/e/f/c.py"))
        indef    = Location(pl.Path("**/*.*"))
        assert(definite in indef)
