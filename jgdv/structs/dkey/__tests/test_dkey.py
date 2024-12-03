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

logging = logmod.root

from tomlguard import TomlGuard
from jgdv.structs.strang import CodeReference

from jgdv.structs import dkey
from jgdv.structs.dkey.formatter import DKeyFormatter
from jgdv._abstract.protocols import Key_p

class TestDKeyMetaSetup:

    def test_sanity(self):
        key  = dkey.DKey("test", implicit=True)
        assert(isinstance(key, dkey.SingleDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(isinstance(key, Key_p))
        assert(f"{key:w}" == "{test}")
        assert(f"{key:i}" == "test_")
        assert(str(key) == "test")

    def test_subclass_registration(self):
        assert(dkey.DKey.get_initiator(dkey.DKeyMark_e.FREE) == dkey.SingleDKey)

        class PretendDKey(dkey.DKeyBase, mark=dkey.DKeyMark_e.FREE):
            pass
        assert(dkey.DKey.get_initiator(dkey.DKeyMark_e.FREE) == PretendDKey)
        # return the original class
        dkey.DKey.register_key(dkey.SingleDKey, dkey.DKeyMark_e.FREE)

    def test_subclass_check(self):
        for x in dkey.DKey._single_registry.values():
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, (dkey.SingleDKey, dkey.NonDKey)))

        for m, x in dkey.DKey._multi_registry.items():
            if m is dkey.DKey.mark.NULL:
                continue
            assert(issubclass(x, dkey.DKey))
            assert(issubclass(x, dkey.MultiDKey))

    def test_subclass_creation_fail(self):
        with pytest.raises(RuntimeError):
            dkey.SingleDKey("test")

    def test_subclass_creation_force(self):
        key = dkey.SingleDKey("test", force=True)
        assert(key is not None)
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, dkey.SingleDKey))
