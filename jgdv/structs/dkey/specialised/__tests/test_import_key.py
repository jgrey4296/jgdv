#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast, Self, Final)
import warnings

import pytest

logging = logmod.root

from jgdv.structs.strang import CodeReference
from ... import DKey
from ..._interface import Key_p
from ..import_key import ImportDKey

IMP_KEY_BASES               : Final[list[str]]           = ["bob", "bill", "blah", "other", "23boo", "aweg2531", "awe_weg", "aweg-weji-joi"]
EXP_KEY_BASES               : Final[list[str]]           = [f"{{{x}}}" for x in IMP_KEY_BASES]
EXP_P_KEY_BASES             : Final[list[str]]           = ["{bob:wd}", "{bill:w}", "{blah:wi}", "{other:i}"]
PATH_KEYS                   : Final[list[str]]           = ["{bob}/{bill}", "{blah}/{bloo}", "{blah}/{bloo}"]
MUTI_KEYS                   : Final[list[str]]           = ["{bob}_{bill}", "{blah} <> {bloo}", "! {blah}! {bloo}!"]
IMP_IND_KEYS                : Final[list[str]]           = ["bob_", "bill_", "blah_", "other_"]
EXP_IND_KEYS                : Final[list[str]]           = [f"{{{x}}}" for x in IMP_IND_KEYS]

VALID_KEYS                                           = IMP_KEY_BASES + EXP_KEY_BASES + EXP_P_KEY_BASES + IMP_IND_KEYS + EXP_IND_KEYS
VALID_MULTI_KEYS                                     = PATH_KEYS + MUTI_KEYS

class TestImportKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_str_mark(self):
        assert(ImportDKey.MarkOf() is DKey.Marks.CODE)

    def test_basic(self):
        match DKey("fn", mark=DKey.Marks.CODE, implicit=True):
            case ImportDKey():
                assert(True)
            case x:
                 assert(False), x


    def test_expand(self):
        key = DKey("fn", mark=DKey.Marks.CODE, implicit=True)
        match key({"fn":"jgdv:identity_fn"}):
            case CodeReference() as x:
                iden = x()
                assert(callable(iden))
                assert(iden(2) == 2)
            case x:
                 assert(False), x


    def test_expand_annotated(self):
        key = DKey("fn", mark=DKey.Marks.CODE, implicit=True)
        match key({"fn":"fn::jgdv:identity_fn"}):
            case CodeReference() as x:
                assert(callable(x()))
                assert(x()(2) == 2)
                assert(True)
            case x:
                 assert(False), x


    def test_expand_redirect(self):
        key = DKey("fn", mark=DKey.Marks.CODE, implicit=True)
        match key({"fn_": "acceptor", "acceptor": "fn::jgdv:identity_fn"}):
            case CodeReference() as x:
                assert(callable(x()))
                assert(x()(2) == 2)
                assert(True)
            case x:
                 assert(False), x
