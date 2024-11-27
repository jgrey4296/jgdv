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

from jgdv.structs.name.strang import Strang

class TestStrang:
    """ Ensure basic functionality of structured names,
    but ensuring StrName is a str.
    """

    def test_sanity(self):
        assert(True is not False)
        assert(Strang is not None)

    def test_initial(self):
        obj = Strang("head:tail")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))

    def test_needs_separator(self):
        with pytest.raises(ValueError):
            Strang("head|tail")


    def test_needs_one_separator(self):
        with pytest.raises(ValueError):
            Strang("head::tail")

    def test_slices(self):
        obj = Strang("head.a.b.:tail.c.d.blah.bloo")
        assert(len(obj.group) == 3)
        assert(len(obj.body) == 5)

    def test_group_str(self):
        obj = Strang("head.a.blah.c:tail")
        assert(list(obj.group) == ["head", "a", "blah", "c"])
        assert(obj.sgroup == "head.a.blah.c")

    def test_body_str(self):
        obj = Strang("head:tail.a.blah.c")
        assert(list(obj.body) == ["tail", "a", "blah", "c"])
        assert(obj.sbody == "tail.a.blah.c")


    def test_empty_component(self):
        obj = Strang("head:tail..c")
        assert(list(obj.body) == ["tail", "", "c"])
        assert(obj.sbody == "tail..c")

class TestStrangCmp:

    def test_hash(self):
        obj = Strang("head:tail.a.b.c")
        obj2 = Strang("head:tail.a.b.c")
        assert(hash(obj) == hash(obj2))

    def test_lt(self):
        obj = Strang("head:tail.a.b.c")
        obj2 = Strang("head:tail.a.b.c.d")
        assert( obj < obj2 )

    def test_not_lt(self):
        obj  = Strang("head:tail.a.b.d")
        obj2 = Strang("head:tail.a.b.c.d")
        assert(not obj < obj2 )

    def test_le_fail_on_self(self):
        obj = Strang("head:tail.a.b.c")
        obj2 = Strang("head:tail.a.b.c")
        assert(obj == obj2)
        assert(obj <= obj2 )

    def test_not_le(self):
        obj = Strang("head:tail.a.b.d")
        obj2 = Strang("head:tail.a.b.c")
        assert(not obj < obj2 )

    def test_contains(self):
        obj  = Strang("head:tail.a.b.c")
        obj2 = Strang("head:tail.a.b.c.e")
        assert(obj2 in obj)

    def test_not_contains(self):
        obj = Strang("head:tail.a.b.c")
        obj2 = Strang("head:tail.a.b.c.e")
        assert(obj not in obj2)

class TestStrangAccess:

    def test_sanity(self):
        assert(True is not False)

    def test_iter(self):
        val = Strang("group.blah.awef:a.b.c")
        for x,y in zip(val, ["group", "blah", "awef", "a", "b","c"]):
            assert(x == y)

    def test_getitem(self):
        val = Strang("group.blah.awef:a.b.c")
        assert(val[0:0] == "group")
        assert(val[0:2] == "awef")
        assert(val[1:0] == "a")
        assert(val[1:2] == "c")
