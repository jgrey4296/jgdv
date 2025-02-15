#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import enum
import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

import pytest

logging = logmod.root

from jgdv.structs.strang import CodeReference

from jgdv.structs import dkey
from jgdv.structs.dkey._meta import DKeyMeta
from jgdv._abstract.protocols import Key_p

@pytest.fixture(scope="function")
def save_registry(mocker):
    single_reg = DKeyMeta._single_registry.copy()
    multi_reg  = DKeyMeta._multi_registry.copy()
    yield
    DKeyMeta._single_registry = single_reg
    DKeyMeta._multi_registry  = multi_reg


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

class TestDKeyMeta:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_implicit(self):
        key  = dkey.DKey("test", implicit=True)
        assert(isinstance(key, dkey.SingleDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(isinstance(key, Key_p))
        assert(f"{key:w}" == "{test}")
        assert(f"{key:i}" == "test_")
        assert(str(key)   == "test")

    def test_basic_explicit(self):
        key  = dkey.DKey("{test}")
        assert(isinstance(key, dkey.SingleDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(isinstance(key, Key_p))
        assert(f"{key:w}" == "{test}")
        assert(f"{key:i}" == "test_")
        assert(str(key)   == "test")

    def test_basic_explicit_with_format_params(self):
        key  = dkey.DKey("{test:w}")
        assert(isinstance(key, dkey.SingleDKey))
        assert(key._fmt_params == "w")
        assert(f"{key:w}" == "{test}")
        assert(f"{key:i}" == "test_")
        assert(str(key)   == "test")

    def test_null_key(self):
        key  = dkey.DKey("test")
        assert(isinstance(key, dkey.NonDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(isinstance(key, Key_p))
        assert(dkey.DKey.MarkOf(key) is dkey.DKeyMark_e.NULL)
        assert(f"{key:w}" == "test")
        assert(f"{key:i}" == "test")
        assert(str(key)   == "test")

    def test_multi_key(self):
        key  = dkey.DKey("{test} {blah}")
        assert(isinstance(key, dkey.MultiDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(isinstance(key, Key_p))
        assert(dkey.DKey.MarkOf(key) is dkey.DKeyMark_e.MULTI)
        assert(f"{key:w}" == "{test} {blah}")
        assert(f"{key:i}" == "{test} {blah}")
        assert(str(key)   == "{test} {blah}")

    def test_mark_conflict(self):
        with pytest.raises(ValueError):
             dkey.DKey("{blah!p}", mark=dkey.DKey.Mark.CODE)


    def test_isntance_check(self):
        assert(isinstance(dkey.SingleDKey, dkey.DKey))


    def test_error_on_bad_kwargs(self):
        with pytest.raises(ValueError):
            dkey.DKey("blah", unexpected=True)

class TestDKeySubclassing:

    def test_subclass_registration_conflict(self, save_registry):
        """ check creating a new dkey type is registered """
        assert(dkey.DKey.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)

        with pytest.raises(ValueError):
            class PretendDKey(dkey.DKeyBase, mark=dkey.DKeyMark_e.FREE):
                pass

        assert(dkey.DKey.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)

    def test_subclass_override(self, save_registry):
        """ check creating a new dkey type is registered """
        assert(dkey.DKey.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)

        class PretendDKey(dkey.SingleDKey, mark=dkey.DKeyMark_e.FREE):
            pass

        assert(dkey.DKey.get_subtype(dkey.DKeyMark_e.FREE) == PretendDKey)

    def test_single_subclass_check(self, save_registry):
        """ Check all registered dkeys are subclasses, or not-dkeys"""
        assert(dkey.DKey.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)
        for x in dkey.DKey._single_registry.values():
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, dkey.DKeyBase))
            assert(not issubclass(x, dkey.MultiDKey))

    def test_multi_subclass_check(self, save_registry):
        for m, x in dkey.DKey._multi_registry.items():
            if m is dkey.DKey.Mark.NULL:
                continue
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, dkey.DKeyBase))
            assert(issubclass(x, dkey.MultiDKey))

    def test_subclass_creation_fail(self, save_registry):
        """ check you can't directly create a dkey subtype """
        with pytest.raises(RuntimeError):
            dkey.SingleDKey("test")

    def test_subclass_creation_force(self, save_registry):
        """ Check you can force creation of a dkey subtype """
        key = dkey.DKey("test", implicit=True, force=dkey.SingleDKey)
        assert(key is not None)
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, dkey.SingleDKey))

    def test_subclass_by_class_item(self, save_registry):
        """ check you can create new key subtypes """
        SimpleDKey = dkey.SingleDKey['simple']
        assert(issubclass(SimpleDKey, dkey.DKey))
        assert(issubclass(SimpleDKey, dkey.DKeyBase))
        match dkey.DKey("blah", force=SimpleDKey):
            case SimpleDKey() as x:
                assert(dkey.DKey.MarkOf(x) == "simple")
                assert(True)
            case x:
                 assert(False), x

    def test_subclass_real_by_class_item(self, save_registry):
        """ check you can create new key subtypes """

        class AnotherSimpleDKey(dkey.SingleDKey['another']):
            pass

        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        assert(issubclass(AnotherSimpleDKey, dkey.DKeyBase))
        match dkey.DKey("blah", force=AnotherSimpleDKey):
            case AnotherSimpleDKey() as x:
                assert(dkey.DKey.MarkOf(x) == "another")
                assert(True)
            case x:
                 assert(False), x

    def test_subclass_non_base_by_class_item(self, save_registry):
        """ check you can create new key subtypes """

        class AnotherSimpleDKey(dkey.SingleDKey['another2']):
            pass

        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        assert(issubclass(AnotherSimpleDKey, dkey.DKeyBase))
        assert(issubclass(AnotherSimpleDKey, dkey.SingleDKey))
        assert(dkey.DKey['another2'] is AnotherSimpleDKey)
        match dkey.DKey("blah", force=AnotherSimpleDKey):
            case AnotherSimpleDKey() as x:
                assert(dkey.DKey.MarkOf(x) == "another2")
                assert(True)
            case x:
                 assert(False), x


    def test_subclass_multi_key(self, save_registry):
        """ check you can create new key subtypes """
        class AnotherSimpleDKey(dkey.MultiDKey['another2']):
            pass

        assert(issubclass(AnotherSimpleDKey, dkey.DKey))
        assert(issubclass(AnotherSimpleDKey, dkey.DKeyBase))
        assert(issubclass(AnotherSimpleDKey, dkey.MultiDKey))
        assert(dkey.DKey['another2'] is AnotherSimpleDKey)
        assert(AnotherSimpleDKey not in DKeyMeta._single_registry.values())
        match dkey.DKey("blah", force=AnotherSimpleDKey):
            case AnotherSimpleDKey() as x:
                assert(dkey.DKey.MarkOf(x) == "another2")
                assert(True)
            case x:
                 assert(False), x
