#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011
from __future__ import annotations

import uuid
import logging as logmod
import pathlib as pl
from typing import (Any, Annotated, ClassVar, Generic, TypeAlias,
                    TypeVar, cast)
from re import Match
from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping, Sequence
import warnings
import pytest
from random import randint

from .. import _interface as API  # noqa: N812
from ..errors import StrangError
from ..strang import Strang
from ..processor import StrangBasicProcessor

##--|
logging  = logmod.root
UUID_STR = str(uuid.uuid1())

##--|

class TestStrangBase:
    """ Ensure basic functionality of structured names,
    but ensuring StrName is a str.
    """

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_type_subclass(self):
        assert(issubclass(Strang, str))

    def test_basic_ctor(self):
        as_str = "head.a::tail.b"
        obj = Strang(as_str)
        assert(obj is not as_str)
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, API.Strang_p))
        assert(isinstance(obj, str))
        assert(not obj.is_uniq())
        assert(obj.shape == (2, 2))

    def test_initial(self):
        obj = Strang("head::tail")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(str in Strang.mro())

    def test_repr(self):
        obj = Strang("head::tail")
        assert(repr(obj) == "<Strang<+P>: head::tail>")

    def test_repr_with_uuid(self):
        obj = Strang(f"head::tail.<uuid:{UUID_STR}>")
        assert(obj.is_uniq())
        assert(repr(obj) == f"<Strang<+P>: head::tail.<uuid:{UUID_STR}>>")
        assert(obj.shape == (1,2))

    def test_repr_with_brace_val(self):
        obj = Strang("head::tail.{aval}.blah")
        assert(repr(obj) == "<Strang<+P>: head::tail.{aval}.blah>")

    def test_needs_separator(self):
        with pytest.raises(StrangError):
            Strang("head|tail")

    def test_shape(self):
        obj = Strang("head.a.b::tail.c.d.blah.bloo")
        assert(obj.shape == (3,5))

