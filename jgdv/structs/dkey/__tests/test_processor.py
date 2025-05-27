#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011, ARG002, ANN001
from __future__ import annotations

import enum
import logging as logmod
import pathlib as pl
from typing import (Any, ClassVar, Generic, TypeAlias, TypeVar, cast, TYPE_CHECKING)
import warnings

import pytest

logging = logmod.root

from jgdv.structs.strang import CodeReference

from jgdv.structs import dkey
from .. import _interface as API # noqa: N812
from .._interface import Key_p, DKeyMark_e
from ..processor import DKeyProcessor, DKeyRegistry
from ..dkey import DKey
from ..keys import SingleDKey

if TYPE_CHECKING:
    from collections.abc import Generator

@pytest.fixture(scope="function")
def save_registry(mocker) -> Generator:  # noqa: ARG001
    single_reg = DKey._processor.registry.single.copy()
    multi_reg  = DKey._processor.registry.multi.copy()
    yield
    DKey._processor.registry.single  = single_reg
    DKey._processor.registry.multi   = multi_reg

class TestDKeyMark:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_mark(self):
        assert(isinstance(dkey.DKeyMark_e, enum.EnumMeta))

    def test_other_mark(self):
        assert("free" in dkey.DKeyMark_e)
        assert("path" in dkey.DKeyMark_e)
        assert("indirect" in dkey.DKeyMark_e)
        assert("blah" not in dkey.DKeyMark_e)

    def test_mark_aliases(self):
        obj = DKeyProcessor()
        assert(obj.mark_alias(DKeyMark_e.FREE) is DKeyMark_e.FREE)

class TestDKeyProcessor:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = DKeyProcessor()
        match obj.pre_process(dkey.DKey, "test", implicit=True):
            case "test", dict() as inst_data, dict(), type() as ctor:
                assert(API.RAWKEY_ID in inst_data)
                assert(len(inst_data[API.RAWKEY_ID]) == 1)
                assert(isinstance(ctor, API.Key_p))
            case x:
                assert(False), x

    def test_basic_explicit(self):
        obj = DKeyProcessor()
        match obj.pre_process(dkey.DKey, "{test}"):
            case "test", dict() as inst_data, dict(), type() as ctor:
                assert(API.RAWKEY_ID in inst_data)
                assert(len(inst_data[API.RAWKEY_ID]) == 1)
                assert(isinstance(ctor, API.Key_p))
            case x:
                assert(False), x

    def test_multi_explicit(self):
        obj = DKeyProcessor()
        match obj.pre_process(dkey.DKey, "{test} mid {blah}"):
            case "{test} mid {blah}", dict() as inst_data, dict(), type() as ctor:
                assert(API.RAWKEY_ID in inst_data)
                assert(len(inst_data[API.RAWKEY_ID]) == 2)
                assert(isinstance(ctor, API.Key_p))
                assert(ctor.MarkOf() is API.DKeyMark_e.MULTI)
            case x:
                assert(False), x

    def test_basic_explicit_with_format_params(self):
        obj = DKeyProcessor()
        match obj.pre_process(dkey.DKey, "{test:w}"):
            case "test", dict() as inst_data, dict(), type() as ctor:
                assert(API.RAWKEY_ID in inst_data)
                assert(len(inst_data[API.RAWKEY_ID]) == 1)
                assert(inst_data[API.RAWKEY_ID][0].key == "test")
                assert(inst_data[API.RAWKEY_ID][0].prefix == "")
                assert(inst_data[API.RAWKEY_ID][0].format == "w")
                assert(isinstance(ctor, API.Key_p))
            case x:
                assert(False), x

    def test_null_key(self):
        obj = DKeyProcessor()
        match obj.pre_process(dkey.DKey, "test"):
            case "test", dict() as inst_data, dict(), type() as ctor:
                assert(API.RAWKEY_ID in inst_data)
                assert(len(inst_data[API.RAWKEY_ID]) == 1)
                assert(isinstance(ctor, API.Key_p))
                assert(ctor.MarkOf() is API.DKeyMark_e.NULL)
            case x:
                assert(False), x

