#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011, PLR0133
# Imports:
from __future__ import annotations

import itertools as itz
import logging as logmod
import warnings
import pathlib as pl
import pytest
from jgdv.cli import ParseError
from jgdv.cli.param_spec import ParamSpec
from jgdv.cli.param_spec.defaults import HelpParam, VerboseParam, SeparatorParam

##--| Values
logging = logmod.root
good_names = ("test", "blah", "bloo")
bad_names  = ("-test", "blah=bloo")

##--| Tests

class TestHelpParam:

    def test_sanity(self):
        assert(True is not False)

    def test_basic(self):
        match HelpParam():
            case HelpParam() as val:
                assert(val.default is False)
                assert(val.implicit is True)
            case x:
                assert(False), x

    def test_consume(self):
        obj = HelpParam()
        in_data = ["--help"]
        match obj.consume(in_data):
            case {"help": True}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_short(self):
        obj = HelpParam()
        in_data = ["--h"]
        match obj.consume(in_data):
            case {"help": True}, 1:
                assert(True)
            case x:
                assert(False), x

class TestVerboseParam:

    def test_sanity(self):
        assert(True is not False)

    def test_basic(self):
        match VerboseParam():
            case VerboseParam() as val:
                assert(val.implicit is True)
            case x:
                assert(False), x

class TestSeparatorParam:

    def test_sanity(self):
        assert(True is not False)

    def test_basic(self):
        match SeparatorParam():
            case SeparatorParam() as val:
                assert(val.implicit is True)
            case x:
                assert(False), x


    def test_consume(self):
        in_args = ["--"]
        obj = SeparatorParam()
        assert(obj.prefix == "-")
        assert(obj.name == "-")
        match obj.consume(in_args):
            case {"-": True}, 1:
                assert(True)
            case x:
                assert(False), x