class TestStrangAccess:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_getitem_equiv_to_str(self):
        ing = "group.blah.awef::a.b.c"
        ang = Strang(ing)
        assert(ang is not ing)
        assert(ang == ing)
        assert(ang[0] == ing[0])
        assert(ang[:-1] == ing[:-1])
        assert(ang[2:6] == ing[2:6])
        assert(ang[:] == ing[:])
        assert(ang[:] is not ing[:])

    def test_getitem_section_word(self):
        val = Strang("a.b.c::d.cognate.f")
        assert(val[0,0]   == "a")
        assert(val[0,1]   == "b")
        assert(val[0,-1]  == "c")
        assert(val[1,0]   == "d")
        assert(val[1,1]   == "cognate")
        assert(val[1,-1]  == "f")

    def test_getitem_section_word_slice(self):
        val = Strang("a.b.c::d.e.f.g")
        assert(val[0,:]   == "a.b.c")
        assert(val[0,:-1] == "a.b")
        assert(val[1,0::2] == "d.f")
        assert(val[1,:0:-2] == "g.e")

    def test_getitem_section_word_by_name(self):
        val = Strang("a.b.c::d.cognate.f")
        assert(val['head',0]   == "a")
        assert(val['head',1]   == "b")
        assert(val['head',-1]  == "c")
        assert(val['body',0]   == "d")
        assert(val['body',1]   == "cognate")
        assert(val['body',-1]  == "f")

    def test_getitem_section_slice(self):
        val = Strang("a.b.c::d.e.f")
        match val.data.bounds[0]:
            case slice(start=x,stop=y):
                assert(x == 0)
                assert(y == 5)
            case x:
                 assert(False), x

        assert(val[0,:] == "a.b.c")
        assert(val[1,:] == "d.e.f")
        assert(val[0,] == "a.b.c")
        assert(val[1,] == "d.e.f")

    def test_getitem_section_slice_by_name(self):
        val = Strang("a.b.c::d.e.f")
        match val.data.bounds[0]:
            case slice(start=x,stop=y):
                assert(x == 0)
                assert(y == 5)
            case x:
                 assert(False), x

        assert(val['head',:] == "a.b.c")
        assert(val['body',:] == "d.e.f")
        assert(val['head',] == "a.b.c")
        assert(val['body',] == "d.e.f")

    def test_getitem_body_mark(self):
        val = Strang("group.blah.awef::a.$head$.c")
        assert(val[1, 1] == "$head$")
        assert(val.get(1,1) is val.section(1).marks.head)
        assert(Strang.section(1).marks.head in val)

    def test_getitem_head_mark(self):
        val = Strang("group.blah.$basic$::a..$head$")
        assert(val[0, -1] == "$basic$")
        assert(val.get(0, -1) is val.section(0).marks.basic)
        assert(Strang.section(0).marks.basic in val)

    def test_getitem_multi_slices(self):
        """
        [:,:] gets the strang, but uses Strang.get instead of str.__getitem__
        """
        ing = "group.blah.$basic$::a..$head$"
        ang = Strang(ing)
        assert(ang[:,:] == ing)

    def test_geitem_multi_slices_with_uuid(self):
        """
        [:,:] gets the strang, but expands the values to give uuid vals as well
        """
        ing = "group.blah.$basic$::a..<uuid>"
        ang = Strang(ing)
        targ = f"group.blah.$basic$::a..<uuid:{ang.get(1,-1)}>"
        assert(ang[:,:] == targ)

    def test_get_str(self):
        val = Strang("group.blah.awef::a.blah.2")
        match val.get(1,1), val[1,1]:
            case "blah", "blah":
                assert(True)
            case x:
                 assert(False), x

    def test_get_int(self):
        val = Strang("group.blah.awef::a.blah.3")
        match val.get(1,-1), val[1,-1]:
            case 3, "3":
                assert(True)
            case x:
                 assert(False), (type(x), x)

    def test_get_uuid(self):
        val = Strang("group.blah.awef::a.<uuid>")
        assert(val.is_uniq())
        match val.get(1, -1), val[1,-1]:
            case uuid.UUID() as x, "<uuid>":
                assert(val.uuid() is x)
            case x:
                 assert(False), x

    def test_get_words(self):
        val = Strang("group.blah.awef::a.b.<uuid>")
        assert(val.is_uniq())
        match list(val.words(1)), val[1,:]:
            case [*xs], "a.b.<uuid>":
                for x,y in zip(xs, ["a", "b", val.data.meta[1][-1]],
                               strict=True):
                    assert(x == y)
                else:
                    assert(True)
            case x:
                 assert(False), x

    def test_get_words_with_case(self):
        val = Strang("group.blah.awef::a.b.<uuid>")
        assert(val.is_uniq())
        match list(val.words(1, case=True)), val[1,:]:
            case [*xs], "a.b.<uuid>":
                for x,y in zip(xs, ["a", ".", "b", ".", val.data.meta[1][-1]],
                               strict=True):
                    assert(x == y)
                else:
                    assert(True)
            case x:
                 assert(False), x

    def test_words_with_selection(self):
        val    = Strang("group.blah.awef::a.b.c.d.e.f")
        words  = list(val.words(1, case=True, select=slice(0, 3)))
        match words, val[1,:3]:
            case [*xs], "a.b.c" as targ:
                assert("".join(xs) == targ)
                for x,y in zip(xs, ["a",".","b",".","c"],
                               strict=True):
                    assert(x == y)
                else:
                    assert(True)
            case x:
                 assert(False), x

    def test_iter(self):
        val = Strang("group.blah.awef::a.b.c")
        for x,y in zip(val, ["group", "blah","awef", "a", "b", "c"],
                       strict=True):
            assert(x == y)

    def test_iter_uuid(self):
        val = Strang("group.blah.awef::a.b.c.<uuid>")
        assert(val.is_uniq())
        for x,y in zip(val, ["group", "blah", "awef", "a", "b","c", val.get(1,-1)],
                       strict=False):
            assert(x == y)

    def test_shape(self):
        obj = Strang("a.b.c::d.e.f.g.h")
        assert(obj.shape == (3,5))

