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

from jgdv.structs.name.pydantic_struct_name import StructuredName as PydStrName
from jgdv.structs.name.str_struct_name import StructuredName as StrName

@pytest.mark.parametrize(["ctor"], [(PydStrName,), (StrName,)])
class TestStructuredName:
    """ Ensure basic functionality of structured names,
    but ensuring StrName is a str.
    """

    def test_sanity(self, ctor):
        assert(True is not False)
        assert(ctor is not None)

    def test_initial(self, ctor):
        obj = ctor.build("head:tail")
        assert(isinstance(obj, ctor))
        match ctor:
            case type() if ctor is PydStrName:
                assert(not isinstance(obj, str))
            case type() if ctor is StrName:
                assert(isinstance(obj, str))

    def test_build_fail(self, ctor):
        with pytest.raises(ValueError):
            ctor.build("head.tail")

    def test_head_str(self, ctor):
        obj = ctor.build("head.a.b.c:tail")
        assert(obj.head == ["head", "a", "b", "c"])
        assert(obj.head_str() == "head.a.b.c")

    def test_tail_str(self, ctor):
        obj = ctor.build("head:tail.a.b.c")
        assert(obj.tail == ["tail", "a", "b", "c"])
        assert(obj.tail_str() == "tail.a.b.c")

    def test_hash(self, ctor):
        obj = ctor.build("head:tail.a.b.c")
        obj2 = ctor.build("head:tail.a.b.c")
        assert(hash(obj) == hash(obj2))

    def test_lt(self, ctor):
        obj = ctor.build("head:tail.a.b.c")
        obj2 = ctor.build("head:tail.a.b.c.d")
        assert( obj < obj2 )

    def test_not_lt(self, ctor):
        obj = ctor.build("head:tail.a.b.d")
        obj2 = ctor.build("head:tail.a.b.c.d")
        assert(not obj < obj2 )

    def test_le_fail_on_self(self, ctor):
        obj = ctor.build("head:tail.a.b.c")
        obj2 = ctor.build("head:tail.a.b.c")
        assert(obj == obj2)
        assert(obj <= obj2 )

    def test_not_le(self, ctor):
        obj = ctor.build("head:tail.a.b.d")
        obj2 = ctor.build("head:tail.a.b.c")
        assert(not obj < obj2 )

    def test_contains(self, ctor):
        obj = ctor.build("head:tail.a.b.c")
        obj2 = ctor.build("head:tail.a.b.c.e")
        assert(obj2 in obj)

    def test_not_contains(self, ctor):
        obj = ctor.build("head:tail.a.b.c")
        obj2 = ctor.build("head:tail.a.b.c.e")
        assert(obj not in obj2)

    def test_bracket_access(self, ctor):
        simple = ctor.build("basic:tail..box[1]")
        assert(str(simple) == "basic:tail..box[1]")
