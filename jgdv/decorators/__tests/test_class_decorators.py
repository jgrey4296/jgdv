#!/usr/bin/env python3
"""

"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv.decorators.core import (
    ANNOTATIONS_PREFIX,
    DATA_SUFFIX,
    MARK_SUFFIX,
    DecoratorBase,
    _TargetType_e,
)

# ##-- end 1st party imports

logging = logmod.root

class _TestUtils:

    @pytest.fixture(scope="function")
    def dec(self):
        return DecoratorBase()

    @pytest.fixture(scope="function")
    def a_class(self):

        class Basic:

            def simple(self):
                return 2

        return Basic

    @pytest.fixture(scope="function")
    def a_method(self):

        class Basic:

            def simple(self):
                return 2

        return Basic.simple

    @pytest.fixture(scope="function")
    def a_fn(self):

        def simple():
            return 2

        return simple

class TestClassDecorator(_TestUtils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_annotation(self):

        class ExDecorator(DecoratorBase):

            def add_annotations(self, fn, ttype:_TargetType_e):
                setattr(fn, "jgtest", True) # noqa: B010

        @ExDecorator()
        class Basic:
            pass

        assert(Basic.jgtest)
        assert(Basic().jgtest)

    def test_add_new_method(self):

        class ExDecorator(DecoratorBase):

            def bmethod(self, val):
                return val + self._val

            def _mod_class(self, target):
                # Gets the unbound method and binds it to the target
                setattr(target, "bmethod", self.__class__.bmethod) # noqa: B010

        @ExDecorator()
        class Basic:

            def __init__(self, val=None):
                self._val = val or 2

            def amethod(self):
                return 2

        inst = Basic()
        assert(inst.amethod() == 2)
        assert(inst.bmethod(2) == 4)