class TestStrangEQ:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_hash(self):
        obj  = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c")
        assert(hash(obj) == hash(obj2))

    def test_hash_same_as_str(self):
        obj = Strang("head::tail.a.b.c")
        assert(hash(obj) == str.__hash__(obj))
        assert(hash(obj) == hash(str(obj)))

    def test_hash_spy(self, mocker):
        hash_spy = mocker.spy(Strang, "__hash__")
        obj = Strang("head::tail.a.b.c")
        hash(obj)
        hash_spy.assert_called()

    def test_hash_fail(self):
        obj  = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.d")
        assert(hash(obj) != hash(obj2))

    def test_different_uuids_different_hashes(self):
        obj   = Strang("head::tail.a.b.<uuid>")
        obj2  = Strang("head::tail.a.b.<uuid>")
        assert(obj.is_uniq())
        assert(obj2.is_uniq())
        assert(obj is not obj2)
        assert(str(obj) is not str(obj2))
        assert(obj.get(1,-1) != obj2.get(1,-1))
        assert(hash(obj) != hash(obj2))

        assert(hash(str(obj)) == str.__hash__(str(obj)))
        assert(str.__hash__(str(obj)) != str.__hash__(str(obj2)))

    def test_eq_to_str(self):
        obj = Strang("head::tail.a.b.c")
        other = "head::tail.a.b.c"
        assert(obj == other)

    def test_not_eq_to_str(self):
        obj = Strang("head::tail.a.b.c")
        other = "tail.a.b.c.d"
        assert(obj != other)

    def test_eq_to_strang(self):
        obj = Strang("head::tail.a.b.c")
        other = Strang("head::tail.a.b.c")
        assert(obj == other)

    def test_not_eq_to_strang(self):
        obj = Strang("head::tail.a.b.c")
        other = Strang("head::tail.a.b.c.d")
        assert(obj != other)

    def test_not_eq_to_strang_group(self):
        obj = Strang("head::tail.a.b.c")
        other = Strang("head.blah::tail.a.b.c")
        assert(obj != other)

    @pytest.mark.xfail
    def test_not_eq_uuids(self):
        obj   = Strang("head::tail.a.<uuid>")
        other = Strang("head::tail.a.<uuid>")
        assert(obj.is_uniq())
        assert(other.is_uniq())

        assert(isinstance(obj[-1], uuid.UUID))
        assert(isinstance(other[-1], uuid.UUID))

        assert(obj[-1] != other[-1])
        assert(hash(obj) != hash(other))
        assert(obj is not other)

        assert(not obj.__eq__(other))
        assert(obj.__eq__(other) is (obj == other))
        result = obj != other
        assert(result)

