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
from ..annotate import SubAnnotate_m, SubRegistry_m, Subclasser

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

class TestSubClasser:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_decorate_name_noop(self):
        target = BasicEx.__name__
        match Subclasser.decorate_name(BasicEx):
            case str() as x if x == target:
                assert(True)
            case x:
                 assert(False), x

    def test_decorate_name_with_extras(self):
        target = f"{BasicEx.__name__}<+test>"
        match Subclasser.decorate_name(BasicEx, "test"):
            case str() as x if x == target:
                assert(True)
            case x:
                 assert(False), x

    def test_redecorate_name_with_extras(self):
        target = f"{BasicEx.__name__}<+test>"
        curr = BasicEx.__name__
        for i in range(10):
            curr = Subclasser.decorate_name(curr, "test")
            assert(curr == target)


    def test_multi_decorate(self):
        target = f"{BasicEx.__name__}<+blah+test>"
        curr = BasicEx.__name__
        for i in range(10):
            curr = Subclasser.decorate_name(curr, "test", "blah")
            assert(curr == target)


    def test_decorate_param(self):
        target = f"{BasicEx.__name__}[bool]"
        curr = BasicEx.__name__
        for i in range(10):
            curr = Subclasser.decorate_name(curr, params="bool")
            assert(curr == target)


    def test_decorate_name_override_param(self):
        target = f"{BasicEx.__name__}[int]"
        curr = Subclasser.decorate_name(BasicEx.__name__, params="bool")
        over = Subclasser.decorate_name(BasicEx.__name__, params="int")
        assert(over == target)


    def test_decorate_extras_and_params(self):
        target = f"{BasicEx.__name__}<+test>[int]"
        curr = Subclasser.decorate_name(BasicEx.__name__, "test", params="int")
        assert(curr == target)
