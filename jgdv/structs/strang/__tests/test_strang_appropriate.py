#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

import pytest
from jgdv.structs.strang import Strang, CodeReference
from jgdv.structs.strang.location import Location

logging = logmod.root

class TestBuildApprorpriate:

    def test_sanity(self):
        assert(True is True)

    def test_simple(self):
        obj = Strang.build("group::tail.a.b.c")
        assert(isinstance(obj, Strang))
        assert(not isinstance(obj, (CodeReference, Location)))


    def test_simple_coderef(self):
        obj = Strang.build("fn::tail.a.b.c:build_fn")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, CodeReference))
        assert(not isinstance(obj, Location))


    def test_simple_location(self):
        obj = Strang.build("file::a/b/c.txt")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, Location))
        assert(not isinstance(obj, CodeReference))
