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
from jgdv.cli.param_spec.positional import PositionalParam
from .. import core
from ..assignment import AssignParam
import jgdv.cli.param_spec as Specs

good_names = ("-test", "--blah", "+bloo")
parse_test_vals = [("-test", "-", "test", core.KeyParam),
                   ("--blah", "--", "blah", core.KeyParam),
                   ("--bloo=", "--", "bloo", AssignParam),
                   ("+aweg", "+", "aweg", core.ToggleParam),
                   ]
sorting_names   = ["-next", "<>another", "--test", "<2>other", "<1>diff",]
correct_sorting = ["-next", "--test", "diff", "other", "another"]
##--|

class TestParamSpec:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_paramspec(self):
        obj = ParamSpec.build({"name" : "test"})
        assert(isinstance(obj, Specs.ParamSpecBase))

    @pytest.mark.parametrize(["full", "pre", "name", "subtype"], parse_test_vals)
    def test_name_parse(self, full, pre, name, subtype):
        obj = ParamSpec.build({"name" : full})
        assert(isinstance(obj, Specs.ParamSpecBase))
        assert(isinstance(obj, subtype))
        assert(obj.name == name)
        assert(obj.prefix == pre)

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head(self, key):
        obj = ParamSpec.build({"name" : key, "type":bool})
        assert(obj.matches_head(f"{obj.prefix}{obj.name}"))
        assert(obj.matches_head(f"{obj.prefix}{obj.name[0]}"))
        assert(obj.matches_head(f"{obj.prefix}no-{obj.name}"))

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head_assignments(self, key):
        obj = ParamSpec.build({"name" : f"{key}="})
        assert(not obj.positional)
        assert(obj.matches_head(f"{obj.prefix}{obj.name}=val"))
        assert(obj.matches_head(f"{obj.prefix}{obj.name[0]}=val"))

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head_fail(self, key):
        obj = ParamSpec.build({"name" : key})
        assert(not isinstance(obj, AssignParam))
        assert(obj.matches_head(key))
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

    @pytest.mark.parametrize("key", [*good_names])
    def test_short_key(self, key):
        obj = ParamSpec.build({"name" : key})
        assert(obj.short == obj.name[0])
        assert(obj.short_key_str == f"{obj.prefix}{obj.name[0]}")

    def test_sorting(self):
        target_sort = correct_sorting
        param_dicts = [{"name":x} for x in sorting_names]
        params = [ParamSpec.build(x) for x in param_dicts]
        s_params = sorted(params, key=ParamSpec.key_func)
        for x,y in zip(s_params, target_sort):
            assert(x.key_str == y), s_params

class TestParamSpecConsumption:

    def test_consume_nothing(self):
        obj = ParamSpec.build({"name" : "test"})
        match obj.consume([]):
            case None:
                assert(True)
            case _:
                assert(False)

    def test_consume_with_offset(self):
        obj = ParamSpec.build({"name" : "-test"})
        assert(obj.type_ is str)
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
            {"name":"-next", "default":2},
            {"name":"--other", "default":list},
            {"name":"+another", "default":lambda: [1,2,3,4]},
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

class TestParamSpecTypesExplicit:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

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

    def test_type_fail(self):
        with pytest.raises(TypeError):
            ParamSpec(name="-blah", type=ParamSpec)

    def test_type_build_fail(self):
        with pytest.raises(TypeError):
            ParamSpec.build({"name":"-blah", "type":ParamSpec})

class TestParamSpecAnnotated:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_annotation(self):
        match ParamSpec[bool]:
            case x if issubclass(x, ParamSpec):
                assert(x._override_type is not None)
                assert(ParamSpec._override_type is None)
                accessor = x
            case x:
                 assert(False), x

        match accessor.build({"name":"Aweg"}):
            case core.ToggleParam():
                assert(True)
            case x:
                 assert(False), x

    def test_annotated(self):
        sub = ParamSpec[str]
        obj = sub(name="blah")
        assert(obj.type_ is str)
        assert(obj.default is '')

    def test_annotated_list(self):
        obj = ParamSpec[list[str]](name="blah")
        assert(obj.type_ is list)
        assert(obj.default is list)
