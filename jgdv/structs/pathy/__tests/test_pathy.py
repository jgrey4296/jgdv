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

from jgdv._types import *
from jgdv.structs.pathy import Pathy
import jgdv.structs.pathy.pathy as Ps

logging = logmod.root

class TestPathy:

    def test_sanity(self):
        assert(True is True)

    def test_basic(self):
        val : Pathy = Pathy("a/test")
        assert(isinstance(val, pl.Path))
        assert(hasattr(val, "__dict__"))
        assert(not val.exists())

    def test_basic_with_kwargs(self):
        val = Pathy("a/test", val="blah")
        assert(isinstance(val, pl.Path))
        assert(hasattr(val, "_meta"))
        assert(val._meta['val'] == 'blah')

    def test_pathy_file(self):
        val : Pathy['file'] = Pathy['file']("a/test.txt", val="blah")
        assert(val.pathy_type is Pathy.mark_e.File)
        assert(issubclass(Pathy['file'], Ps.PathyFile))
        assert(isinstance(val, Pathy['file']))
        assert(isinstance(val, Pathy))
        assert(isinstance(val, pl.Path))
        assert(hasattr(val, "_meta"))
        assert(val._meta['val'] == 'blah')


    def test_bad_annotation(self):
        with pytest.raises(ValueError):
            Pathy['blah']
