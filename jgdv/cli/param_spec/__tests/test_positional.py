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

class TestPositionalSpecs:

    def test_consume_positional(self):
        obj = Specs.PositionalParam(**{"name":"test", "prefix":1, "type":str})
        assert(obj.positional)
        match obj.consume(["aweg", "blah"]):
            case {"test": "aweg"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_positional_list(self):
        obj = Specs.PositionalParam(**{
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
        obj = Specs.PositionalParam(**{"name":"test", "prefix":1, "type":str})
        assert(obj.positional)
        match obj.consume(["aweg", "blah"]):
            case {"test": "aweg"}, 1:
                assert(True)
            case x:
                assert(False), x

    def test_consume_positional_list(self):
        obj = Specs.PositionalParam(**{
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
