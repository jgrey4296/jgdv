#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011
# imports:
from __future__ import annotations

import itertools as itz
import logging as logmod
import warnings
import pathlib as pl
import typing
from typing import Any
import pytest
from jgdv.cli import ParseError
from ..param_spec import ParamSpec
from ... import _interface as API  # noqa: N812
from .. import core
##--| vars
logging = logmod.root

good_names = ("test", "blah", "bloo")
bad_names  = ("-test", "blah=bloo")

##--|

class TestToggleParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_fail_with_wrong_type(self):
        data     = {"name" : "-test", "type":str}
        with pytest.raises(TypeError):
            core.ToggleParam(**data)

    def test_consume_toggle(self):
        data     = {"name" : "-test"}
        in_data  = [ "-test" ]
        obj      = core.ToggleParam(**data)
        match obj.consume(in_data):
            case {"test": True}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_inverse_toggle(self):
        data     = {"name" : "-test"}
        in_data  = ["-no-test"]
        obj      = core.ToggleParam(**data)
        assert(obj.default_value is False)
        match obj.consume(in_data):
            case {"test": False}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_short_toggle(self):
        data     = {"name" : "-test"}
        in_data  = ["-t"]
        obj      = core.ToggleParam(**data)
        match obj.consume(in_data):
            case {"test": True}, 1:
                assert(True)
            case x:
                assert(False), x

class TestPositionalParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_protocol(self):
        assert(issubclass(core.PositionalParam, ParamSpec))
        assert(isinstance(core.PositionalParam, API.ParamStruct_p))
        assert(issubclass(core.PositionalParam, API.PositionalParam_p))

    def test_consume_positional(self):
        data     = {"name":"<1>test", "type":str}
        in_data  = ["aweg", "blah"]
        obj      = core.PositionalParam(**data)
        match obj.consume(in_data):
            case {"test": "aweg"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_positional_list(self):
        data = {
            "name"     : "test",
            "type"     : list,
            "default"  : [],
            "count"    : 2,
        }
        in_data = ["bloo", "blah", "aweg"]
        obj = core.PositionalParam(**data)
        match obj.consume(in_data):
            case {"test": ["bloo", "blah"]}, 2:
                assert(True)
            case x:
                assert(False), x

class TestKeyParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_key_value_str(self):
        data     = {"name" : "-test", "type":str}
        in_data  = ["-test", "blah"]
        obj      = core.KeyParam(**data)
        assert(obj.type_ is str)
        match obj.consume(in_data):
            case {"test":"blah"}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_int(self):
        data     = {"name" : "-test", "type": int}
        in_data  = ["-test", "20"]
        obj      = core.KeyParam(**data)
        assert(obj.type_ is int)
        match obj.consume(in_data):
            case {"test":20}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_key_value_fail(self):
        data     = {"name" : "-test", "type":str}
        in_data  = ["-nottest", "blah"]
        obj      = core.KeyParam(**data)
        match obj.consume(in_data):
            case None:
                assert(True)
            case _:
                assert(False)

class TestAssignParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_fail_with_wrong_type(self):
        data     = {"name" : "-test=", "type":bool}
        with pytest.raises(TypeError):
            core.AssignParam(**data)

    def test_fail_with_no_prefix(self):
        data     = {"name" : "test="}
        with pytest.raises(ValueError):
            core.AssignParam(**data)

    def test_fail_with_no_separator(self):
        data     = {"name" : "-test"}
        with pytest.raises(ValueError):
            core.AssignParam(**data)

    def test_build_with_custom_prefix(self):
        data     = {"name" : "+test="}
        val = core.AssignParam(**data)
        assert(val.prefix == "+")

    def test_consume_assignment(self):
        data     = {"name" : "--test="}
        in_args  = ["--test=blah", "other"]
        obj      = core.AssignParam(**data)
        match obj.consume(in_args):
            case {"test":"blah"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_int(self):
        data     = {"name" : "--test=", "type":int}
        in_args  = ["--test=2", "other"]
        obj      = core.AssignParam(**data)
        match obj.consume(in_args):
            case {"test": 2}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_assignment_wrong_prefix(self):
        data     = {"name" : "--test="}
        in_args  = ["-t=blah"]
        obj      = core.AssignParam(**data)
        match obj.consume(in_args):
            case None:
                assert(True)
            case x:
                assert(False), x
