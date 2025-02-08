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

from jgdv.decorators.class_decorators import WithProto, Mixin
from jgdv.decorators.check_protocol import CheckProtocol
# ##-- end 1st party imports

logging = logmod.root

@runtime_checkable
class Proto_p(Protocol):

    def blah(self): ...

    def aweg(self): ...

class Simple_m:

    def blah(self):
        return 2

    def bloo(self):
        return 4

class Second_m:

    def aweg(self):
        return super(Second_m, self).bloo()

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

class TestMixinDecorator:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):

        @Mixin(Simple_m)
        class Example:

            def bloo(self):
                return 10

        obj = Example()
        assert(obj.blah() == 2)
        assert(obj.bloo() == 10)

    def test_two_mixins(self):

        @Mixin(Second_m, Simple_m)
        class Example:

            def bloo(self):
                return 10

        obj = Example()
        assert(obj.blah() == 2)
        assert(obj.bloo() == 10)
        # Aweg->super()->Simple_m.bloo
        assert(obj.aweg() == 4)

    def test_append_mixin(self):

        @Mixin(Second_m, append=[Simple_m])
        class Example:
            val : ClassVar[int] = 25

            def bloo(self):
                return 10

        obj = Example()
        assert(obj.blah() == 2)
        assert(obj.bloo() == 10)
        # Aweg->super()->Example.bloo
        assert(obj.aweg() == 10)
        assert(Example.val == 25)

class TestProtoDecorator:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_proto_no_check(self):

        @WithProto(Proto_p, check=False)
        class Example:
            val : ClassVar[int] = 25

            def bloo(self):
                return 10

        obj = Example()
        assert(isinstance(Example, Proto_p))
        assert(obj.bloo() == 10)
        assert(Example.val == 25)


    def test_proto_check_success(self):

        @WithProto(Proto_p, check=True)
        class Example:
            val : ClassVar[int] = 25

            def bloo(self):
                return 10
            
            def blah(self):
                return
            
            def aweg(self):
                return

        obj = Example()
        assert(isinstance(Example, Proto_p))
        assert(obj.bloo() == 10)
        assert(Example.val == 25)


    def test_proto_check_fail(self):

        with pytest.raises(NotImplementedError):
            @WithProto(Proto_p, check=True)
            class Example:
                val : ClassVar[int] = 25
    
                def bloo(self):
                    return 10


