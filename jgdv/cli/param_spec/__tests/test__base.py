#!/usr/bin/env python2
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
from jgdv.cli.param_spec import ParamSpecBase
import jgdv.cli.param_spec as Specs
from .._base import ParamSpecBase
from ... import _interface as API

good_names = ("test", "blah", "bloo")

class TestParamSpecBase:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_initial(self):
        match ParamSpecBase(name="test"):
            case ParamSpecBase() as obj:
                assert(isinstance(obj, API.ParamStruct_p))
            case x:
                 assert(False), x

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head(self, key):
        obj = ParamSpecBase(name=key)
        assert(obj.matches_head(f"-{key}"))
        assert(obj.matches_head(f"-{key[0]}"))
        assert(obj.matches_head(f"-no-{key}"))

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head_assignments(self, key):
        obj = ParamSpecBase(name=key, prefix="--", separator="=")
        assert(not obj.positional)
        assert(obj.matches_head(f"--{key}=val"))
        assert(obj.matches_head(f"--{key[0]}=val"))

    @pytest.mark.parametrize("key", [*good_names])
    def test_match_on_head_fail(self, key):
        obj = ParamSpecBase(name=key, prefix="--")
        assert(not obj.matches_head(key))
        assert(not obj.matches_head(f"{key}=blah"))
        assert(not obj.matches_head(f"-{key}=val"))
        assert(not obj.matches_head(f"-{key[0]}=val"))

    def test_positional(self):
        obj = ParamSpecBase(name="test",
                            type=list,
                            default=[1,2,3],
                            prefix="")
        assert(obj.positional is True)

    @pytest.mark.parametrize(["key", "prefix"], zip(good_names, itz.cycle(["-", "--"])))
    def test_short_key(self, key, prefix):
        obj = ParamSpecBase(name=key, prefix=prefix)
        assert(obj.short == key[0])
        match prefix:
            case "--":
                assert(obj.short_key_str == f"{prefix}{key[0]}")
            case "-":
                assert(obj.short_key_str == f"{prefix}{key[0]}")

class TestParamSpecConsumption:

    def test_consume_nothing(self):
        obj = ParamSpecBase(name="test")
        match obj.consume([]):
            case None:
                assert(True)
            case _:
                assert(False)

    @pytest.mark.xfail
    def test_consume_something(self):
        obj = ParamSpecBase(name="test")
        match obj.consume([]):
            case None:
                assert(False)
            case _:
                assert(True)

class TestParamSpecDefaults:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_build_defaults(self):
        param_dicts = [
            {"name":"test","default":"test"},
            {"name":"next", "default":2},
            {"name":"other", "default":list},
            {"name":"another", "default":lambda: [1,2,3,4]},
        ]
        params = [ParamSpecBase(**x) for x in param_dicts]
        result = ParamSpecBase.build_defaults(params)
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
        params = [ParamSpecBase(**x) for x in param_dicts]
        ParamSpecBase.check_insists(params, {"next": 2, "other":[1,2,3]})
        assert(True)

    def test_check_insist_params_fail(self):
        param_dicts = [
            {"name":"test","default":"test", "insist":False},
            {"name":"next", "default":2, "insist":True},
            {"name":"other", "default":list, "insist":True},
            {"name":"another", "default":lambda: [1,2,3,4], "insist":False},
        ]
        params = [ParamSpecBase(**x) for x in param_dicts]
        with pytest.raises(ParseError) as ctx:
            ParamSpecBase.check_insists(params, {"other":[1,2,3]})

        assert(ctx.value.args[-1] == ["next"])

class TestParamSpecTypes:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_int(self):
        obj = ParamSpecBase(**{"name":"blah", "type":int})
        assert(obj.type_ is int)
        assert(obj.default == 0)

    def test_Any(self):
        obj = ParamSpecBase(**{"name":"blah", "type":Any})
        assert(obj.type_ is Any)
        assert(obj.default is None)

    def test_typed_list(self):
        obj = ParamSpecBase(**{"name":"blah", "type":list[str]})
        assert(obj.type_ is list)
        assert(obj.default is list)

    def test_annotated(self):
        new_class = ParamSpecBase[str]
        assert(new_class is not ParamSpecBase)
        obj = new_class(name="blah")
        assert(obj.type_ is str)
        assert(obj.default is '')

    def test_annotated_list(self):
        obj = ParamSpecBase[list[str]](name="blah")
        assert(obj.type_ is list)
        assert(obj.default is list)

    def test_type_fail(self):
        with pytest.raises(TypeError):
            ParamSpecBase(name="blah", type=ParamSpecBase)

    def test_type_build_fail(self):
        with pytest.raises(TypeError):
            ParamSpecBase(**{"name":"blah", "type":ParamSpecBase})
