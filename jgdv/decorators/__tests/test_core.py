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

class TestTargetTypeDiscrimination(_TestUtils):

    def test_sanity(self):
        assert(True is not False)

    def test_is_fn(self, dec, a_fn):
        assert(dec._target_type(a_fn) is _TargetType_e.FUNC)

    def test_is_instance_method(self, dec, a_class):
        inst = a_class()
        assert(dec._target_type(inst.simple) is _TargetType_e.METHOD)

    def test_is_method(self, dec, a_method):
        assert(dec._target_type(a_method) is _TargetType_e.METHOD)

    def test_is_class(self, dec, a_class):
        assert(dec._target_type(a_class) is _TargetType_e.CLASS)

    def test_decorated_fn_retains_correct_type(self):

        class Dec1(DecoratorBase):
            pass

        class Dec2(DecoratorBase):
            pass

        @Dec1()
        @Dec2()
        def testfn():
            pass

        assert(Dec1()._target_type(testfn) is _TargetType_e.FUNC)


    def test_decorated_method_retains_correct_type(self):

        class Dec1(DecoratorBase):
            pass

        class Dec2(DecoratorBase):
            pass

        class TestClass:
            @Dec1()
            @Dec2()
            def testfn(self):
                pass

        assert(Dec1()._target_type(TestClass.testfn) is _TargetType_e.METHOD)

class TestDecoratorBase(_TestUtils):

    def test_sanity(self):
        assert(True is True)

    def test_basic_init(self, dec):
        assert(dec._mark_key == f"{ANNOTATIONS_PREFIX}:{dec.__class__.__name__}")
        assert(dec._data_key == f"{ANNOTATIONS_PREFIX}:{DATA_SUFFIX}")

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_prefix(self, name):
        dec = DecoratorBase(prefix=name)
        assert(dec._mark_key == f"{name}:{dec.__class__.__name__}")
        assert(dec._data_key == f"{name}:{DATA_SUFFIX}")

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_mark(self, name):
        dec = DecoratorBase(mark=name)
        assert(dec._mark_key == f"{ANNOTATIONS_PREFIX}:{name}")
        assert(dec._data_key == f"{ANNOTATIONS_PREFIX}:{DATA_SUFFIX}")

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_data(self, name):
        dec = DecoratorBase(data=name)
        assert(dec._mark_key == f"{ANNOTATIONS_PREFIX}:{dec.__class__.__name__}")
        assert(dec._data_key == f"{ANNOTATIONS_PREFIX}:{name}")

    def test_mark_fn(self, dec, a_fn):
        assert(not dec._is_marked(a_fn))
        dec._apply_mark(a_fn)
        assert(dec._is_marked(a_fn))
        assert(dec._mark_key in a_fn.__dict__)
        assert(dec._data_key not in a_fn.__dict__)

    def test_mark_of_class_persists_to_instances(self, dec):

        class Basic:

            @dec
            def simple(self):
                pass

        instance = Basic()
        assert(dec._is_marked(Basic.simple))
        assert(dec._is_marked(instance.simple))
        assert(dec._mark_key in Basic.simple.__dict__)
        assert(dec._data_key in instance.simple.__dict__)

    def test_mark_of_class_survives_subclassing(self, dec):

        class Basic:

            @dec
            def simple(self):
                pass

        class BasicSub(Basic):
            pass

        instance = BasicSub()
        assert(dec._is_marked(Basic.simple))
        assert(dec._is_marked(instance.simple))
        assert(dec._mark_key in Basic.simple.__dict__)
        assert(dec._mark_key in BasicSub.simple.__dict__)
        assert(dec._data_key in instance.simple.__dict__)

    def test_no_annotations(self, dec, a_fn):
        assert(not bool(dec.get_annotations(a_fn)))
        assert(dec._mark_key not in a_fn.__dict__)
        assert(dec._data_key not in a_fn.__dict__)

    def test_unwrap_depth(self, dec):

        def simple():
            return 2

        assert(dec._unwrapped_depth(simple) == 0)
        w1 = ftz.update_wrapper(lambda fn: fn(), simple)
        assert(dec._unwrapped_depth(w1) == 1)
        w2 = ftz.update_wrapper(lambda fn: fn(), w1)
        assert(dec._unwrapped_depth(w2) == 2)
        w3 = ftz.update_wrapper(lambda fn: fn(), w2)
        assert(dec._unwrapped_depth(w3) == 3)

    def test_wrap_dict_update(self, dec, a_fn):
        assert(not dec._is_marked(a_fn))
        decorated = dec(a_fn)
        assert(dec._is_marked(a_fn))
        assert(decorated is not a_fn)

    def test_basic_wrap(self, dec, a_fn):
        assert(not dec._is_marked(a_fn))
        decorated = dec(a_fn)
        assert(dec._is_marked(a_fn))
        assert(decorated is not a_fn)

    def test_basic_wrap_idempotent(self, dec, a_fn):
        assert(not dec._is_marked(a_fn))
        d1 = dec(a_fn)
        d2 = dec(d1)
        assert(dec._is_marked(a_fn))
        assert(d1 is not a_fn)
        assert(d2 is not a_fn)
        assert(d2 is d1)
        assert(dec._unwrapped_depth(d1) == dec._unwrapped_depth(d2))

    def test_basic_unwrap(self, dec, a_fn):
        decorated = dec(a_fn)
        assert(decorated is not a_fn)
        unwrapped = dec._unwrap(decorated)
        assert(unwrapped is a_fn)
        assert(unwrapped is not decorated)

    def test_basic_wrap_fn_call(self, dec, a_fn, caplog):
        with caplog.at_level(logmod.DEBUG):
            assert("Calling Wrapped Fn" not in caplog.text)
            a_fn()
            assert("Calling Wrapped Fn" not in caplog.text)
            decorated = dec(a_fn)
            assert("Calling Wrapped Fn" not in caplog.text)
            decorated()
            assert("Calling Wrapped Fn" in caplog.text)

    def test_basic_wrap_method_call(self, dec, a_class, caplog):
        instance = a_class()
        with caplog.at_level(logmod.DEBUG):
            assert("Calling Wrapped Method" not in caplog.text)
            instance.simple()
            assert("Calling Wrapped Method" not in caplog.text)
            decorated = dec(a_class.simple)
            assert("Calling Wrapped Method" not in caplog.text)
            decorated(instance)
            assert("Calling Wrapped Method" in caplog.text)

