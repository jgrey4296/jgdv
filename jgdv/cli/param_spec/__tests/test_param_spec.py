#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, ANN001, B011, PLR0133, PLR2004
# Imports:
from __future__ import annotations

import itertools as itz
import logging as logmod
import warnings
import pathlib as pl
import pytest
import types
from typing import Any
from ... import ParseError
from .. import param_spec as pbase
from ..param_spec import ParamSpec, ParamProcessor
from ... import _interface as API # noqa: N812

##--| vars
logging          = logmod.root
good_names       = ("test", "blah", "bloo")
parse_test_vals  = [("-test", "-", "test"),
                    ("--blah", "--", "blah"),
                    ("--bloo=", "--", "bloo"),
                    ("+aweg", "+", "aweg"),
                   ]

sorting_names   = ["-next", "<>another", "--test", "<2>other", "<1>diff"]
correct_sorting = ["-next", "--test", "diff", "other", "another"]
##--|

class TestParamProcessor:

    def test_sanity(self):
        assert(True is not False)

    ##--| name parsing

    @pytest.mark.parametrize(["full", "pre", "name"], parse_test_vals)
    def test_name_parse(self, full, pre, name):
        res = ParamProcessor().parse_name(full)
        assert(res['name'] == name)
        assert(res['prefix'] == pre)

    def test_name_parse_complex(self):
        res = ParamProcessor().parse_name("--group-by")
        assert(res['name'] == "group-by")
        assert(res['prefix'] == "--")

    def test_name_parse_complex_assign(self):
        res = ParamProcessor().parse_name("--group-by=")
        assert(res['name'] == "group-by")
        assert(res['prefix'] == "--")

    ##--| match utils

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head(self, key):
        """ Simple names match a set of standard variations """
        obj    = ParamProcessor()
        param  = ParamSpec(name=f"-{key}")
        assert(obj.matches_head(param, f"-{key}"))
        assert(obj.matches_head(param, f"-{key[0]}"))
        assert(obj.matches_head(param, f"-no-{key}"))

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head_assignments(self, key):
        """ Assignments match on a reduced set of variations """
        obj    = ParamProcessor()
        param  = ParamSpec(name=f"--{key}=")
        assert(obj.matches_head(param, f"--{key}=val"))
        assert(obj.matches_head(param, f"--{key[0]}=val"))

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head_fail(self, key):
        """ some variations do not match """
        obj    = ParamProcessor()
        param  = ParamSpec(name=f"--{key}")
        assert(not obj.matches_head(param, key))
        assert(not obj.matches_head(param, f"{key}=blah"))
        assert(not obj.matches_head(param, f"-{key}=val"))
        assert(not obj.matches_head(param, f"-{key[0]}=val"))

##--|

class TestParamSpec_classmethods:

    def test_sanity(self):
        assert(True is not False)

    def test_build_defaults(self):
        param_dicts = [
            {"name":"test","default":"test"},
            {"name":"-next", "default":2},
            {"name":"--other", "default":list},
            {"name":"+another", "default":lambda: [1,2,3,4]},
        ]
        params = [y for x in param_dicts if (y:=ParamSpec(**x))]
        assert(len(params) == len(param_dicts))
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
        params = [ParamSpec(**x) for x in param_dicts]
        ParamSpec.check_insists(params, {"next": 2, "other":[1,2,3]})
        assert(True)

    def test_check_insist_params_fail(self):
        param_dicts = [
            {"name":"test","default":"test", "insist":False},
            {"name":"next", "default":2, "insist":True},
            {"name":"other", "default":list, "insist":True},
            {"name":"another", "default":lambda: [1,2,3,4], "insist":False},
        ]
        params = [ParamSpec(**x) for x in param_dicts]
        with pytest.raises(ParseError) as ctx:
            ParamSpec.check_insists(params, {"other":[1,2,3]})

        assert(ctx.value.args[-1] == ["next"])

class TestParamSpec_Sorting:

    def test_sanity(self):
        assert(True is not False)

    def test_sorting(self):
        target_sort  = correct_sorting
        param_dicts  = [{"name":x} for x in sorting_names]
        params       = [ParamSpec(**x) for x in param_dicts]
        s_params     = sorted(params, key=ParamSpec.key_func)
        for x,y in zip(s_params, target_sort, strict=True):
            assert(x.key_str == y), s_params

