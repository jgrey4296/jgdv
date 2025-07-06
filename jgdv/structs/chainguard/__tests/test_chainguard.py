#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN201, B011, B018, PLR2004
##-- import
from __future__ import annotations

import logging as logmod
import warnings
import pathlib as pl
from typing import Final
##-- end import

import typing
import pytest
from ..errors import GuardedAccessError
from .. import ChainGuard
from ..proxies.base import GuardProxy

logging = logmod.root
example_dict : Final[dict] = {
    "test": {
        "val"   : 2,
        "blah"  : "bloo",
    },
}
example_toml : Final[str] = """
[test]
val   = 2
blah  = "bloo"
"""
ROOT_INDEX : Final[tuple[str, ...]] = ("<root>",)
##--|

class TestBaseGuard:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_initial(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic is not None)

    def test_is_mapping(self):
        basic = ChainGuard({"test": "blah"})
        assert(isinstance(basic, typing.Mapping))
        assert(isinstance(basic, dict))

    def test_is_dict(self):
        basic = ChainGuard({"test": "blah"})
        assert(isinstance(basic, dict))

    def test_match_as_dict(self):
        match ChainGuard({"test": "blah"}):
            case dict():
                assert(True)
            case x:
                 assert(False), x

    def test_repr(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        assert(repr(basic) == "<ChainGuard:['test', 'bloo']>")


    def test_basic_table(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        match basic._table():
            case dict() as data:
                assert(not isinstance(data, ChainGuard))
            case x:
                assert(False), x

class TestBaseGuard_Access:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

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

    def test_nested_access(self):
        basic = ChainGuard({"test": {"blah": 2}})
        assert(basic.test.blah == 2)

    def test_immutable(self):
        basic = ChainGuard({"test": {"blah": 2}, "bloo": 2})
        with pytest.raises(TypeError):
            basic.test = 5

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

class TestBaseGuard_Info:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_index(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic._index() == ROOT_INDEX)

    def test_index_independence(self):
        basic = ChainGuard({"test": "blah"})
        assert(basic._index() == ROOT_INDEX)
        basic.test
        assert(basic._index() == ROOT_INDEX)

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

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_from_dict(self):
        match ChainGuard.from_dict(example_dict):
            case ChainGuard():
                assert(True)
            case x:
                assert(False), x

    def test_read_text(self):
        match ChainGuard.read(example_toml):
            case ChainGuard() as x:
                assert("test" in x)
                assert(x.test.val == 2)
            case x:
                assert(False), x

class TestGuardMerge:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

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

class TestProxyFailAccess:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

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
        result = obj.on_fail([]).nothing[1]
        assert(isinstance(result, GuardProxy))
        assert(isinstance(result(), list))
        assert(result() == [])

    def test_fail_access_list_with_vals(self):
        obj = ChainGuard({"nothing": []})
        result = obj.on_fail([1,2,3,4]).nothing[1]
        assert(isinstance(result, GuardProxy))
        assert(isinstance(result(), list))
        assert(result() == [1,2,3,4])

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

    def test_success_list_access(self):
        obj     = ChainGuard({"nothing": {"blah": [{"bloo":20}, {"bloo": 10}]}})
        result  = obj.on_fail(None).nothing.blah[1].bloo
        assert(isinstance(result, GuardProxy))
        assert(result() == 10)


    def test_on_fail_with_list_fallback(self):
        obj     = ChainGuard({"nothing": {"blah-aweg": [{"bloo":20}, {"bloo": 10}]}})
        result  = obj.on_fail([]).nothing.blah_aweg
        assert(isinstance(result, GuardProxy))
        match result():
            case list():
                assert(True)
            case x:
                assert(False), x
