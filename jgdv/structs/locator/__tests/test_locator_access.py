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

class TestLocatorGet:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

class TestLocatorAccess:

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

class TestLocatorExpand:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

class TestLocatorGetAttr:

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

class TestLocatorGetItem:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

class TestLocatorFails:

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

class TestLocatorMixins:

    def test_sanity(self, simple):
        assert(True is not False) # noqa: PLR0133

    @pytest.mark.parametrize("key", ["blah", pl.Path("blah"), DKey("blah"), Location("blah")])
    def test_simple_coercions(self, key):
        locs = JGDVLocator(pl.Path.cwd())
        assert(isinstance(locs._coerce_key(key), str))

    def test_getattr_missing(self, simple):
        locs = JGDVLocator(pl.Path.cwd())
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
