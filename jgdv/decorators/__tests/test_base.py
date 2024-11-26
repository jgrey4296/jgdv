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
import functools as ftz
from jgdv.decorators import base
from jgdv.decorators.base import _TargetType_e, DecoratorBase, ANNOTATIONS_PREFIX, MARK_SUFFIX, DATA_SUFFIX

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

class TestDecoratorBase(_TestUtils):

    def test_sanity(self):
        assert(True is True)

    def test_basic_init(self, dec):
        assert(dec._mark_key == f"{ANNOTATIONS_PREFIX}:{MARK_SUFFIX}")
        assert(dec._data_key == f"{ANNOTATIONS_PREFIX}:{DATA_SUFFIX}")

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_prefix(self, name):
        dec = DecoratorBase(prefix=name)
        assert(dec._mark_key == f"{name}:{MARK_SUFFIX}")
        assert(dec._data_key == f"{name}:{DATA_SUFFIX}")

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_mark(self, name):
        dec = DecoratorBase(mark=name)
        assert(dec._mark_key == f"{ANNOTATIONS_PREFIX}:{name}")
        assert(dec._data_key == f"{ANNOTATIONS_PREFIX}:{DATA_SUFFIX}")

    @pytest.mark.parametrize("name", ["blah", "bloo", "blee"])
    def test_custom_data(self, name):
        dec = DecoratorBase(data=name)
        assert(dec._mark_key == f"{ANNOTATIONS_PREFIX}:{MARK_SUFFIX}")
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
        assert(dec._data_key not in instance.simple.__dict__)

    def test_no_annotations(self, dec, a_fn):
        assert(not bool(dec.get_annotations(a_fn)))
        assert(not dec._mark_key in a_fn.__dict__)
        assert(not dec._data_key in a_fn.__dict__)

    def test_unwrap_depth(self, dec):

        def simple():
            return 2

        assert(dec._unwrapped_depth(simple) == 0)
        w1 = ftz.update_wrapper(lambda fn: f(), simple)
        assert(dec._unwrapped_depth(w1) == 1)
        w2 = ftz.update_wrapper(lambda fn: f(), w1)
        assert(dec._unwrapped_depth(w2) == 2)
        w3 = ftz.update_wrapper(lambda fn: f(), w2)
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

class TestMetaDecorator(_TestUtils):

    @pytest.fixture(scope="function")
    def a_meta_dec(self):
        return base.MetaDecorator("example")

    def test_sanity(self):
        assert(True is True)

    def test_basic_init(self, a_meta_dec, dec):
        assert(isinstance(a_meta_dec, DecoratorBase))
        assert(issubclass(a_meta_dec.__class__, DecoratorBase))
        assert(a_meta_dec._data == "example")

    def test_basic_wrap_fn(self, a_meta_dec, a_fn):
        assert(not a_meta_dec.get_annotations(a_fn))
        wrapped = a_meta_dec(a_fn)
        assert(wrapped is not a_fn)
        assert(a_meta_dec.get_annotations(wrapped) == ["example"])

class TestDecoratorAccessorMixin(_TestUtils):

    @pytest.fixture(scope="function")
    def setup(self):
        pass

    @pytest.fixture(scope="function")
    def cleanup(self):
        pass

    def test_sanity(self):
        assert(True is True)

