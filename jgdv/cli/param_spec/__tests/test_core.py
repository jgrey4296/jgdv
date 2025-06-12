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
from ..param_spec import ParamSpec
from .. import core

good_names = ("test", "blah", "bloo")
bad_names  = ("-test", "blah=bloo")

class TestToggleParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_toggle(self):
        obj = core.ToggleParam.model_validate({"name" : "test"})
        match obj.consume(["-test"]):
            case {"test": True,}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_inverse_toggle(self):
        obj = core.ToggleParam.model_validate({"name" : "test"})
        assert(obj.default_value is False)
        match obj.consume(["-no-test"]):
            case {"test": False,}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_short_toggle(self):
        obj = core.ToggleParam.model_validate({"name" : "test"})
        match obj.consume(["-t"]):
            case {"test": True,}, 1:
                assert(True)
            case x:
                assert(False), x

class TestImplicitParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

class TestKeyParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_key_value_str(self):
        obj = core.KeyParam[str].model_validate({"name" : "test"})
        assert(obj.type_ is str)
        match obj.consume(["-test", "blah"]):
            case {"test":"blah"}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_int(self):
        obj = core.KeyParam[int].model_validate({"name" : "test"})
        assert(obj.type_ is int)
        match obj.consume(["-test", "20"]):
            case {"test":20}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_fail(self):
        obj = core.KeyParam[str].model_validate({"name" : "test"})
        match obj.consume(["-nottest", "blah"]):
            case None:
                assert(True)
            case _:
                assert(False)



class TestPositionalSpecs:

    def test_consume_positional(self):
        obj = core.PositionalParam(**{"name":"test", "prefix":1, "type":str})
        assert(obj.positional)
        match obj.consume(["aweg", "blah"]):
            case {"test": "aweg"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_positional_list(self):
        obj = core.PositionalParam(**{
            "name"       : "test",
            "type"       : list,
            "default"    : [],
            "prefix"     : "",
            "count" : 2
          })
        match obj.consume(["bloo", "blah", "aweg"]):
            case {"test": ["bloo", "blah"]}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_positional(self):
        obj = core.PositionalParam(**{"name":"test", "prefix":1, "type":str})
        assert(obj.positional)
        match obj.consume(["aweg", "blah"]):
            case {"test": "aweg"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_positional_list(self):
        obj = core.PositionalParam(**{
            "name"       : "test",
            "type"       : list,
            "default"    : [],
            "prefix"     : "",
            "count" : 2
          })
        match obj.consume(["bloo", "blah", "aweg"]):
            case {"test": ["bloo", "blah"]}, 2:
                assert(True)
            case x:
                assert(False), x


    @pytest.mark.skip
    def test_todo(self):
        pass

class TestAssignParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_assignment(self):
        obj = core.AssignParam(**{"name" : "test"})
        in_args             = ["--test=blah", "other"]
        match obj.consume(in_args):
            case {"test":"blah"}, 1:
                assert(True)
            case x:
                assert(False), x


    def test_consume_int(self):
        obj = core.AssignParam(**{"name" : "test", "type":int})
        in_args             = ["--test=2", "other"]
        match obj.consume(in_args):
            case {"test": 2}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_assignment_wrong_prefix(self):
        obj = core.AssignParam(**{"name" : "test"})
        match obj.consume(["-t=blah"]):
            case None:
                assert(True)
            case x:
                assert(False), x
