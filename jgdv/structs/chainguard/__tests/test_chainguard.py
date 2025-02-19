#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import logging as logmod
import warnings
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple,
                    TypeVar, cast)
##-- end imports

import typing
import pytest
from jgdv.structs.chainguard.errors import GuardedAccessError
from jgdv.structs.chainguard import ChainGuard

logging = logmod.root

class TestBaseGuard:

    def test_initial(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic is not None)

    def test_is_mapping(self):
        basic = ChainGuard({"test": "blah"})
        assert(isinstance(basic, typing.Mapping))


    def test_is_dict(self):
        basic = ChainGuard({"test": "blah"})
        assert(isinstance(basic, dict))


    def test_match_as_dict(self):
        match ChainGuard({"test": "blah"}):
            case dict():
                assert(True)
            case x:
                 assert(False), x


    def test_basic_access(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic.test == "blah")

    def test_basic_item_access(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic['test'] == "blah")

    def test_multi_item_access(self):
        basic = ChainGuard({"test": {"blah": "bloo"}})
        assert(basic['test', "blah"] ==  "bloo")

    def test_basic_access_error(self):
        basic = ChainGuard({"test": "blah"})
        with pytest.raises(GuardedAccessError):
            basic.none_existing

    def test_item_access_error(self):
        basic = ChainGuard({"test": "blah"})
        with pytest.raises(GuardedAccessError):
            basic['non_existing']

    def test_dot_access(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic.test == "blah")

    def test_index(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic._index() == ["<root>"])

    def test_index_independence(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic._index() == ["<root>"])
        basic.test
        assert(basic._index() == ["<root>"])

    def test_nested_access(self):
        basic = ChainGuard({"test": {"blah": 2}})
        assert(basic.test.blah == 2)

    def test_repr(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert(repr(basic) == "<ChainGuard:['test', 'bloo']>")

    def test_immutable(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        with pytest.raises(TypeError):
            basic.test = 5

    def test_uncallable(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        with pytest.raises(GuardedAccessError):
            basic()

    def test_iter(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        vals = list(basic)
        assert(vals == ["test", "bloo"])

    def test_contains(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert("test" in basic)

    def test_contains_fail(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert("blah" not in basic)

    def test_get(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert(basic.get("bloo") == 2)

    def test_get_default(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert(basic.get("blah") is None)

    def test_get_default_value(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert(basic.get("blah", 5) == 5)

    def test_keys(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert(list(basic.keys()) == ["test", "bloo"])

    def test_items(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert(list(basic.items()) == [("test", {"blah": 2}), ("bloo", 2)])

    def test_values(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert(list(basic.values()) == [{"blah": 2}, 2])

    def test_list_access(self):
        basic = ChainGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert(basic.test.blah == [1,2,3])
        assert(basic.bloo == ["a","b","c"])

    def test_contains(self):
        basic = ChainGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("test" in basic)

    def test_contains_false(self):
        basic = ChainGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("doesntexist" not in basic)

    def test_contains_nested_but_doesnt_recurse(self):
        basic = ChainGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("blah" not in basic)

    def test_contains_nested(self):
        basic = ChainGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("blah" in basic.test)

    def test_contains_nested_false(self):
        basic = ChainGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("doesntexist" not in basic.test)

class TestLoaderGuard:

    @pytest.mark.skip(reason="not implemented")
    def test_initial_load(self):
        # TODO
        raise

class TestGuardMerge:

    def test_initial(self):
        simple = ChainGuard.merge({"a":2}, {"b": 5})
        assert(isinstance(simple, ChainGuard))
        assert(simple._table() == {"a": 2, "b": 5})

    def test_merge_conflict(self):
        with pytest.raises(KeyError):
            ChainGuard.merge({"a":2}, {"a": 5})

    def test_merge_with_shadowing(self):
        basic = ChainGuard.merge({"a":2}, {"a": 5, "b": 5}, shadow=True)
        assert(dict(basic) == {"a":2, "b": 5})

    def test_merge_guards(self):
        first  = ChainGuard({"a":2})
        second = ChainGuard({"a": 5, "b": 5})

        merged = ChainGuard.merge(first ,second, shadow=True)
        assert(dict(merged) == {"a":2, "b": 5})

    def test_dict_updated_with_chainguard(self):
        the_dict = {}
        cg = ChainGuard({"a": 2, "b": 3, "c": {"d": "test" }})
        assert(not bool(the_dict))
        the_dict.update(cg)
        assert(bool(the_dict))
        assert("a" in the_dict)
        assert(the_dict["c"]["d"] == "test")

class TestFailAccess:

    def test_basic(self):
        obj = ChainGuard({})
        assert(obj is not  None)

    def test_basic_fail(self):
        obj = ChainGuard({})
        result = obj.on_fail(5).nothing()
        assert(result == 5)

    def test_fail_access_dict(self):
        obj = ChainGuard({"nothing": {}})
        result = obj.on_fail({}).nothing['blah']()
        assert(isinstance(result, dict))

    def test_fail_access_list(self):
        obj = ChainGuard({"nothing": []})
        result = obj.on_fail([]).nothing[1]()
        assert(isinstance(result, list))

    def test_fail_access_type_mismatch(self):
        obj = ChainGuard({"nothing": {}})
        result = obj.on_fail({}).nothing[1]()
        assert(isinstance(result, dict))

    def test_fail_return_none(self):
        obj = ChainGuard({"nothing": {}})
        result = obj.on_fail(None).nothing.blah.bloo()
        assert(result is None)


    def test_success_return_val(self):
        obj = ChainGuard({"nothing": {"blah": {"bloo": 10}}})
        result = obj.on_fail(None).nothing.blah.bloo()
        assert(result == 10)