class TestDecorators(_TestUtils):

    def test_initial(self):
        """ check a simple annotation and wrap """

        @decs.DryRunSwitch()
        def simple(spec:dict, state:dict) -> str:
            return "blah"

        dec = decs.DryRunSwitch()
        assert(dec._is_marked(simple))
        assert(simple({}, {}) == "blah")

    def test_override_dry_run(self):
        """ check the wrapper works """

        @decs.DryRunSwitch(override=True)
        def simple(spec:dict, state:dict) -> str:
            return "blah"

        dec = decs.DryRunSwitch()
        assert(dec._is_marked(simple))
        assert(simple({}, {}) is None)

    def test_wrap_method(self):

        @decs.DryRunSwitch()
        class SimpleClass:

            def __call__(self, spec, state):
                return "blah"

        dec = decs.DryRunSwitch()
        # class is annotated
        assert(dec._is_marked(SimpleClass))
        # Instance is annotated
        assert(dec._is_marked(SimpleClass()))
        assert(SimpleClass()({}, {}) == "blah")

    def test_wrap_method_override_dry(self):

        @decs.DryRunSwitch(override=True)
        class SimpleClass:

            def __call__(self, spec, state):
                return "blah"

        dec = decs.DryRunSwitch()
        # class is annotated
        assert(dec._is_marked(SimpleClass))
        # Instance is annotated
        assert(dec._is_marked(SimpleClass()))
        assert(SimpleClass()({}, {}) is None)

    def test_annotate_fn(self):

        @decs.RunsDry()
        def simple(spec:dict, state:dict) -> str:
            return "blah"

        assert(DU.has_annotations(simple, doot.constants.decorations.RUN_DRY))

    def test_annotate_method(self):

        @decs.RunsDry()
        class SimpleClass:

            def __call__(self, spec:dict, state:dict) -> str:
                return "blah"

        assert(DU.has_annotations(SimpleClass, doot.constants.decorations.RUN_DRY))
        assert(DU.has_annotations(SimpleClass(), doot.constants.decorations.RUN_DRY))

    def test_annotation_survives_subclassing(self):

        @decs.RunsDry()
        class SimpleSuper:
            pass

        class SimpleChild(SimpleSuper):
            pass

        assert(DU.has_annotations(SimpleSuper,   decs.RUN_DRY))
        assert(DU.has_annotations(SimpleSuper(), decs.RUN_DRY))
        assert(DU.has_annotations(SimpleChild,   decs.RUN_DRY))
        assert(DU.has_annotations(SimpleChild(), decs.RUN_DRY))

    def test_key_decoration_survives_annotation(self):

        @decs.RunsDry()
        @DKeyed.formats("blah")
        def simple(spec, state, blah):
            return blah

        assert(DU.has_annotations(simple,   decs.RUN_DRY))
        assert(simple(None, {"blah":"bloo"}) == "bloo")

    def test_wrapper_survives_key_decoration(self):

        @decs.DryRunSwitch(override=True)
        @DKeyed.expands("blah")
        def simple(spec:dict, state:dict, blah:str) -> str:
            """ a simple test func """
            return blah

        dec = decs.DryRunSwitch()
        assert(dec._is_marked(simple))
        assert(simple(None, {"blah": "bloo"}) is None)

    def test_wrapper_survives_method_key_decoration(self):

        @decs.DryRunSwitch(override=True)
        class SimpleAction:

            @DKeyed.expands("blah")
            def __call__(self, spec:dict, state:dict, blah:str) -> str:
                """ a simple test func """
                return blah

        dec = decs.DryRunSwitch()
        assert(dec._is_marked(SimpleAction))
        assert(SimpleAction()({}, {"blah": "bloo"}) is None)

    def test_setting_dryswitch_on_method(self):

        class SimpleAction:

            @decs.DryRunSwitch(override=True)
            @DKeyed.expands("blah")
            def __call__(self, spec:dict, state:dict, blah:str) -> str:
                """ a simple test func """
                return blah

        dec = decs.DryRunSwitch()
        assert(dec._is_marked(SimpleAction.__call__))
        assert(dec._is_marked(SimpleAction))
        assert(SimpleAction()({}, {"blah": "bloo"}) is None)

    def test_wrapping_overriden_by_subclassing(self):

        @decs.DryRunSwitch(override=True)
        class SimpleSuper:

            def __call__(self, spec, state):
                return "blah"

        class SimpleChild(SimpleSuper):

            def __call__(self, spec, state):
                return "blah"

        dec = decs.DryRunSwitch()
        assert(dec._is_marked(SimpleSuper))
        assert(SimpleSuper()({}, {}) is None)
        assert(SimpleChild()({}, {}) == "blah")

    def test_gens_tasks(self):

        @decs.GeneratesTasks()
        def simple(spec, state):
            return []

        assert(DU.has_annotations(simple, decs.GEN_TASKS))
        assert(isinstance(simple({},{}), list))

    def test_gens_tasks_raises_error(self):

        @decs.GeneratesTasks()
        def simple(spec, state):
            return "blah"

        assert(DU.has_annotations(simple, decs.GEN_TASKS))
        with pytest.raises(doot.errors.DootActionError):
            simple({},{})

    @pytest.mark.xfail
    def test_io_writer_check(self, wrap_locs):
        """ check IOWriter guards locations """
        doot.locs.update({"blah" : dict(loc="blah", protected=True) })

        @decs.IOWriter()
        @DKeyed.paths("to")
        def simple(spec, state, to):
            return "blah"

        assert(DU.has_annotations(simple, decs.IO_ACT))
        with pytest.raises(doot.errors.DootTaskError):
            simple(None, {"to": "{blah}"})

    def test_io_writer_pas(self, wrap_locs):
        doot.locs.update({"blah" : dict(path="blah", protected=False) })

        @decs.IOWriter()
        @DKeyed.paths("to")
        def simple(spec, state, to):
            "a simple docstring "
            return "blah"

        assert(DU.has_annotations(simple, decs.IO_ACT))
        assert(simple(None, {"to": "{blah}"}) == "blah")