class TestParamSpec_Basic:

    def test_sanity(self):
        assert(True is not False)

    def test_initial(self):
        match ParamSpec(name="test"):
            case ParamSpec() as obj:
                assert(isinstance(obj, API.ParamStruct_p))
            case x:
                 assert(False), x


    def test_equality(self):
        obj1 = ParamSpec(name="test")
        obj2 = ParamSpec(name="test")
        assert(obj1 is not obj2)
        assert(obj1 == obj2)


    def test_equality_trivial_fail(self):
        obj1 = ParamSpec(name="test")
        obj2 = "blah"
        assert(obj1 is not obj2)
        assert(obj1 != obj2)


    def test_equality_fail_on_name(self):
        obj1 = ParamSpec(name="test")
        obj2 = ParamSpec(name="blah")
        assert(obj1 is not obj2)
        assert(obj1 != obj2)


    def test_equality_fail_on_prefix(self):
        obj1 = ParamSpec(name="-test")
        obj2 = ParamSpec(name="--test")
        assert(obj1 is not obj2)
        assert(obj1 != obj2)


    def test_equaltiy_fail_on_separator(self):
        obj1 = ParamSpec(name="--test=")
        obj2 = ParamSpec(name="--test")
        assert(obj1 is not obj2)
        assert(obj1 != obj2)

    def test_key_strs_prop(self):
        obj = ParamSpec(name="-test")
        assert(obj.key_str == "-test")
        match obj.key_strs:
            case list():
                assert(True)
            case x:
                 assert(False), x

    @pytest.mark.parametrize(["key", "prefix"], zip(good_names, itz.cycle(["-", "--"])))
    def test_short_key(self, key, prefix):
        obj = ParamSpec(name=f"{prefix}{key}")
        assert(obj.short == key[0])
        match prefix:
            case "--":
                assert(obj.short_key_str == f"{prefix}{key[0]}")
            case "-":
                assert(obj.short_key_str == f"{prefix}{key[0]}")

class TestParamSpec_Types:

    def test_sanity(self):
        assert(True is not False)

    def test_int(self):
        obj = ParamSpec(**{"name":"blah", "type":int})
        assert(obj.type_ is int)
        assert(obj.default == 0)

    def test_Any(self): # noqa: N802
        obj = ParamSpec(**{"name":"blah", "type":Any})
        assert(obj.type_ is None)
        assert(obj.default is None)

    def test_typed_list(self):
        obj = ParamSpec(**{"name":"blah", "type":list[str]})
        assert(isinstance(obj.type_, types.GenericAlias))
        assert(obj.type_.__origin__ is list)
        assert(obj.type_.__args__[0] is str)
        assert(obj.default is list)

    def test_annotated(self):

        class TestParam(ParamSpec[str]):
            pass

        assert(issubclass(TestParam, ParamSpec))
        obj = TestParam(name="blah")
        assert(obj.type_ is str)
        assert(obj.default == '')

    def test_annotated_list(self):

        class TestParam2(ParamSpec[list[str]]):
            pass

        obj = TestParam2(name="blah")
        assert(obj.type_ is list)
        assert(obj.default is list)

    def test_type_fail(self):
        with pytest.raises(TypeError):
            ParamSpec(name="blah", type=ParamSpec)

    def test_type_build_fail(self):
        with pytest.raises(TypeError):
            ParamSpec(**{"name":"blah", "type":ParamSpec})

class TestParamSpec_Building:

    def test_sanity(self):
        assert(True is not False)

    def test_int(self):
        obj = ParamSpec(**{"name":"blah", "type":int})
        assert(obj.type_ is int)
        assert(obj.default == 0)

    def test_Any(self): # noqa: N802
        obj = ParamSpec(**{"name":"blah", "type":Any})
        assert(obj.type_ is None)
        assert(obj.default is None)

    def test_typed_list(self):
        obj = ParamSpec(**{"name":"blah", "type":list[str]})
        assert(isinstance(obj.type_, types.GenericAlias))
        assert(obj.type_.__origin__ is list)
        assert(obj.type_.__args__[0] is str)
        assert(obj.default is list)

    def test_type_fail(self):
        with pytest.raises(TypeError):
            ParamSpec(name="-blah", type=ParamSpec)

    def test_type_build_fail(self):
        with pytest.raises(TypeError):
            ParamSpec(**{"name":"-blah", "type":ParamSpec})

class TestParamSpec_Consumption:

    def test_sanity(self):
        assert(True is not False)

    def test_consume_nothing(self):
        data     = {"name" : "test"}
        in_args  = []
        obj      = ParamSpec(**data)
        match obj.consume(in_args):
            case None:
                assert(True)
            case _:
                assert(False)

    def test_consume_match(self):
        data     = {"name" : "-test"}
        in_args  = ["-test"]
        obj      = ParamSpec(**data)
        assert(isinstance(obj, ParamSpec))
        match obj.consume(in_args):
            case {"test": True}, 1:
                assert(True)
            case _:
                assert(False)

    def test_consume_with_remaining(self):
        data     = {"name"  : "-test"}
        in_args  = ["-test", "blah"]
        obj      = ParamSpec(**data)
        assert(isinstance(obj, ParamSpec))
        match obj.consume(in_args):
            case {"test": True}, 1:
                assert(True)
            case _:
                assert(False)

    def test_consume_with_offset(self):
        data     = {"name" : "-test"}
        in_args  = ["blah", "bloo", "-test", "aweg"]
        obj      = ParamSpec(**data)
        match obj.consume(in_args, offset=2):
            case {"test": True}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_nothing_without_offset(self):
        data     = {"name" : "-test", "type" : str}
        in_args  = ["blah", "bloo", "-test", "aweg"]
        obj      = ParamSpec(**data)
        assert(obj.type_ is str)
        match obj.consume(in_args):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_consume_short(self):
        data     = {"name" : "--test", "default":False, "type":bool}
        in_args  = ["--t", "blah", "bloo"]
        obj      = ParamSpec(**data)
        assert(obj.type_ is bool)
        match obj.consume(in_args):
            case {"test": True}, 1:
                assert(True)
            case x:
                assert(False), x

