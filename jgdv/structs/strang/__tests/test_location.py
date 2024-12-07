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
from jgdv.structs.strang import Strang
from jgdv.structs.strang.location import Location
from jgdv.structs.strang.locations import JGDVLocations

logging = logmod.root

class TestLocation:

    def test_sanity(self):
        assert(True is not False)

    def test_simple_dir(self):
        loc = Location("dir::test/path")
        assert(loc is not None)
        assert(isinstance(loc, Strang))
        assert(isinstance(loc, Location))

    def test_simple_file(self):
        loc = Location("file::test/path.py")
        assert(loc is not None)
        assert(isinstance(loc, Strang))
        assert(isinstance(loc, Location))
        assert(Location.mark_e.file in loc)

    def test_file_stem(self):
        loc = Location("file::test/path.py")
        assert(loc.stem == "path")

    def test_file_ext(self):
        loc = Location("file::test/path.py")
        assert(loc.ext() == ".py")

    def test_file_multi_ext(self):
        loc = Location("file::test/path.py.bl.gz")
        assert(loc.ext() == ".py.bl.gz")

    def test_multi_ext_last(self):
        loc = Location("file::test/path.py.bl.gz")
        assert(loc.ext(last=True) == ".gz")
        assert(loc.ext(last=False) == ".py.bl.gz")

    def test_bad_form_fail(self):
        with pytest.raises(KeyError):
            Location("bad::test/path.py")

    def test_file_with_metadata(self):
        loc = Location("file/clean::test/path.py")
        assert(isinstance(loc, Location))
        assert(Location.mark_e.file in loc._group_objs)
        assert(Location.mark_e.clean in loc._group_objs)
        assert(Location.mark_e.abstract not in loc._group_objs)

    def test_glob_path(self):
        loc = Location("file::test/*/path.py")
        assert(isinstance(loc, Location))
        assert(Location.mark_e.abstract in loc._group_objs)
        assert(not loc.is_concrete())
        assert(loc[1:1] is loc.wild_e.glob)

    def test_rec_glob_path(self):
        loc = Location("file::test/**/path.py")
        assert(isinstance(loc, Location))
        assert(Location.mark_e.abstract in loc._group_objs)
        assert(not loc.is_concrete())
        assert(loc[1:1] is loc.wild_e.rec_glob)

    def test_select_path(self):
        loc = Location("file::test/?/path.py")
        assert(isinstance(loc, Location))
        assert(Location.mark_e.abstract in loc._group_objs)
        assert(not loc.is_concrete())
        assert(loc[1:1] is loc.wild_e.select)

    def test_glob_stem(self):
        loc = Location("file::test/blah/*ing.py")
        assert(isinstance(loc, Location))
        assert(Location.mark_e.abstract in loc._group_objs)
        assert(not loc.is_concrete())
        assert(loc.stem == (loc.wild_e.glob, "*ing"))

    def test_select_stem(self):
        loc = Location("file::test/blah/?ing.py")
        assert(isinstance(loc, Location))
        assert(Location.mark_e.abstract in loc._group_objs)
        assert(not loc.is_concrete())
        assert(loc.stem == (loc.wild_e.select, "?ing"))

    def test_earlycwd_expansion(self):
        loc = Location("file/earlycwd::a/b/c.py")
        assert(loc[1:] == "a/b/c.py")
        assert(loc.path == pl.Path("a/b/c.py"))

    def test_earlycwd_expansion_uses_initial_cwd(self):
        loc = Location("file/earlycwd::a/b/c.py")
        orig_cwd = pl.Path.cwd()
        sub_cwd = [x for x in orig_cwd.iterdir() if not x.is_file()][0] 
        with JGDVLocations(sub_cwd) as loclookup:
            assert(pl.Path.cwd() != orig_cwd)
            assert(pl.Path.cwd() == sub_cwd)
            expanded = loclookup.normalize(loc)
            assert(expanded.is_absolute())
            assert(not expanded.is_relative_to(sub_cwd))