class TestStrangLT:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_lt(self):
        obj   = Strang("head::tail.a.b.c")
        obj2  = Strang("head::tail.a.b.c.d")
        assert( obj < obj2 )

    def test_lt_mark(self):
        obj   = Strang("head::tail.a.b..c")
        obj2  = Strang("head::tail.a.b..c.d")
        assert( obj < obj2 )

    def test_lt_uuid(self):
        obj   = Strang("head::tail.a.b.c")
        obj2  = Strang("head::tail.a.b.c.<uuid>")
        assert(not obj.is_uniq())
        assert(obj2.is_uniq())
        assert( obj < obj2 )

    def test_lt_fail(self):
        obj   = Strang("head::tail.a.b.c")
        obj2  = Strang("head::tail.a.c.c.d")
        assert(not obj < obj2 )

    def test_lt_fail_on_head(self):
        obj   = Strang("head.blah::tail.a.b.c")
        obj2  = Strang("head::tail.a.b.c.d")
        assert(not obj < obj2 )

    def test_le(self):
        obj   = Strang("head::tail.a.b.d")
        obj2  = Strang("head::tail.a.b.d")
        assert(not obj < obj2 )
        assert(obj <= obj2)

    def test_le_on_self(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c")
        assert(obj == obj2)
        assert(obj <= obj2 )

    @pytest.mark.xfail
    def test_le_on_uuid(self):
        obj  = Strang("head::tail.a.b.c.<uuid>")
        obj2 = Strang(obj)
        assert(obj.is_uniq())
        assert(obj2.is_uniq())
        assert(obj[-1] == obj2[-1])
        assert(obj == obj2)
        assert(obj <= obj2 )

    @pytest.mark.xfail
    def test_le_fail_on_gen_uuid(self):
        obj  = Strang("head::tail.a.b.<uuid>")
        obj2 = Strang("head::tail.a.b.<uuid>")
        assert(obj.is_uniq())
        assert(obj2.is_uniq())
        assert(not obj < obj2 )
        assert(not obj <= obj2)

@pytest.mark.skip
class TestStrangSubGen:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_canon(self):
        obj = Strang(f"group::body.a.b.c..<uuid:{UUID_STR}>")
        assert(isinstance((result:=obj.canon()), Strang))
        assert(result == "group::body.a.b.c")
        assert(obj == f"group::body.a.b.c..<uuid:{UUID_STR}>")

    def test_canon_extended(self):
        obj = Strang(f"group::body.a.b.c..$gen$.<uuid:{UUID_STR}>.e.f.g")
        assert(isinstance((result:=obj.canon()), Strang))
        assert(result == "group::body.a.b.c..e.f.g")
        assert(obj == f"group::body.a.b.c..$gen$.<uuid:{UUID_STR}>.e.f.g")

    def test_pop_no_marks(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((result:=obj.pop()), Strang))
        assert(result == obj)
        assert(result is not obj)

    def test_pop_mark(self):
        obj = Strang("group::body.a.b.c..d")
        assert(isinstance((result:=obj.pop()), Strang))
        assert(result == "group::body.a.b.c")
        assert(obj == "group::body.a.b.c..d")

    def test_pop_to_top(self):
        obj = Strang("group::body.a.b.c..d..e")
        assert(isinstance((result:=obj.pop(top=True)), Strang))
        assert(result == "group::body.a.b.c")
        assert(obj == "group::body.a.b.c..d..e")

    def test_pop_to_top_with_markers(self):
        obj = Strang("group::+.body.a.b.c").with_head().to_uniq()
        assert(isinstance((result:=obj.pop(top=True)), Strang))
        assert(result == "group::+.body.a.b.c")

    def test_push(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((result:=obj.push("blah")), Strang))
        assert(result == "group::body.a.b.c..blah")
        assert(obj == "group::body.a.b.c")

    def test_push_none(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((result:=obj.push(None)), Strang))
        assert(result == "group::body.a.b.c")
        assert(result is not obj)
        assert(obj == "group::body.a.b.c")

    def test_push_uuid(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((result:=obj.push(f"<uuid:{UUID_STR}>")), Strang))
        assert(result == f"group::body.a.b.c..<uuid:{UUID_STR}>")
        assert(obj == "group::body.a.b.c")

    def test_push_multi(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((result:=obj.push("first", "second", "third")), Strang))
        assert(result == "group::body.a.b.c..first.second.third")
        assert(obj == "group::body.a.b.c")

    def test_push_repeated(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((r1:=obj.push("first")), Strang))
        assert(r1 == "group::body.a.b.c..first")
        assert(isinstance((r2:=r1.push("second")), Strang))
        assert(r2 == "group::body.a.b.c..first..second")
        assert(isinstance((r3:=r2.push("third")), Strang))
        assert(r3 == "group::body.a.b.c..first..second..third")
        assert(obj == "group::body.a.b.c")

    def test_push_number(self):
        obj = Strang("group::body.a.b.c")
        for _ in range(10):
            num = randint(0, 100)
            assert(obj.push(num) == "group::body.a.b.c..{num}")

    def test_to_uniq(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((r1:=obj.to_uniq()), Strang))
        assert(isinstance((r1_uuid:=r1[-1]), uuid.UUID))
        assert(r1 == f"group::body.a.b.c..$gen$.<uuid:{r1_uuid}>")

    def test_to_uniq_idempotent(self):
        obj = Strang("group::body.a.b.c")
        r1  = obj.to_uniq()
        r2  = r1.to_uniq()
        assert(r1 is r2)

    def test_to_uniq_with_suffix(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((r1:=obj.to_uniq(suffix="simple")), Strang))
        assert(isinstance((r1_uuid:=r1[-2]), uuid.UUID))
        assert(r1 == f"group::body.a.b.c..$gen$.<uuid:{r1_uuid}>.simple")

    def test_de_uniq(self):
        obj = Strang("group::body.a.b.c")
        r1 = obj.to_uniq()
        assert(r1.pop() == obj)
        assert(r1.de_uniq() == obj)

    def test_blah(self):
        obj = Strang("group::body.a.b.c")
        r1 = obj.to_uniq()
        assert(r1.pop() == obj)

    def test_with_head(self):
        obj = Strang("group::body")
        assert((result:=obj.with_head()) == "group::body..$head$")
        assert(obj < result)
        assert(obj == "group::body")

    def test_idempotent_with_head(self):
        obj = Strang("group::body")
        assert((result:=obj.with_head()) == "group::body..$head$")
        assert(result == result.with_head().with_head())

    def test_uuid_with_head(self):
        obj = Strang(f"group::body.<uuid:{UUID_STR}>")
        assert(isinstance((result:=obj.with_head()), Strang))
        assert(result == f"group::body.<uuid:{UUID_STR}>..$head$")
        assert(obj == f"group::body.<uuid:{UUID_STR}>")

    def test_mark_with_head(self):
        obj = Strang(f"group::body..<uuid:{UUID_STR}>")
        assert(isinstance((result:=obj.with_head()), Strang))
        assert(result == f"group::body..<uuid:{UUID_STR}>..$head$")
        assert(obj == f"group::body..<uuid:{UUID_STR}>")

@pytest.mark.skip
class TestStrangTests:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_contains(self):
        obj  = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b")
        assert(obj2 in obj)

    def test_match_against_str(self):
        obj  = Strang("head::tail.a.b.c")
        match obj:
            case "head::tail.a.b.c":
                assert(True)
            case _:
                assert(False)

    def test_match_against_strang(self):
        obj  = Strang("head::tail.a.b.c")
        match obj:
            case Strang("head::tail.a.b.c"):
                assert(True)
            case _:
                assert(False)

    def test_not_contains(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.c.b")
        assert(obj not in obj2)

    def test_contains_word(self):
        obj = Strang("head::tail.a.b.c")
        assert("tail" in obj)

    def test_contains_uuid(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(isinstance((obj_uuid:=obj[-1]), uuid.UUID))
        assert(obj_uuid in obj)

    def test_contains_uuid_fail(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(uuid.uuid1() not in obj)

    def test_contains_mark(self):
        obj = Strang("head::tail.a.b.c.$gen$.<uuid>")
        assert(Strang.bmark_e.gen in obj)

    def test_contains_mark_fail(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(Strang.bmark_e.gen not in obj)

    def test_is_uniq(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(obj.is_uniq())

    def test_not_is_uniq(self):
        obj = Strang("head::tail.a.b.c")
        assert(not obj.is_uniq())

    def test_popped_uniq_is_not_uniq(self):
        obj = Strang("head::tail.a.b.c..<uuid>")
        assert(obj.is_uniq())
        popped = obj.pop()
        assert(not popped.is_uniq())

@pytest.mark.skip
class TestStrangFormatting:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_format_group(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj:g}" == "group.blah")

    def test_format_body(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj:b}" == "body.a.b.c")

    @pytest.mark.skip
    def test_todo(self):
        pass

@pytest.mark.skip
class TestStrangAnnotation:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_unannotated(self):
        obj = Strang("group::body")
        assert(Strang._typevar is None)
        assert(obj._typevar is None)

    def test_type_annotated(self):
        cls = Strang[int]
        assert(issubclass(cls, Strang))
        assert(cls._typevar is int)

    def test_str_annotation(self):
        cls = Strang["blah"]
        assert(issubclass(cls, Strang))
        assert(cls._typevar == "blah")

    def test_annotated_instance(self):
        cls = Strang[int]
        ref = cls("group.a.b::body.c.d")
        assert(isinstance(ref, Strang))
        assert(ref._typevar is int)

    def test_match_type(self):
        match Strang[int]("group.a.b::body.c.d"):
            case Strang():
                assert(True)
            case _:
                assert(False)

    def test_match_on_strang(self):
        match Strang[int]("group.a.b::body.c.d"):
            case Strang("group.a.b::body.c.d"):
                assert(True)
            case _:
                assert(False)

    def test_match_on_literal(self):
        match Strang[int]("group.a.b::body.c.d"):
            case "group.a.b::body.c.d":
                assert(True)
            case _:
                assert(False)

    def test_match_on_subtype(self):
        cls = Strang[int]
        match Strang[int]("group.a.b::body.c.d"):
            case cls():
                assert(True)
            case _:
                assert(False)

    def test_match_on_subtype_fail(self):
        cls = Strang[bool]
        match Strang[int]("group.a.b::body.c.d"):
            case cls():
                assert(False)
            case _:
                assert(True)

    def test_subclass_annotate(self):

        class StrangSub(Strang):
            _separator : ClassVar[str] = ":|:"
            pass

        ref = StrangSub[int]("group.a.b:|:body.c.d")
        assert(ref._typevar is int)
        assert(isinstance(ref, Strang))
        assert(isinstance(ref, StrangSub))

    def test_subclass_annotate_independence(self):

        class StrangSub(Strang):
            _separator : ClassVar[str] = ":|:"
            pass

        ref = StrangSub[int]("group.a.b:|:body.c.d")
        assert(ref._typevar is int)
        assert(isinstance(ref, Strang))
        assert(isinstance(ref, StrangSub))

        obj = Strang("group::tail.a.b.c")
        assert(isinstance(obj, Strang))
        assert(not isinstance(obj, StrangSub))

@pytest.mark.skip
class TestStrangParameterized:

    def test_with_params(self):
        obj = Strang("head::tail.a.b.c[blah]")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(obj[-1] == "c[blah]")
