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
    Decorator,
    IdempotentDec,
    MonotonicDec,
    DForm_e,
)

from jgdv.decorators.proto import Proto
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

##--|

class GoodInheritAbsProto(AbsProto_p):

    def blah(self) -> None:
        pass

    def other(self):
        pass

class BadInheritAbsProto(AbsProto_p):
    pass

##--|

class GoodInheritRawProto(RawProto_p):

    def blah(self):
        return 10

    def aweg(self):
        return 10

class BadInheritRawProto(RawProto_p):

    def aweg(self):
        return 10

##--|

class GoodStructuralRawProto:

    def blah(self):
        return 10

    def aweg(self):
        return 10

class BadStructuralRawProto:

    def aweg(self):
        return 10

##-- end implementations

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

    def test_proto_on_type_alias(self):
        type proto_alias = RawProto_p

        @Proto(proto_alias, check=True)
        class Example:
            val : ClassVar[int] = 25

            def bloo(self):
                return 10

            def blah(self):
                return

            def aweg(self):
                return

        assert(True)

    def test_proto_on_protocol_fails(self):

        with pytest.raises(TypeError) as ctx:
            @Proto(RawProto_p)
            class Example(Protocol):
                pass

        match ctx.value:
            case TypeError(args=["Don't use @Proto to combine protocols, use normal inheritance", *_]):
                assert(True)
            case x:
                 assert(False), x


    def test_proto_annotations(self):
        assert(isinstance(GoodStructuralRawProto, RawProto_p))
        @Proto(RawProto_p)
        class Sub(GoodStructuralRawProto):
            pass

        match Proto.get(Sub):
            case [x] if x == RawProto_p:
                assert(True)
            case x:
                assert(False), x


    def test_proto_annotations_dont_travel_to_superclass(self):
        assert(isinstance(GoodStructuralRawProto, RawProto_p))
        @Proto(RawProto_p)
        class Sub(GoodStructuralRawProto):
            pass

        match Proto.get(GoodStructuralRawProto):
            case []:
                assert(True)
            case x:
                assert(False), x
class TestCheckProtocolClass:

    @pytest.fixture(scope="function")
    def proto(self):
        return Proto()

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_abs_class_success(self, proto):
        assert(issubclass(GoodAbsClass, AbsClass))
        proto.validate_protocols(GoodAbsClass)
        assert(True)

    def test_abs_class_fail(self, proto):
        assert(issubclass(BadAbsClass, AbsClass))
        with pytest.raises(NotImplementedError):
            proto.validate_protocols(BadAbsClass)

    def test_abs_proto_class_success(self, proto):
        assert(isinstance(GoodInheritAbsProto, AbsProto_p))
        proto.validate_protocols(GoodInheritAbsProto)
        assert(True)

    def test_abs_proto_class_fail(self, proto):
        assert(issubclass(BadInheritAbsProto, AbsProto_p))
        with pytest.raises(NotImplementedError):
            proto.validate_protocols(BadInheritAbsProto)
            assert(True)

    def test_raw_proto_class_success(self, proto):
        assert(isinstance(GoodInheritRawProto, RawProto_p))
        proto.validate_protocols(GoodInheritRawProto)
        assert(True)

    def test_raw_proto_class_fail(self, proto):
        assert(issubclass(BadInheritRawProto, RawProto_p))
        with pytest.raises(NotImplementedError):
            proto.validate_protocols(BadInheritRawProto)

    def test_raw_structural_proto_class_success(self):
        assert(isinstance(GoodStructuralRawProto, RawProto_p))
        assert(not RawProto_p in GoodStructuralRawProto.mro())

        @Proto(RawProto_p)
        class Sub(GoodStructuralRawProto):
            pass

        match Proto.get(Sub):
            case [x] if x == RawProto_p:
                assert(True)
            case x:
                assert(False), x

        match Proto.get(GoodStructuralRawProto):
            case []:
                assert(True)
            case x:
                assert(False), x

    def test_raw_structural_proto_class_fail(self):
        assert(not issubclass(BadStructuralRawProto, RawProto_p))
        assert(not isinstance(BadStructuralRawProto, RawProto_p))
        assert(not RawProto_p in BadStructuralRawProto.mro())
        with pytest.raises(NotImplementedError):
            Proto.validate_protocols(BadStructuralRawProto, RawProto_p)
            assert(True)


    @pytest.mark.parametrize("cls", [GoodStructuralRawProto])
    def test_get_protocols_empty(self, cls):
        match Proto.get(cls):
            case []:
                assert(True)
            case x:
                assert(False), x


    @pytest.mark.parametrize("cls", [GoodAbsClass, GoodInheritAbsProto, GoodInheritRawProto])
    def test_get_protocols(self, cls):
        match Proto.get(cls):
            case list() as xs if bool(xs):
                 assert(True)
            case x:
                 assert(False), (x, cls)

class TestGenericProtocolChecking:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_unparam_generic_proto_successs(self):

        @runtime_checkable
        class GenericProto_p[T](Protocol):
            pass

        @Proto(GenericProto_p)
        class Impl:
            pass

        assert(True)

    def test_param_generic_proto_success(self):

        @runtime_checkable
        class GenericProto_p[T](Protocol):
            pass

        @Proto(GenericProto_p[int])
        class Impl:
            pass

        assert(True)

    def test_aliased_param_generic_proto_success(self):

        @runtime_checkable
        class GenericProto_p[T](Protocol):
            pass

        type IntGenericProto_p = GenericProto_p[int]

        @Proto(IntGenericProto_p)
        class Impl:
            pass

        assert(True)

    def test_unparam_generic_proto_fail(self):

        @runtime_checkable
        class GenericProto_p[T](Protocol):

            def blah(self): ...

        with pytest.raises(NotImplementedError):

            @Proto(GenericProto_p)
            class Impl:
                pass

    def test_param_generic_proto_fail(self):

        @runtime_checkable
        class GenericProto_p[T](Protocol):

            def blah(self): ...

        with pytest.raises(NotImplementedError):

            @Proto(GenericProto_p[int])
            class Impl:
                pass

    def test_alias_param_generic_proto_fail(self):

        @runtime_checkable
        class GenericProto_p[T](Protocol):

            def blah(self): ...

        type IntGenProto_p = GenericProto_p[int]
        with pytest.raises(NotImplementedError):

            @Proto(IntGenProto_p)
            class Impl:
                pass
