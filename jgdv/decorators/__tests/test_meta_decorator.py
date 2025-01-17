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
from jgdv.decorators.meta_decorator import MetaDecorator

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

class TestMetaDecorator(_TestUtils):

    @pytest.fixture(scope="function")
    def a_meta_dec(self):
        return MetaDecorator("example")

    def test_sanity(self):
        assert(True is True)

    def test_basic_init(self, a_meta_dec, dec):
        assert(isinstance(a_meta_dec, DecoratorBase))
        assert(issubclass(a_meta_dec.__class__, DecoratorBase))
        assert(a_meta_dec._data == ["example"])

    def test_basic_wrap_fn(self, a_meta_dec, a_fn):
        assert(not a_meta_dec.get_annotations(a_fn))
        wrapped = a_meta_dec(a_fn)
        assert(wrapped is not a_fn)
        assert(a_meta_dec.get_annotations(wrapped) == ["example"])