class TestDKeyRegistry:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match DKeyRegistry():
            case DKeyRegistry():
                assert(True)
            case x:
                assert(False), x

    def test_basic_register(self):
        obj = DKeyRegistry()
        assert(not bool(obj.single))
        obj.register_key_type(SingleDKey, SingleDKey.MarkOf())
        assert(bool(obj.single))

    def test_get_subtype(self):
        obj = DKeyRegistry()
        obj.register_key_type(SingleDKey, SingleDKey.MarkOf())
        assert(bool(obj.single))
        match obj.get_subtype(SingleDKey.MarkOf()):
            case type() as x if x is SingleDKey:
                assert(True)
            case x:
                assert(False), x

class TestDKeySubclassing:

    def test_subclass_registration_conflict(self, save_registry):
        """ check you can't accidentally override an existing dkey mark type """
        assert(dkey.DKey._processor.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)

        with pytest.raises(ValueError):

            class PretendDKey(dkey.DKey, mark=dkey.DKeyMark_e.FREE):
                pass

        assert(dkey.DKey._processor.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)

    def test_subclass_override(self, save_registry):
        """ check creating a new dkey type is registered """
        assert(dkey.DKey._processor.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)

        class PretendDKey(dkey.SingleDKey, mark=dkey.DKeyMark_e.FREE):
            pass

        assert(dkey.DKey._processor.get_subtype(dkey.DKeyMark_e.FREE) == PretendDKey)

    def test_single_subclass_check(self, save_registry):
        """ Check all registered dkeys are subclasses"""
        assert(dkey.DKey._processor.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)
        for x in dkey.DKey._processor.registry.single.values():
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, dkey.DKey))
            assert(not issubclass(x, dkey.MultiDKey))

    def test_multi_subclass_check(self, save_registry):
        """ All multi keys must be instances of MultiKey_p """
        for m, x in dkey.DKey._processor.registry.multi.items():
            if m is dkey.DKey.Marks.NULL:
                continue
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, dkey.MultiDKey))
            assert(isinstance(x, API.MultiKey_p))

    def test_subclass_creation_force(self, save_registry):
        """ Check you can force creation of a dkey subtype """
        key = dkey.DKey("test", implicit=True, force=dkey.SingleDKey)
        assert(key is not None)
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, dkey.SingleDKey))

    def test_subclass_by_class_item(self, save_registry):
        """ check you can create new key subtypes """
        SimpleDKey = dkey.SingleDKey['simple']  # noqa: N806
        assert(issubclass(SimpleDKey, dkey.DKey))
        assert(issubclass(SimpleDKey, dkey.DKey))
        match dkey.DKey("blah", force=SimpleDKey):
            case SimpleDKey() as x:
                assert(x.MarkOf() == "simple")
                assert(x.MarkOf() == SimpleDKey.MarkOf())
                assert(x.MarkOf() != dkey.SingleDKey.MarkOf())
            case x:
                 assert(False), x

    def test_subclass_real_by_class_item(self, save_registry):
        """ check you can create new key subtypes """

        class AnotherSimpleDKey(dkey.SingleDKey['another']):
            __slots__ = ()
            pass

        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        match dkey.DKey("blah", force=AnotherSimpleDKey):
            case AnotherSimpleDKey() as x:
                assert(x.MarkOf() == "another")
            case x:
                 assert(False), x

    def test_subclass_non_base_by_class_item(self, save_registry):
        """ check you can create new key subtypes """

        class AnotherSimpleDKey(dkey.SingleDKey['another2']):
            __slots__ = ()
            pass

        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        assert(issubclass(AnotherSimpleDKey, dkey.SingleDKey))
        assert(dkey.DKey['another2'] is AnotherSimpleDKey)
        match dkey.DKey("blah", force=AnotherSimpleDKey):
            case AnotherSimpleDKey() as x:
                assert(x.MarkOf() == "another2")
                assert(True)
            case x:
                 assert(False), x


    def test_subclass_multi_key(self, save_registry):
        """ check you can create new key subtypes """
        class AnotherSimpleDKey(dkey.MultiDKey['another2']):
            __slots__ = ()
            pass

        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        assert(issubclass(AnotherSimpleDKey, dkey.MultiDKey))
        assert(dkey.MultiDKey['another2'] is AnotherSimpleDKey)
        assert(AnotherSimpleDKey not in dkey.DKey._processor.registry.single.values())
        match dkey.DKey("{blah}", mark='another2'):
            case AnotherSimpleDKey() as x:
                assert(x.MarkOf() == "another2")
                assert(True)
            case x:
                 assert(False), x
