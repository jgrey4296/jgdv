#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011, ARG002, ANN001
from __future__ import annotations

import enum
import logging as logmod
import pathlib as pl
from typing import (Any, ClassVar, Generic, TypeAlias, TypeVar, cast, TYPE_CHECKING)
from collections.abc import Mapping
import warnings
import pytest

from jgdv.structs.strang import CodeReference

from jgdv.structs import dkey
from .. import _interface as API # noqa: N812
from .._interface import Key_p, DKeyMark_e
from ..processor import DKeyProcessor
from ..dkey import DKey
from .. import keys
from .. import special

if TYPE_CHECKING:
    from collections.abc import Generator

logging = logmod.root

class TestDKey_Mark:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_mark(self):
        assert(isinstance(dkey.DKeyMark_e, enum.EnumMeta))

    def test_mark_aliases(self):
        assert("blah" not in dkey.DKeyMark_e)
        assert(dkey.DKeyMark_e.default() is Any)
        assert(dkey.DKeyMark_e.null() is False)
        assert(dkey.DKeyMark_e.multi() is list)
        assert(dkey.DKeyMark_e.indirect() is Mapping)

class TestDKey_Processor:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = DKeyProcessor()
        match obj.pre_process(dkey.DKey, "test", implicit=True):
            case "test", dict() as inst_data, dict(), type() as ctor:
                assert(API.RAWKEY_ID in inst_data)
                assert(len(inst_data[API.RAWKEY_ID]) == 1)
                assert(isinstance(ctor, API.Key_p))
                assert(ctor.MarkOf(ctor) == Any), ctor
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
                assert(DKey.MarkOf(ctor) == list), ctor
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
                assert(DKey.MarkOf(ctor) == False)
            case x:
                assert(False), x

class TestDKey_FormatParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_select_no_conversion(self):
        obj           = DKeyProcessor()
        default_ctor  = DKey._registry[DKey._default_k]
        match obj.pre_process(dkey.DKey, "test", implicit=True):
            case "test", dict(), dict(), type() as ctor:
                assert(ctor is default_ctor)
            case x:
                assert(False), x

    def test_select_strdkey(self):
        obj = DKeyProcessor()
        obj.register_convert_param(special.StrDKey, "s")
        match obj.pre_process(dkey.DKey, "test!s", implicit=True):
            case "test", dict(), dict(), type() as ctor:
                assert(ctor is special.StrDKey)
            case x:
                assert(False), x

    def test_select_indirect(self):
        obj = DKeyProcessor()
        obj.register_convert_param(keys.IndirectDKey, "I")
        match obj.pre_process(dkey.DKey, "test!I", implicit=True):
            case "test", dict(), dict(), type() as ctor:
                assert(ctor is keys.IndirectDKey)
            case x:
                assert(False), x

    def test_multikey_preprocess(self):
        obj = DKeyProcessor()
        obj.register_convert_param(keys.IndirectDKey, "I")
        obj.register_convert_param(special.StrDKey, "s")
        match obj.pre_process(dkey.DKey, "{test!I}} then {blah!s}"):
            case str(), dict(), dict(), type() as ctor:
                assert(ctor is keys.MultiDKey)
            case x:
                assert(False), x

    def test_multikey_build(self):
        obj = dkey.DKey("{test!I} then {blah!s}")
        assert(isinstance(obj, keys.MultiDKey))
        match obj.keys():
            case [keys.SingleDKey(), keys.SingleDKey()]:
                assert(True)
            case x:
                assert(False), x
