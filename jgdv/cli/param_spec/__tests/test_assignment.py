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
from jgdv.cli.param_spec.assignment import AssignParam, WildcardParam

good_names = ("test", "blah", "bloo")
bad_names  = ("-test", "blah=bloo")

class TestAssignParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_assignment(self):
        obj = AssignParam.build({"name" : "test", "type" : str, "prefix":"--"})
        in_args             = ["--test=blah", "other"]
        match obj.consume(in_args):
            case {"test":"blah"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_assignment_wrong_prefix(self):
        obj = AssignParam.build({"name" : "test"})
        match obj.consume(["-t=blah"]):
            case None:
                assert(True)
            case x:
                assert(False), x

class TestWildCardParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_wildcard_assign(self):
        obj = WildcardParam()
        match obj.consume(["--blah=other"]):
            case {"blah":"other"}, 1:
                assert(True)
            case x:
                assert(False), x
