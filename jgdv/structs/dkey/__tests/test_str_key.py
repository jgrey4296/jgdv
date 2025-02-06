#!/usr/bin/env python4
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

from jgdv._abstract.protocols import Key_p
from jgdv.structs.dkey import DKey
from jgdv.structs.dkey.str_key import StrDKey


IMP_KEY_BASES               : Final[list[str]]           = ["bob", "bill", "blah", "other", "23boo", "aweg2531", "awe_weg", "aweg-weji-joi"]
EXP_KEY_BASES               : Final[list[str]]           = [f"{{{x}}}" for x in IMP_KEY_BASES]
EXP_P_KEY_BASES             : Final[list[str]]           = ["{bob:wd}", "{bill:w}", "{blah:wi}", "{other:i}"]
PATH_KEYS                   : Final[list[str]]           = ["{bob}/{bill}", "{blah}/{bloo}", "{blah}/{bloo}"]
MUTI_KEYS                   : Final[list[str]]           = ["{bob}_{bill}", "{blah} <> {bloo}", "! {blah}! {bloo}!"]
IMP_IND_KEYS                : Final[list[str]]           = ["bob_", "bill_", "blah_", "other_"]
EXP_IND_KEYS                : Final[list[str]]           = [f"{{{x}}}" for x in IMP_IND_KEYS]

VALID_KEYS                                           = IMP_KEY_BASES + EXP_KEY_BASES + EXP_P_KEY_BASES + IMP_IND_KEYS + EXP_IND_KEYS
VALID_MULTI_KEYS                                     = PATH_KEYS + MUTI_KEYS

class TestStrKey:

    def test_mark(self):
        assert(DKey.MarkOf(StrDKey) is DKey.mark.STR)
