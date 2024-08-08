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

logging = logmod.root

from jgdv.files.tags.base import TagFile
from jgdv.files.tags.substitutions import SubstitutionFile

class TestSubFile:

    def test_initial(self):
        obj = SubstitutionFile()
        assert(obj is not None)

    def test_len(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(len(obj) == 3)

    def test_sub_default(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(obj.sub("a") == {"a"})

    def test_sub_norms(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(obj.sub("a tag") == {"a_tag"})
        assert(obj.sub("a_tag") == {"a_tag"})

    def test_update_just_count(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(obj.get_count("b") == 5)
        obj.update("b")
        assert(obj.get_count("b") == 6)

    def test_update_subs(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(obj.sub("a_tag") == {"a_tag"})
        obj.update(("a tag", 1, "blah"))
        assert(obj.sub("a_tag") == {"blah"})


    def test_contains(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert("a tag" in obj)
        assert("a_tag" in obj)


    def test_contains_subs(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert("a tag" in obj)
        assert("a_tag" in obj)
        obj.update(("a tag", 1, "blah"))
        assert("blah" in obj)


    def test_subs_dont_have_subs(self):
        obj = SubstitutionFile(count={"a": 2, "b": 5, "a tag": 19})
        obj.update(("a tag", 1, "blah"))
        assert("blah" in obj)
        assert(not obj.has_sub("blah"))


    def test_has_sub_false(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(not obj.has_sub("a"))
        assert(not obj.has_sub("a_tag"))

    def test_has_sub_on_norm(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(obj.has_sub("a tag"))
        assert(not obj.has_sub("a_tag"))

    def test_has_sub_true(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(not obj.has_sub("a_tag"))
        obj.update(("a_tag", 1, "blah"))
        assert(obj.has_sub("a tag"))


    def test_update_multi_sub(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        assert(not obj.has_sub("a_tag"))
        obj.update(("a_tag", 1, "blah", "bloo"))
        assert(obj.sub("a_tag") == {"blah", "bloo"})


    def test_canonical(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        obj.update(("a_tag", 1, "blah", "bloo"))
        canon = obj.canonical()
        assert(isinstance(canon, TagFile))
        assert("a" in canon)
        assert("b" in canon)
        assert("blah" in canon)
        assert("bloo" in canon)


    def test_canonical_filters_presubs(self):
        obj = SubstitutionFile(counts={"a": 2, "b": 5, "a tag": 19})
        obj.update(("a_tag", 1, "blah", "bloo"), ("bloo", 1, "aweg"))
        canon = obj.canonical()
        assert(isinstance(canon, TagFile))
        assert("a_tag" not in canon)
        assert("bloo" not in canon)
        assert("aweg" in canon)

