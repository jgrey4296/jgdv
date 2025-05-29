#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, ANN001, B011, ANN204, ANN002, ANN003
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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest

# ##-- end 3rd party imports

# ##-- 1st party imports
from .. import _interface as API  # noqa: N812
from .._core import (
    Decorator,
    MonotonicDec,
    IdempotentDec,
    MetaDec,
    DataDec,
)

# ##-- end 1st party imports

class _Utils:

    @pytest.fixture(scope="function")
    def dec(self): # type: ignore
        return Decorator()

    @pytest.fixture(scope="function")
    def mdec(self):

        class MDec(MonotonicDec):
            pass

        return MDec()

    @pytest.fixture(scope="function")
    def idec(self):
        return IdempotentDec()

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

##--|

class TestDFormDiscrimination(_Utils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_is_fn(self, dec, a_fn):
        match dec._discrim_form(a_fn):
            case API.DForm_e.FUNC:
                assert(True)
            case x:
                assert(False), x

    def test_is_instance_method(self, dec, a_class):
        inst = a_class()
        match dec._discrim_form(inst.simple):
            case API.DForm_e.METHOD:
                assert(True)
            case x:
                assert(False), x

    def test_is_method(self, dec, a_method):
        match dec._discrim_form(a_method):
            case API.DForm_e.METHOD:
                assert(True)
            case x:
                assert(False), x

    def test_is_class(self, dec, a_class):
        match dec._discrim_form(a_class):
            case API.DForm_e.CLASS:
                assert(True)
            case x:
                assert(False), x

    def test_instance(self, dec, a_class):
        with pytest.raises(TypeError):
            dec._discrim_form(a_class())

class TestDecorator(_Utils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_init(self, dec):
        mark = f"{API.ANNOTATIONS_PREFIX}:{dec.__class__.__name__}"
        data = f"{API.ANNOTATIONS_PREFIX}:{API.DATA_SUFFIX}"
        assert(dec.mark_key() == mark)
        assert(dec.data_key() == data)

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_prefix(self, name):
        dec = Decorator(prefix=name)
        assert(dec.mark_key() == f"{name}:{dec.__class__.__name__}")
        assert(dec.data_key() == f"{name}:{API.DATA_SUFFIX}")

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_mark(self, name):
        dec = Decorator(mark=name)
        assert(dec.mark_key() == f"{API.ANNOTATIONS_PREFIX}:{name}")
        assert(dec.data_key() == f"{API.ANNOTATIONS_PREFIX}:{API.DATA_SUFFIX}")

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_data(self, name):
        dec = Decorator(data=name)
        assert(dec.mark_key() == f"{API.ANNOTATIONS_PREFIX}:{dec.__class__.__name__}")
        assert(dec.data_key() == f"{API.ANNOTATIONS_PREFIX}:{name}")


    def test_decorating_without_instantiation(self):

        class SimpleDec(Decorator):

            def __init__(self, extra=None):
                super().__init__()
                self._extra = extra or []

            def __call__(self, target):
                def simple_wrapped(*args, **kwargs):
                    return [*target(*args, **kwargs), 2, *self._extra]

                return simple_wrapped

        @SimpleDec()
        def test_fn():
            return [1]

        assert(test_fn() == [1,2])


    def test_decorating_with_instantiation(self):

        class SimpleDec(Decorator):

            def __init__(self, extra=None):
                super().__init__()
                self._extra = extra or []

            def __call__(self, target):
                def simple_wrapped(*args, **kwargs):
                    return [*target(*args, **kwargs), 2, *self._extra]

                return simple_wrapped

        @SimpleDec(extra=[3,4,5])
        def test_fn():
            return [1]

        assert(test_fn() == [1, 2, 3, 4, 5])


class TestMarking(_Utils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_mark_fn(self, dec, a_fn):
        assert(not dec.is_marked(a_fn))
        dec.apply_mark(a_fn)
        assert(dec.is_marked(a_fn))
        assert(dec._mark_key in a_fn.__annotations__)
        assert(dec._data_key not in a_fn.__annotations__)

    def test_mark_method(self, a_class, dec):
        assert(not dec.is_marked(a_class))
        assert(not dec.is_marked(a_class.simple))
        dec.apply_mark(a_class.simple)
        assert(dec.is_marked(a_class.simple))

    def test_mark_method_doesnt_mark_class(self, a_class, dec):
        assert(not dec.is_marked(a_class))
        assert(not dec.is_marked(a_class.simple))
        dec.apply_mark(a_class.simple)
        assert(dec.is_marked(a_class.simple))
        assert(not dec.is_marked(a_class))

    def test_mark_method_survives_instantiation(self, a_class, dec):
        assert(not dec.is_marked(a_class))
        assert(not dec.is_marked(a_class.simple))
        dec.apply_mark(a_class.simple)
        obj = a_class()
        assert(dec.is_marked(obj.simple))

    def test_mark_method_survives_subclassing(self, a_class, dec):
        assert(not dec.is_marked(a_class))
        assert(not dec.is_marked(a_class.simple))
        dec.apply_mark(a_class.simple)
        assert(dec.is_marked(a_class.simple))

        class BasicSub(a_class):
            pass

        assert(dec.is_marked(BasicSub.simple))

    def test_mark_class(self, a_class, dec):
        assert(not dec.is_marked(a_class))
        dec.apply_mark(a_class)
        assert(dec.is_marked(a_class))

    def test_mark_class_survives_instantiation(self, a_class, dec):
        assert(not dec.is_marked(a_class))
        dec.apply_mark(a_class)
        assert(dec.is_marked(a_class))
        obj = a_class()
        assert(dec.is_marked(obj))

class TestAnnotation(_Utils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_fn_is_not_annotated(self, dec, a_fn):
        assert(not dec.is_annotated(a_fn))

    def test_method_is_not_annotated_(self, dec, a_method):
        assert(not dec.is_annotated(a_method))

    def test_class_is_not_annotated(self, dec, a_class):
        assert(not dec.is_annotated(a_class))

    def test_instance_is_not_annotated(self, dec, a_class):
        obj = a_class()
        assert(not dec.is_annotated(obj))

class TestWrapping(_Utils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_fn_unwrap_default(self, mdec, a_fn):
        assert(not mdec.is_marked(a_fn))
        unwrapped = mdec._unwrap(a_fn)
        assert(unwrapped is a_fn)

    def test_method_unwrap_default(self, mdec, a_method):
        assert(not mdec.is_marked(a_method))
        unwrapped = mdec._unwrap(a_method)
        assert(unwrapped is a_method)

    def test_class_unwrap_default(self, mdec, a_class):
        assert(not mdec.is_marked(a_class))
        unwrapped = mdec._unwrap(a_class)
        assert(unwrapped is a_class)

    def test_fn_wrap(self, mdec, a_fn):
        assert(not mdec.is_marked(a_fn))
        decorated = mdec(a_fn)
        assert(decorated is not a_fn)

    def test_fn_unwrap(self, mdec, a_fn):
        assert(not mdec.is_marked(a_fn))
        decorated = mdec(a_fn)
        unwrapped = mdec._unwrap(decorated)
        assert(unwrapped is a_fn)
        assert(unwrapped is not decorated)

    def test_method_wrap(self, mdec, a_method):
        assert(not mdec.is_marked(a_method))
        decorated = mdec(a_method)
        assert(decorated is not a_method)
        assert(mdec.is_marked(a_method))
        assert(mdec.is_marked(decorated))

    def test_method_unwrap(self, mdec, a_method):
        assert(not mdec.is_marked(a_method))
        decorated = mdec(a_method)
        unwrapped = mdec._unwrap(decorated)
        assert(unwrapped is a_method)
        assert(unwrapped is not decorated)

    def test_class_wrap(self, mdec, a_class):
        assert(not mdec.is_marked(a_class))
        decorated = mdec(a_class)
        assert(decorated is not a_class)
        assert(mdec.is_marked(a_class))
        assert(mdec.is_marked(decorated))

    def test_class_unwrap(self, mdec, a_class):
        assert(not mdec.is_marked(a_class))
        decorated = mdec(a_class)
        unwrapped = mdec._unwrap(decorated)
        assert(unwrapped is not a_class)
        assert(unwrapped is decorated)

    def test_unwrap_depth_simple(self, dec):

        def simple():
            return 2

        assert(dec._unwrapped_depth(simple) == 0)
        w1 = ftz.update_wrapper(lambda fn: fn(), simple)
        assert(dec._unwrapped_depth(w1) == 1)
        w2 = ftz.update_wrapper(lambda fn: fn(), w1)
        assert(dec._unwrapped_depth(w2) == 2)
        w3 = ftz.update_wrapper(lambda fn: fn(), w2)
        assert(dec._unwrapped_depth(w3) == 3)

##--|

class TestIdempotent(_Utils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_mark_of_class_persists_to_instances(self, idec):
        class Basic:

            @idec
            def simple(self):
                pass

        instance = Basic()
        assert(idec.is_marked(Basic.simple))
        assert(idec.is_marked(instance.simple))
        assert(not idec.is_annotated(Basic.simple))
        assert(not idec.is_annotated(instance.simple))

    def test_fn_wrap_idempotent(self, idec, a_fn):
        assert(not idec.is_marked(a_fn))
        d1 = idec(a_fn)
        d2 = idec(d1)
        assert(d1 is not a_fn)
        assert(d2 is not a_fn)
        assert(d2 is d1)
        assert(idec.is_marked(a_fn))
        assert(idec.is_marked(d1))
        assert(idec.is_marked(d2))
        assert(idec._unwrapped_depth(d1) == idec._unwrapped_depth(d2))

    def test_doesnt_annotate(self, idec):
        assert(not bool(idec._build_annotations_h(None, [])))

class TestMonotonic(_Utils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_mark_of_class_persists_to_instances(self, mdec):

        class Basic:

            @mdec
            def simple(self):
                pass

        instance = Basic()
        assert(mdec.is_marked(Basic.simple))
        assert(mdec.is_marked(instance.simple))
        assert(mdec._mark_key in Basic.simple.__annotations__)

    def test_fn_retains_correct_type(self):

        class Dec1(MonotonicDec):
            pass

        class Dec2(MonotonicDec):
            pass

        @Dec1()
        @Dec2()
        def testfn():
            pass

        match Dec1()._discrim_form(testfn):
            case API.DForm_e.FUNC:
                assert(True)
            case x:
                assert(False), x

    def test_method_retains_correct_type(self):

        class Dec1(MonotonicDec):
            pass

        class Dec2(MonotonicDec):
            pass

        class TestClass:

            @Dec1()
            @Dec2()
            def testfn(self):
                pass

        match Dec1()._discrim_form(TestClass.testfn):
            case API.DForm_e.METHOD:
                assert(True)
            case x:
                assert(False), x

class TestMetaDecorator(_Utils):

    @pytest.fixture(scope="function")
    def a_meta_dec(self):
        return MetaDec("example")

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_init(self, a_meta_dec, dec):
        assert(isinstance(a_meta_dec, Decorator))
        assert(issubclass(a_meta_dec.__class__, Decorator))
        assert(a_meta_dec._data == ["example"])

    def test_basic_wrap_fn(self, a_meta_dec, a_fn):
        assert(not a_meta_dec.is_annotated(a_fn))
        wrapped = a_meta_dec(a_fn)
        assert(wrapped is a_fn)
        assert(a_meta_dec.get_annotations(wrapped) == ["example"])

class TestDataDecorator(_Utils):

    @pytest.fixture(scope="function")
    def ddec(self):
        return DataDec("aval")

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self, ddec, a_fn):
        wrapped = ddec(a_fn)
        assert(bool(ddec._build_annotations_h(None, [])))
        assert(ddec.get_annotations(wrapped) == ["aval"])

class TestClassDecoration(_Utils):

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_add_new_method(self):
        """ Modify the decorated class"""
        class ExDecorator(IdempotentDec):

            def bmethod(self, val):
                return val + self._val

            def _wrap_class_h(self, target:type):
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
