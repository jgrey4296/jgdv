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

    def test_join_file(self):
        obj = Pathy['dir']("a/b/c")
        obj2 = obj / Pathy['file']("test.txt")
        assert(isinstance(obj2, Pathy['file']))

    def test_join_file_str(self):
        obj = Pathy['dir']("a/b/c")
        obj2 = obj / "test.txt"
        assert(isinstance(obj2, Pathy['file']))

    def test_join_fail_on_file(self):
        obj = Pathy['file']("a/b/c/test.txt")
        with pytest.raises(ValueError):
            obj / "test.txt"

    def test_rjoin_for_str(self):
        obj = "a/b/c"
        obj2 = obj / Pathy("test")
        assert(isinstance(obj2, Pathy))
        assert(obj2 == "a/b/c/test")

    def test_call_expansion(self):
        obj    = Pathy("a/b/c")
        normed = obj()
        assert(isinstance(normed, pl.Path))
        assert(normed.is_absolute())

    def test_lt(self):
        obj  = Pathy("a/b/c")
        obj2 = Pathy("a/b/c/d/e")
        assert(obj < obj2)

    def test_contains_str(self):
        obj  = Pathy("a/b/c")
        assert("b" in obj)

    def test_contains_path(self):
        obj  = Pathy("a/b/c")
        sub  = pl.Path("b/c")
        assert(sub in obj)

    def test_format(self):
        obj  = Pathy("a/{b}/c")
        res  = obj.format(b="blah")
        assert(isinstance(res, Pathy))
        assert(res == "a/blah/c")


    def test_format_keep_filetype(self):
        obj  = Pathy['file']("a/{b}/c.txt")
        res  = obj.format(b="blah")
        assert(isinstance(res, Pathy['file']))
        assert(res == "a/blah/c.txt")
