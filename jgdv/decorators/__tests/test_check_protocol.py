#!/usr/bin/env python3
"""

"""
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
from jgdv.decorators.check_protocol import check_protocol, CheckProtocol

# ##-- end 1st party imports

logging = logmod.root

##-- example classes

class AbsClass(abc.ABC):

    @abc.abstractmethod
    def blah(self):
        pass

class GoodAbsClass(AbsClass):

    def blah(self):
        return 2

class BadAbsClass(AbsClass):
    pass

@runtime_checkable
class Proto_p(Protocol):

    def blah(self) -> None: ...


    @abc.abstractmethod
    def other(self):
        pass
class GoodProto(Proto_p):

    def blah(self) -> None:
        pass

    def other(self):
        pass

class BadProto(Proto_p):
    pass

##-- end example classes

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

class TestCheckProtocolClass(_TestUtils):

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

    def test_proto_class_success(self):
        assert(issubclass(GoodProto, Proto_p))
        dec = CheckProtocol()
        dec(GoodProto)
        assert(True)


    def test_proto_class_fail(self):
        assert(issubclass(BadProto, Proto_p))
        dec = CheckProtocol()
        with pytest.raises(NotImplementedError):
            dec(BadProto)
        assert(True)

class TestCheckProtocolFunc(_TestUtils):

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
