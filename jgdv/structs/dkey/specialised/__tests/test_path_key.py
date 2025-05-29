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

from jgdv.structs.locator import JGDVLocator
from ... import DKey, Key_p
from ..path_key import PathDKey

logging = logmod.root

IMP_KEY_BASES               : Final[list[str]]           = ["bob", "bill", "blah", "other", "23boo", "aweg2531", "awe_weg", "aweg-weji-joi"]
EXP_KEY_BASES               : Final[list[str]]           = [f"{{{x}}}" for x in IMP_KEY_BASES]
EXP_P_KEY_BASES             : Final[list[str]]           = ["{bob:wd}", "{bill:w}", "{blah:wi}", "{other:i}"]
PATH_KEYS                   : Final[list[str]]           = ["{bob}/{bill}", "{blah}/{bloo}", "{blah}/{bloo}"]
MUTI_KEYS                   : Final[list[str]]           = ["{bob}_{bill}", "{blah} <> {bloo}", "! {blah}! {bloo}!"]
IMP_IND_KEYS                : Final[list[str]]           = ["bob_", "bill_", "blah_", "other_"]
EXP_IND_KEYS                : Final[list[str]]           = [f"{{{x}}}" for x in IMP_IND_KEYS]

VALID_KEYS                                           = IMP_KEY_BASES + EXP_KEY_BASES + EXP_P_KEY_BASES + IMP_IND_KEYS + EXP_IND_KEYS
VALID_MULTI_KEYS                                     = PATH_KEYS + MUTI_KEYS

class TestPathKey:

    def test_mark(self):
        assert(PathDKey.MarkOf() is DKey.Marks.PATH)

    def test_expansion(self):
        key = DKey("test", mark=DKey.Marks.PATH, implicit=True)
        match key.expand({"test":"blah"}):
            case pl.Path() as x:
                assert(x == pl.Path.cwd() / "blah")
                assert(True)
            case x:
                 assert(False), x


    def test_expansion_fail(self):
        key = DKey("test", mark=DKey.Marks.PATH, implicit=True)
        match key.expand():
            case None:
                assert(True)
            case x:
                 assert(False), x


    def test_loc_expansion(self):
        locs = JGDVLocator(root=pl.Path.cwd())
        locs.update({"test":"blah"})
        key = DKey("test", mark=DKey.Marks.PATH, implicit=True)
        match key.expand(locs):
            case pl.Path() as x:
                assert(x == pl.Path.cwd() / "blah")
                assert(True)
            case x:
                 assert(False), x


    def test_loc_expansion_miss(self):
        locs = JGDVLocator(root=pl.Path.cwd())
        key = DKey("test", force=PathDKey, implicit=True)
        match key.expand(locs):
            case None:
                assert(True)
            case x:
                 assert(False), x


    @pytest.mark.skip
    def test_todo(self):
        pass
