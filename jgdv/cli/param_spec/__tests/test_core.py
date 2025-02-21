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
from jgdv.cli.param_spec.core import ToggleParam, LiteralParam, ImplicitParam, KeyParam, RepeatableParam, ChoiceParam, EntryParam, ConstrainedParam

good_names = ("test", "blah", "bloo")
bad_names  = ("-test", "blah=bloo")

class TestToggleParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_toggle(self):
        obj = ToggleParam.model_validate({"name" : "test"})
        match obj.consume(["-test"]):
            case {"test": True,}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_inverse_toggle(self):
        obj = ToggleParam.model_validate({"name" : "test"})
        assert(obj.default_value is False)
        match obj.consume(["-no-test"]):
            case {"test": False,}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_short_toggle(self):
        obj = ToggleParam.model_validate({"name" : "test"})
        match obj.consume(["-t"]):
            case {"test": True,}, 1:
                assert(True)
            case x:
                assert(False), x

class TestLiteralParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_literal(self):
        obj = LiteralParam(name="blah")
        match obj.consume(["blah"]):
            case {"blah":True}, 1:
                assert(True)
            case None:
                assert(False)

    def test_literal_fail(self):
        obj = LiteralParam(name="blah")
        match obj.consume(["notblah"]):
            case None:
                assert(True)
            case _:
                assert(False)

class TestImplicitParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

class TestKeyParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_key_value_str(self):
        obj = KeyParam[str].model_validate({"name" : "test"})
        assert(obj.type_ is str)
        match obj.consume(["-test", "blah"]):
            case {"test":"blah"}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_int(self):
        obj = KeyParam[int].model_validate({"name" : "test"})
        assert(obj.type_ is int)
        match obj.consume(["-test", "20"]):
            case {"test":20}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_fail(self):
        obj = KeyParam[str].model_validate({"name" : "test"})
        match obj.consume(["-nottest", "blah"]):
            case None:
                assert(True)
            case _:
                assert(False)

class TestRepeatableParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_list_single_value(self):
        obj = RepeatableParam.model_validate({"name" : "test", "type" : list})
        match obj.consume(["-test", "bloo"]):
            case {"test": ["bloo"]}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_list_multi_key_val(self):
        obj     = RepeatableParam.model_validate({"name":"test"})
        in_args = ["-test", "bloo", "-test", "blah", "-test", "bloo", "-not", "this"]
        match obj.consume(in_args):
            case {"test": ["bloo", "blah", "bloo"]}, 6:
                assert(True)
            case x:
                assert(False), x

    def test_consume_set_multi(self):
        obj = RepeatableParam[set].model_validate({
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
        obj = RepeatableParam[set].model_validate({
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

    def test_consume_multi_assignment_fail(self):
        obj     = RepeatableParam.model_validate({"name":"test", "type":list, "default":list, "prefix":"--"})
        in_args = ["--test=blah", "--test=bloo"]
        match obj.consume(in_args):
            case None:
                assert(True)
            case _:
                assert(False), x

@pytest.mark.xfail
class TestChoiceParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

@pytest.mark.xfail
class TestEntryParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

@pytest.mark.xfail
class TestConstrainedParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133
