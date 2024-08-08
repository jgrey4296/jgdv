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
import doot
doot._test_setup()
from doot._structs.str_struct_name import StrStruct, TaskName

logging = logmod.root

class TestStrStruct:

    @pytest.fixture(scope="function")
    def setup(self):
        pass

    @pytest.fixture(scope="function")
    def cleanup(self):
        pass

    def test_initial(self):
        obj = StrStruct("test::blah", sep="::")
        assert(isinstance(obj, StrStruct))
        assert(isinstance(obj, str))
        assert(obj == "test::blah")
        assert(obj._sep == "::")
        assert(obj.head == ["test"])
        assert(obj.tail == ["blah"])

    def test_with_simple_params(self):
        obj = StrStruct("test::blah::[1,2,3]", sep="::")
        assert(isinstance(obj, StrStruct))
        assert(isinstance(obj, str))
        assert(obj == "test::blah::[1,2,3]")
        assert(obj._sep == "::")
        assert(obj.head == ["test"])
        assert(obj.tail == ["blah"])

    def test_fail_build(self):
        with pytest.raises(ValueError):
            StrStruct("test>blah", sep="::")

    def test_hash(self):
        obj = StrStruct("test::blah")
        assert(isinstance(obj, StrStruct))
        assert(hash(obj) == hash("test::blah"))

    def test_head_str(self):
        obj = StrStruct("test.bloo::blah.aweg")
        assert(isinstance(obj, StrStruct))
        assert(obj.head_str() == "test.bloo")

    def test_tail_str(self):
        obj = StrStruct("test.bloo::blah.aweg")
        assert(isinstance(obj, StrStruct))
        assert(obj.tail_str() == "blah.aweg")

    def test_lt(self):
        obj = StrStruct("test.bloo::blah.aweg")
        assert(isinstance(obj, StrStruct))
        assert(obj < "test.bloo::blah.aweg.aweg")

    def test_le(self):
        obj = StrStruct("test.bloo::blah.aweg")
        assert(isinstance(obj, StrStruct))
        assert(obj <= "test.bloo::blah.aweg")

    def test_format_dunder_head(self):
        obj = StrStruct("test.bloo::blah.aweg")
        assert(isinstance(obj, StrStruct))
        assert(f"{obj:h}" == "test.bloo")

    def test_format_dunder_tail(self):
        obj = StrStruct("test.bloo::blah.aweg")
        assert(isinstance(obj, StrStruct))
        assert(f"{obj:t}" == "blah.aweg")

    def test_format_dunder_params(self):
        obj = StrStruct("test.bloo::blah.aweg::[1,2,3]")
        assert(isinstance(obj, StrStruct))
        assert(f"{obj:p}" == "[1, 2, 3]")


    @pytest.mark.xfail
    def test_format_dunder_subselect(self):
        obj = StrStruct("test.bloo::blah.aweg.blee.blawee::[1,2,3]")
        assert(isinstance(obj, StrStruct))
        assert(f"{obj:t}" == "blah.aweg")

class TestTaskName:

    def test_initial(self):
        obj = TaskName("blah::awef")
        assert(isinstance(obj, TaskName))

    def test_root_folding(self):
        """
          a...b -> a..b
          (a,root,root,b) -> (a, root b)
        """
        obj = TaskName("blah::awef....aweg")
        assert(isinstance(obj, TaskName))
        assert(f"{obj:t}" == "awef..aweg")

    def test_root_detection(self):
        """
          a...b -> a..b
          (a,root,root,b) -> (a, root b)
        """
        obj = TaskName("blah::awef..aweg..bloo")
        assert(isinstance(obj, TaskName))
        assert(obj._roots == (1, 3))
