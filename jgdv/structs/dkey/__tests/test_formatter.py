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

from jgdv.structs.dkey import DKey, MultiDKey, DKeyFormatter

class TestDKeyFormatterParsing:

    def test_parsing_doesnt_modify_string(self):
        val = "{bob}"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(bool(keys))
        assert(val == "{bob}")

    def test_parsing_prefix(self):
        val    = "--{bob}"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(has_text)
        assert(len(keys) == 1)

    def test_parsing_postfix(self):
        val = "{bob}--"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(has_text)
        assert(bool(keys))

    def test_parsing_internal_text(self):
        val = "{bob}--{bill}"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(has_text)
        assert(bool(keys))

    def test_parsing_no_text(self):
        val = "{bob}{bill}"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(not has_text)
        assert(bool(keys))

    def test_parsing_no_keys(self):
        val = "bob bill"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(has_text)
        assert(not bool(keys))

    def test_parsing_empty_str(self):
        val = ""
        has_text, keys = DKeyFormatter.Parse(val)
        assert(not has_text)
        assert(not bool(keys))

    def test_parsing_multi(self):
        val = "{bob} {bill}"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(len(keys) == 2)

    def test_parsing_format_params(self):
        val = "{bob:w} {bill:p}"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(len(keys) == 2)
        for x in keys:
            assert(x[2] in ["w", "p"])
            assert(x[3] == "")

    def test_parsing_conv_params(self):
        val = "{bob!w} {bill!p}"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(len(keys) == 2)
        for x in keys:
            assert(x[3] in ["w", "p"])
            assert(x[2] == "")

    def test_parsing_mixed_params(self):
        val = "{bob!a:w} {bill!b:p}"
        has_text, keys = DKeyFormatter.Parse(val)
        assert(len(keys) == 2)
        for x in keys:
            assert(x[3] in ["a", "b"])
            assert(x[2] in ["w", "p"])

class TestDKeyFormatter:

    def test_simple_format(self):
        fmt           = DKeyFormatter()
        result = fmt.format("test")
        assert(result == "test")

    def test_simple_key_replace(self):
        fmt           = DKeyFormatter()
        result = fmt.format("{test}", test="aweg")
        assert(result == "aweg")

    def test_simple_key_wrap(self):
        fmt           = DKeyFormatter()
        result = fmt.format("{test:w}", test="aweg")
        assert(result == "{aweg}")
