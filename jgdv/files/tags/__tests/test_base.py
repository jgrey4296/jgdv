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

class TestTagFile:

    def test_initial(self):
        obj = TagFile()
        assert(obj is not None)

    @pytest.mark.parametrize("tag,exp", [("tag", "tag"), ("a tag", "a_tag"), ("A Tag", "A_Tag")])
    def test_norm_tag(self, tag, exp):
        obj = TagFile()
        normed = obj.norm_tag(tag)
        assert(normed == exp)

    def test_empty(self):
        obj = TagFile()
        assert(not bool(obj))

    def test_non_empty(self):
        obj = TagFile(counts={"blah": 1})
        assert(bool(obj))

    def test_len(self):
        obj = TagFile(counts={"blah": 1})
        assert(len(obj) == 1)

    def test_len_2(self):
        obj = TagFile(counts={"blah": 1, "bloo": 3})
        assert(len(obj) == 2)

    def test_contains(self):
        obj = TagFile(counts={"blah": 1})
        assert("blah" in obj)

    def test_contains_fail(self):
        obj = TagFile(counts={"blah": 1})
        assert("bloo" not in obj)

    def test_contains_norms(self):
        obj = TagFile(counts={"a blah": 1, "a_bloo":5})
        assert("a blah" in obj)
        assert("a_blah" in obj)
        assert("a_bloo" in obj)
        assert("a bloo" in obj)

    def test_update_str(self):
        obj = TagFile()
        assert(not bool(obj))
        assert("bloo" not in obj)
        obj.update("bloo")
        assert(bool(obj))
        assert("bloo" in obj)

    def test_update_list(self):
        obj = TagFile()
        assert(not bool(obj))
        assert("bloo" not in obj)
        obj.update(["bloo", "blee"])
        assert(bool(obj))
        assert("bloo" in obj)

    def test_update_set(self):
        obj = TagFile()
        assert(not bool(obj))
        obj.update({"bloo", "blah", "blee"})
        assert(bool(obj))
        assert("bloo" in obj)
        assert("blah" in obj)
        assert("blee" in obj)

    def test_update_str_multi(self):
        obj = TagFile()
        assert(not bool(obj))
        assert("bloo" not in obj)
        obj.update("bloo", "blah")
        assert(bool(obj))
        assert("bloo" in obj)
        assert("blah" in obj)

    def test_update_dict(self):
        obj = TagFile()
        assert(not bool(obj))
        obj.update({"bloo":1, "blah":3, "blee":5})
        assert(bool(obj))
        assert("bloo" in obj)
        assert("blah" in obj)
        assert("blee" in obj)

    def test_update_tagfile(self):
        obj = TagFile()
        obj2 = TagFile(counts={"blah":1, "bloo":1, "blee":1})
        assert(not bool(obj))
        obj.update(obj2)
        assert(bool(obj))
        assert("bloo" in obj)
        assert("blah" in obj)
        assert("blee" in obj)

    def test_to_set(self):
        obj = TagFile(counts={"blah":1, "bloo":1, "blee":1})
        as_set = obj.to_set()
        assert(isinstance(as_set, set))
        assert(len(as_set) == 3)

    def test_get_count(self):
        obj = TagFile(counts={"blah":1, "bloo":5, "blee":1})
        assert(obj.get_count("blah") == 1)

    def test_get_count_2(self):
        obj = TagFile(counts={"blah":1, "bloo":5, "blee":1})
        assert(obj.get_count("bloo") == 5)

    def test_get_count_missing(self):
        obj = TagFile(counts={"blah":1, "bloo":5, "blee":1})
        assert(obj.get_count("aweg") == 0)

    def test_count_inc(self):
        obj = TagFile(counts={"blah":1, "bloo":5, "blee":1})
        assert(obj.get_count("bloo") == 5)
        obj.update("bloo")
        assert(obj.get_count("bloo") == 6)

    def test_str(self):
        obj = TagFile(counts={"blah":1, "bloo":5, "blee":1, "aweg": 0})
        assert(str(obj) == "\n".join(["blah : 1", "blee : 1", "bloo : 5"]))

