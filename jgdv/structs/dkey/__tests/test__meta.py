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
from jgdv._abstract.protocols import Key_p

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

class TestDKeyMetaSetup:

    @pytest.fixture(scope="function")
    def save_registry(self, mocker):
        single_reg = dkey.DKey._single_registry.copy()
        multi_reg  = dkey.DKey._multi_registry.copy()
        yield
        dkey.DKey._single_registry = single_reg
        dkey.DKey._multi_registry  = multi_reg

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

    def test_subclass_registration(self, save_registry):
        """ check creating a new dkey type is registered """
        assert(dkey.DKey.get_subtype(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)

        class PretendDKey(dkey.DKeyBase, mark=dkey.DKeyMark_e.FREE):
            pass

        assert(dkey.DKey.get_subtype(dkey.DKeyMark_e.FREE) == PretendDKey)

    def test_subclass_check(self):
        """ Check all registered dkeys are subclasses, or not-dkeys"""
        for x in dkey.DKey._single_registry.values():
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, dkey.DKeyBase))

        for m, x in dkey.DKey._multi_registry.items():
            if m is dkey.DKey.mark.NULL:
                continue
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, dkey.MultiDKey))

    def test_subclass_creation_fail(self):
        """ check you can't directly create a dkey subtype """
        with pytest.raises(RuntimeError):
            dkey.SingleDKey("test")

    def test_subclass_creation_force(self):
        """ Check you can force creation of a dkey subtype """
        key = dkey.DKey("test", implicit=True, force=dkey.SingleDKey)
        assert(key is not None)
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, dkey.SingleDKey))
