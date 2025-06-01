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
from .. import keys

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
                assert(DKey.MarkOf(ctor) == API.DKeyMark_e.MULTI)
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
                assert(DKey.MarkOf(ctor) == API.DKeyMark_e.NULL)
            case x:
                assert(False), x

