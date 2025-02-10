#!/usr/bin/env python3
"""

"""
# ruff: noqa: B011
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import abc
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

from jgdv.decorators.class_decorators import Proto, Mixin, CheckProtocol, check_protocol
# ##-- end 1st party imports

logging = logmod.root

##-- protocols

class AbsClass(abc.ABC):
    """ An Abstract class with an explicit abstract method """

    @abc.abstractmethod
    def blah(self):
        pass

@runtime_checkable
class AbsProto_p(Protocol):
    """ A Protocol with an explicit abstract method """

    def blah(self) -> None: ...

    @abc.abstractmethod
    def other(self):
        pass

@runtime_checkable
class RawProto_p(Protocol):
    """ A Protocol with no additional anntoations """

    def blah(self): ...

    def aweg(self): ...

##-- end protocols

##-- implementations

class GoodAbsClass(AbsClass):

    def blah(self):
        return 2

class BadAbsClass(AbsClass):
    pass

class GoodInheritAbsProto(AbsProto_p):

    def blah(self) -> None:
        pass

    def other(self):
        pass

class BadInheritAbsProto(AbsProto_p):
    pass

class GoodInheritRawProto(RawProto_p):

    def blah(self):
        return 10

    def aweg(self):
        return 10

class BadInheritRawProto(RawProto_p):

    def aweg(self):
        return 10

class GoodStructuralRawProto:

    def blah(self):
        return 10

    def aweg(self):
        return 10

class BadStructuralRawProto:

    def aweg(self):
        return 10

##-- end implementations

##-- mixins

class Simple_m:

    def blah(self):
        return 2

    def bloo(self):
        return 4

class Second_m:

    def aweg(self):
        return super(Second_m, self).bloo()

##-- end mixins


class TestClassDecorator:

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

    def test_proto_no_check_no_error(self):

        @Proto(RawProto_p, check=False)
        class Example:
            """ doesn't implement the protocol, but is annotated with it """
            val : ClassVar[int] = 25

            def bloo(self):
                return 10

        obj = Example()
        assert(not isinstance(Example, RawProto_p))
        assert(obj.bloo() == 10)
        assert(Example.val == 25)
        match Proto.get(Example):
            case [x] if x is RawProto_p:
                assert(True)
            case x:
                 assert(False), x

    def test_proto_no_check(self):

        @Proto(RawProto_p, check=False)
        class Example:
            val : ClassVar[int] = 25

            def blah(self):
                return 10

            def aweg(self):
                return 10

        obj = Example()
        assert(isinstance(Example, RawProto_p))
        assert(obj.blah() == 10)
        assert(obj.aweg() == 10)
        assert(Example.val == 25)
        match Proto.get(Example):
            case [x] if x is RawProto_p:
                assert(True)
            case x:
                 assert(False), x

    def test_proto_check_success(self):

        @Proto(RawProto_p, check=True)
        class Example:
            val : ClassVar[int] = 25

            def bloo(self):
                return 10

            def blah(self):
                return

            def aweg(self):
                return

        obj = Example()
        assert(isinstance(Example, RawProto_p))
        assert(obj.bloo() == 10)
        assert(Example.val == 25)
        match Proto.get(Example):
            case [x] if x is RawProto_p:
                assert(True)
            case x:
                 assert(False), x


    def test_proto_check_fail(self):

        with pytest.raises(NotImplementedError):
            @Proto(RawProto_p, check=True)
            class Example:
                val : ClassVar[int] = 25

                def bloo(self):
                    return 10

class TestCheckProtocolClass:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_abs_class_success(self):
        assert(issubclass(GoodAbsClass, AbsClass))
        dec = CheckProtocol()
        dec(GoodAbsClass)
        assert(True)

    def test_abs_class_fail(self):
        assert(issubclass(BadAbsClass, AbsClass))
        dec = CheckProtocol()
        with pytest.raises(NotImplementedError):
            dec(BadAbsClass)

    def test_abs_proto_class_success(self):
        assert(isinstance(GoodInheritAbsProto, AbsProto_p))
        dec = CheckProtocol()
        dec(GoodInheritAbsProto)
        assert(True)

    def test_abs_proto_class_fail(self):
        assert(issubclass(BadInheritAbsProto, AbsProto_p))
        dec = CheckProtocol()
        with pytest.raises(NotImplementedError):
            dec(BadInheritAbsProto)
            assert(True)


    def test_raw_proto_class_success(self):
        assert(isinstance(GoodInheritRawProto, RawProto_p))
        dec = CheckProtocol()
        dec(GoodInheritRawProto)
        assert(True)

    def test_raw_proto_class_fail(self):
        assert(issubclass(BadInheritRawProto, RawProto_p))
        dec = CheckProtocol()
        with pytest.raises(NotImplementedError):
            dec(BadInheritRawProto)
            assert(True)

    def test_raw_structural_proto_class_success(self):
        assert(isinstance(GoodStructuralRawProto, RawProto_p))
        dec = CheckProtocol(RawProto_p)
        match dec(GoodStructuralRawProto):
            case None:
                assert(False)
            case _:
                assert(True)

        match Proto.get(GoodStructuralRawProto):
            case []:
                assert(True)
            case x:
                 assert(False), x



    def test_raw_structural_proto_class_fail(self):
        assert(not issubclass(BadStructuralRawProto, RawProto_p))
        assert(not isinstance(BadStructuralRawProto, RawProto_p))
        dec = CheckProtocol(RawProto_p)
        with pytest.raises(NotImplementedError):
            dec(BadStructuralRawProto)
            assert(True)

        match Proto.get(BadStructuralRawProto):
            case []:
                 assert(True)
            case x:
                 assert(False), x



class TestCheckProtocolFunc:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_abs_class_success(self):
        assert(issubclass(GoodAbsClass, AbsClass))
        check_protocol(GoodAbsClass)
        assert(True)

    def test_abs_class_fail(self):
        assert(issubclass(BadAbsClass, AbsClass))
        with pytest.raises(NotImplementedError):
            check_protocol(BadAbsClass)
