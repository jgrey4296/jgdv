#!/usr/bin/env python3
"""

"""
# Imports
from __future__ import annotations

##-- stdlib imports
import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

##-- end stdlib imports

import pytest
from jgdv.mixins.annotate import SubAnnotate_m, SubRegistry_m

# Logging:
logging = logmod.root

# Global Vars:

class BasicEx(SubAnnotate_m):
    pass

class BasicSub(BasicEx):
    pass

class BasicTargeted(SubAnnotate_m, AnnotateTo="blah"):
    pass

##--|
class TestAnnotateMixin:

    def test_sanity(self):
        assert(True is True)

    def test_basic(self):
        obj = BasicEx[int]
        assert(issubclass(obj, BasicEx))
        assert(obj._get_annotation() is int)

    def test_subclass(self):
        obj = BasicSub[int]
        assert(issubclass(obj, BasicEx))
        assert(issubclass(obj, BasicSub))
        assert(obj._get_annotation() is int)

    def test_idempotent(self):
        obj = BasicSub[int]
        obj2 = BasicSub[int]
        assert(obj is obj2)

class TestAnnotateRegistry:

    def test_sanity(self):
        assert(True is not False)

    def test_registry(self):

        class BasicReg(SubRegistry_m):
            pass

        class BasicSubReg(BasicReg[int]):
            pass

        class BasicSubOther(BasicReg[float]):
            pass

        assert(BasicReg[int] is BasicSubReg)
        assert(BasicReg[float] is not BasicReg[int])
        assert(int in BasicReg._registry)
        assert(BasicReg._registry is BasicSubReg._registry)
