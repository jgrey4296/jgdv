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
from jgdv.structs.location.location_path import Location

logging = logmod.root

class TestLocationPath:

    def test_sanity(self):
        assert(True is True)

    def test_basic(self):
        val = Location("a/test")
        assert(isinstance(val, pl.Path))
        assert(hasattr(val, "__dict__"))
        assert(not val.exists())

    def test_basic_with_kwargs(self):
        val = Location("a/test", val="blah")
        assert(isinstance(val, pl.Path))
        assert(hasattr(val, "_meta"))
        assert(val._meta['val'] == 'blah')
