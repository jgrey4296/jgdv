#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import itertools as itz
import logging as logmod
import warnings
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
##-- end imports
logging = logmod.root

import pytest
from jgdv.cli import ParseError
from jgdv.cli.param_spec import ParamSpec
import jgdv.cli.param_spec as Specs

good_names = ("test", "blah", "bloo")
bad_names  = ("-test", "blah=bloo")

class TestParamSpec:

    def test_sanity(self):
        assert(True is not False)
        test = ParamSpec[bool].build({"name":"Aweg"})

    def test_paramspec(self):
        obj = ParamSpec.build({"name" : "test"})
        assert(isinstance(obj, Specs.ParamSpecBase))

    @pytest.mark.parametrize("key", [*bad_names])
    def test_key_validation_fail(self, key):
        with pytest.raises(TypeError):
            ParamSpec.build({"name": key})

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head(self, key):
        obj = ParamSpec.build({"name" : key})
        assert(obj.matches_head(f"-{key}"))
        assert(obj.matches_head(f"-{key[0]}"))
        assert(obj.matches_head(f"-no-{key}"))

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head_assignments(self, key):
        obj = ParamSpec.build({"name" : key, "prefix":"--"})
        assert(not obj.positional)
        assert(obj.matches_head(f"--{key}=val"))
        assert(obj.matches_head(f"--{key[0]}=val"))

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head_fail(self, key):
        obj = ParamSpec.build({"name" : key, "prefix":"--"})
        assert(not obj.matches_head(key))
        assert(not obj.matches_head(f"{key}=blah"))
        assert(not obj.matches_head(f"-{key}=val"))
        assert(not obj.matches_head(f"-{key[0]}=val"))

    def test_positional(self):
        obj = ParamSpec.build({
            "name"       : "test",
            "type"       : list,
            "default"    : [1,2,3],
            "prefix"     : ""
            })
        assert(obj.positional is True)

    @pytest.mark.parametrize(["key", "prefix"], zip(good_names, itz.cycle(["-", "--"])))
    def test_short_key(self, key, prefix):
        obj = ParamSpec.build({"name" : key, "prefix": prefix})
        assert(obj.short == key[0])
        match prefix:
            case "--":
                assert(obj.short_key_str == f"{prefix}{key[0]}")
            case "-":
                assert(obj.short_key_str == f"{prefix}{key[0]}")

    def test_sorting(self):
        target_sort = ["test", "next", "another", "diff", "other"]
        param_dicts = [
            {"name":"next",    "prefix":"-"},
            {"name":"another", "prefix": ""},
            {"name":"test",    "prefix":"--"},
            {"name":"other",   "prefix": 2},
            {"name":"diff",    "prefix": 1},
        ]
        params = [ParamSpec.build(x) for x in param_dicts]
        s_params = sorted(params, key=ParamSpec.key_func)
        for x,y in zip(s_params, target_sort):
            assert(x.name == y)

class TestParamSpecConsumption:

    def test_consume_nothing(self):
        obj = ParamSpec.build({"name" : "test"})
        match obj.consume([]):
            case None:
                assert(True)
            case _:
                assert(False)

    def test_consume_with_offset(self):
        obj = ParamSpec.build({"name" : "test", "type":"str"})
        match obj.consume(["-test", "blah", "bloo", "-test", "aweg"], offset=3):
            case {"test": "aweg"}, 2:
                assert(True)
            case x:
                assert(False), x

class TestParamSpecDefaults:

    def test_sanity(self):
        assert(True is not False)

    def test_build_defaults(self):
        param_dicts = [
            {"name":"test","default":"test"},
            {"name":"next", "default":2},
            {"name":"other", "default":list},
            {"name":"another", "default":lambda: [1,2,3,4]},
        ]
        params = [ParamSpec.build(x) for x in param_dicts]
        result = ParamSpec.build_defaults(params)
        assert(result['test'] == 'test')
        assert(result['next'] == 2)
        assert(result['other'] == [])
        assert(result['another'] == [1,2,3,4])

    def test_check_insist_params(self):
        param_dicts = [
            {"name":"test","default":"test", "insist":False},
            {"name":"next", "default":2, "insist":True},
            {"name":"other", "default":list, "insist":True},
            {"name":"another", "default":lambda: [1,2,3,4], "insist":False},
        ]
        params = [ParamSpec.build(x) for x in param_dicts]
        ParamSpec.check_insists(params, {"next": 2, "other":[1,2,3]})
        assert(True)

    def test_check_insist_params_fail(self):
        param_dicts = [
            {"name":"test","default":"test", "insist":False},
            {"name":"next", "default":2, "insist":True},
            {"name":"other", "default":list, "insist":True},
            {"name":"another", "default":lambda: [1,2,3,4], "insist":False},
        ]
        params = [ParamSpec.build(x) for x in param_dicts]
        with pytest.raises(ParseError) as ctx:
            ParamSpec.check_insists(params, {"other":[1,2,3]})

        assert(ctx.value.args[-1] == ["next"])

class TestParamSpecTypes:

    def test_sanity(self):
        assert(True is not False)

    def test_int(self):
        obj = ParamSpec.build({"name":"blah", "type":int})
        assert(obj.type_ is int)
        assert(obj.default == 0)

    def test_Any(self):
        obj = ParamSpec.build({"name":"blah", "type":Any})
        assert(obj.type_ is Any)
        assert(obj.default is None)

    def test_typed_list(self):
        obj = ParamSpec.build({"name":"blah", "type":list[str]})
        assert(obj.type_ is list)
        assert(obj.default is list)

    def test_annotated(self):
        obj = ParamSpec[str](name="blah")
        assert(obj.type_ is str)
        assert(obj.default is '')

    def test_annotated_list(self):
        obj = ParamSpec[list[str]](name="blah")
        assert(obj.type_ is list)
        assert(obj.default is list)

    def test_type_fail(self):
        with pytest.raises(TypeError):
            ParamSpec(name="blah", type=ParamSpec)

    def test_type_build_fail(self):
        with pytest.raises(TypeError):
            ParamSpec.build({"name":"blah", "type":ParamSpec})
