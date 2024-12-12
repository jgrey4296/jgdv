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
from jgdv.cli.param_spec import ParamSpec, ArgParseError
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
            "positional" : True
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
        target_sort = ["another", "diff", "other", "next", "test"]
        param_dicts = [
            {"name":"test",    "prefix":"--"},
            {"name":"next",    "prefix":"-"},
            {"name":"other",   "positional": 2},
            {"name":"diff",    "positional": 1},
            {"name":"another", "positional": True},
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

    def test_consume_toggle(self):
        obj = Specs.ToggleParam.build({"name" : "test"})
        match obj.consume(["-test"]):
            case {"test": True,}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_inverse_toggle(self):
        obj = Specs.ToggleParam.build({"name" : "test"})
        assert(obj.default_value is False)
        match obj.consume(["-no-test"]):
            case {"test": False,}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_short_toggle(self):
        obj = Specs.ToggleParam.build({"name" : "test"})
        match obj.consume(["-t"]):
            case {"test": True,}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_str(self):
        obj = Specs.KeyParam[str].build({"name" : "test"})
        assert(obj.type_ is str)
        match obj.consume(["-test", "blah"]):
            case {"test":"blah"}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_int(self):
        obj = Specs.KeyParam[int].build({"name" : "test"})
        assert(obj.type_ is int)
        match obj.consume(["-test", "20"]):
            case {"test":20}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_fail(self):
        obj = Specs.KeyParam[str].build({"name" : "test"})
        match obj.consume(["-nottest", "blah"]):
            case None:
                assert(True)
            case _:
                assert(False)

    def test_consume_list_single_value(self):
        obj = Specs.RepeatableParam.build({"name" : "test", "type" : list})
        match obj.consume(["-test", "bloo"]):
            case {"test": ["bloo"]}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_list_multi_key_val(self):
        obj     = Specs.RepeatableParam.build({"name":"test"})
        in_args = ["-test", "bloo", "-test", "blah", "-test", "bloo", "-not", "this"]
        match obj.consume(in_args):
            case {"test": ["bloo", "blah", "bloo"]}, 6:
                assert(True)
            case x:
                assert(False), x

    def test_consume_set_multi(self):
        obj = Specs.RepeatableParam[set].build({
            "name"    : "test",
            "type"    : set,
            "default" : set,
          })
        in_args             = ["-test", "bloo", "-test", "blah", "-test", "bloo", "-not", "this"]
        match obj.consume(in_args):
            case {"test": set() as x}, 6:
                assert(x == {"bloo", "blah"})
            case x:
                assert(False), x

    def test_consume_str_multi_set_fail(self):
        obj = Specs.RepeatableParam[set].build({
            "name" : "test",
            "type" : str,
            "default" : "",
          })
        in_args             = ["-nottest", "bloo", "-nottest", "blah", "-nottest", "bloo", "-not", "this"]
        match obj.consume(in_args):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_consume_assignment(self):
        obj = Specs.AssignParam.build({"name" : "test", "type" : str, "prefix":"--"})
        in_args             = ["--test=blah", "other"]
        match obj.consume(in_args):
            case {"test":"blah"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_multi_assignment_fail(self):
        obj     = Specs.RepeatableParam.build({"name":"test", "type":list, "default":list, "prefix":"--"})
        in_args = ["--test=blah", "--test=bloo"]
        match obj.consume(in_args):
            case None:
                assert(True)
            case _:
                assert(False), x

    def test_consume_assignment_wrong_prefix(self):
        obj = Specs.AssignParam.build({"name" : "test"})
        match obj.consume(["-t=blah"]):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_consume_with_offset(self):
        obj = ParamSpec.build({"name" : "test", "type":"str"})
        match obj.consume(["-test", "blah", "bloo", "-test", "aweg"], offset=3):
            case {"test": "aweg"}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_positional(self):
        obj = Specs.PositionalParam.build({"name":"test", "positional":True, "type":str})
        match obj.consume(["aweg", "blah"]):
            case {"test": "aweg"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_positional_list(self):
        obj = Specs.PositionalParam.build({
            "name"       : "test",
            "type"       : list,
            "default"    : [],
            "positional" : 2
          })
        match obj.consume(["bloo", "blah", "aweg"]):
            case {"test": ["bloo", "blah"]}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_literal(self):
        obj = Specs.LiteralParam(name="blah")
        match obj.consume(["blah"]):
            case {"blah":True}, 1:
                assert(True)
            case None:
                assert(False)

    def test_literal_fail(self):
        obj = Specs.LiteralParam(name="blah")
        match obj.consume(["notblah"]):
            case None:
                assert(True)
            case _:
                assert(False)


    def test_wildcard_assign(self):
        obj = Specs.WildcardParam()
        match obj.consume(["--blah=other"]):
            case {"blah":"other"}, 1:
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
        with pytest.raises(ArgParseError) as ctx:
            ParamSpec.check_insists(params, {"other":[1,2,3]})

        assert(ctx.value.args[-1] == ["next"])

        
class TestParamReactiveBuild:

    def test_sanity(self):
        assert(True is not False)
