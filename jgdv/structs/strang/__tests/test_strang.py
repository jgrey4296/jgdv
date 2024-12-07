#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import uuid
import logging as logmod
import pathlib as pl
from typing import (Any, Annotated, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings
import pytest
from random import randint

from jgdv.structs.strang import Strang
logging = logmod.root

UUID_STR = str(uuid.uuid1())

class TestStrangBase:
    """ Ensure basic functionality of structured names,
    but ensuring StrName is a str.
    """

    def test_sanity(self):
        assert(True is not False)
        assert(Strang is not None)

    def test_initial(self):
        obj = Strang("head::tail")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))

    def test_with_params(self):
        obj = Strang("head::tail.a.b.c[blah]")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(obj[-1] == "c[blah]")

    def test_repr(self):
        obj = Strang("head::tail")
        assert(repr(obj) == "<Strang: head::tail>")

    def test_repr_with_uuid(self):
        obj = Strang(f"head::tail.<uuid:{UUID_STR}>")
        assert(repr(obj) == f"<Strang: head::tail.<uuid>>")

    def test_needs_separator(self):
        with pytest.raises(ValueError):
            Strang("head|tail")

    def test_shape(self):
        obj = Strang("head.a.b::tail.c.d.blah.bloo")
        assert(obj.shape == (3,5))

class TestStrangValidation:

    def test_sanity(self):
        assert(True is not False)

    def test_pre_filter_repeat_gaps(self):
        val = Strang("group::a.b....c....d.e")
        assert(val == "group::a.b..c..d.e")

    def test_gap_mark(self):
        obj = Strang("head::tail..blah")
        assert(obj[1:1] == Strang.bmark_e.mark)

    def test_remove_gap_if_last(self):
        obj = Strang("head::tail.blah..")
        assert(obj[-1] == "blah")

    def test_build_uuids(self):
        obj = Strang(f"head::tail.<uuid:{UUID_STR}>")
        assert(isinstance(obj[1:-1], uuid.UUID))

    def test_build_uuid_gen(self):
        obj = Strang("head::tail.<uuid>.<uuid>")
        assert(isinstance(obj[-1], uuid.UUID))
        assert(isinstance(obj[-2], uuid.UUID))
        assert(obj[-1] != obj[-2])

    def test_rebuild_uuid(self):
        s1 = Strang(f"head::tail.<uuid:{UUID_STR}>")
        s2 = Strang(str(s1))
        assert(isinstance(s1[1:-1], uuid.UUID))
        assert(isinstance(s2[1:-1], uuid.UUID))
        assert(s1[-1] == s2[-1])

    def test_rebuild_generated_uuid(self):
        s1 = Strang("head::tail.<uuid>")
        s2 = Strang(str(s1))
        assert(isinstance(s1[-1], uuid.UUID))
        assert(isinstance(s2[-1], uuid.UUID))
        assert(s1[-1] == s2[-1])

    @pytest.mark.parametrize(["val"], [(x,) for x in iter(Strang.bmark_e)])
    def test_build_named_mark(self, val):
        obj = Strang(f"head::{val}.blah")
        assert(obj._body_meta[0] == val)
        assert(obj[0] == val)

    def test_implicit_mark(self):
        obj = Strang(f"head::_.tail.blah")
        assert(obj[0] == Strang.bmark_e.hide)

    def test_implicit_mark_fail(self):
        """ implicit only works in first two elements of body """
        obj = Strang(f"head::a.b.c._.tail.blah")
        assert(obj._body_meta[3] == None)

    def test_extension_mark(self):
        obj = Strang(f"head::+.tail.blah")
        assert(obj[0] == Strang.bmark_e.extend)

class TestStrangCmp:

    def test_hash(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c")
        assert(hash(obj) == hash(obj2))

    def test_hash_fail(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.d")
        assert(hash(obj) != hash(obj2))

    def test_hash_uuid_fail(self):
        obj = Strang("head::tail.a.b.<uuid>")
        obj2 = Strang("head::tail.a.b.<uuid>")
        assert(hash(obj) != hash(obj2))

    def test_eq_to_str(self):
        obj = Strang("head::tail.a.b.c")
        other = "tail.a.b.c"
        assert(obj == other)

    def test_eq_to_full_str(self):
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

    def test_lt(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c.d")
        assert( obj < obj2 )

    def test_lt_mark(self):
        obj = Strang("head::tail.a.b..c")
        obj2 = Strang("head::tail.a.b..c.d")
        assert( obj < obj2 )

    def test_lt_uuid(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c.<uuid>")
        assert( obj < obj2 )

    def test_lt_fail(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.c.c.d")
        assert(not obj < obj2 )

    def test_lt_fail_on_head(self):
        obj = Strang("head.blah::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c.d")
        assert(not obj < obj2 )

    def test_le(self):
        obj  = Strang("head::tail.a.b.d")
        obj2 = Strang("head::tail.a.b.d")
        assert(not obj < obj2 )
        assert(obj <= obj2)

    def test_le_on_self(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c")
        assert(obj == obj2)
        assert(obj <= obj2 )

    def test_le_on_uuid(self):
        obj  = Strang("head::tail.a.b.c.<uuid>")
        assert(obj.metadata.get("gen_uuid"))
        obj2 = Strang(obj)
        assert(obj[-1] == obj2[-1])
        assert(obj == obj2)
        assert(obj <= obj2 )

    def test_le_fail_on_gen_uuid(self):
        obj  = Strang("head::tail.a.b.<uuid>")
        obj2 = Strang("head::tail.a.b.<uuid>")
        assert(not obj < obj2 )
        assert(not obj <= obj2)

class TestStrangAccess:

    def test_sanity(self):
        assert(True is not False)

    def test_iter(self):
        val = Strang("group.blah.awef::a.b.c")
        for x,y in zip(val, ["a", "b","c"]):
            assert(x == y)

    def test_iter_uuid(self):
        val = Strang("group.blah.awef::a.b.c.<uuid>")
        for x,y in zip(val, ["a", "b","c", val[-1]]):
            assert(x == y)

    def test_getitem(self):
        val = Strang("group.blah.awef::a.b.c")
        assert(val[0:0] == "group")
        assert(val[0:2] == "awef")
        assert(val[1:0] == "a")
        assert(val[1:2] == "c")

    def test_getitem_mark(self):
        val = Strang("group.blah.awef::a..c")
        assert(val[-2] == Strang.bmark_e.mark)

    def test_getitem_uuid(self):
        val = Strang("group.blah.awef::a.<uuid>")
        assert(isinstance(val[-1], uuid.UUID))

    def test_getslice_0(self):
        val = Strang("group.blah.awef::a.b.c")
        assert(val[0:] == "group.blah.awef")

    def test_getslice_1(self):
        val = Strang("group.blah.awef::a.b.c")
        assert(val[1:] == "a.b.c")

    def test_getslice_2(self):
        obj = Strang("group.simple::a.b.c.d")
        sub = obj[2:-1]
        assert(isinstance(sub, Strang))
        assert(sub == "group.simple::a.b.c")

    def test_getslice_2_uuid(self):
        obj = Strang(f"group.simple::<uuid:{UUID_STR}>.b.c.d")
        sub = obj[2:-1]
        assert(isinstance(sub, Strang))
        assert(sub == f"group.simple::<uuid:{UUID_STR}>.b.c")

class TestStrangSubGen:

    def test_sanity(self):
        assert(True is not False)

    def test_canon(self):
        obj = Strang(f"group::body.a.b.c..<uuid:{UUID_STR}>")
        assert(isinstance((result:=obj.canon()), Strang))
        assert(result == "group::body.a.b.c")
        assert(obj == f"group::body.a.b.c..<uuid:{UUID_STR}>")

    def test_pop_no_marks(self):
        obj = Strang(f"group::body.a.b.c")
        assert(isinstance((result:=obj.pop()), Strang))
        assert(result == obj)
        assert(result is not obj)

    def test_pop_mark(self):
        obj = Strang(f"group::body.a.b.c..d")
        assert(isinstance((result:=obj.pop()), Strang))
        assert(result == "group::body.a.b.c")
        assert(obj == f"group::body.a.b.c..d")

    def test_pop_to_top(self):
        obj = Strang(f"group::body.a.b.c..d..e")
        assert(isinstance((result:=obj.pop(top=True)), Strang))
        assert(result == "group::body.a.b.c")
        assert(obj == "group::body.a.b.c..d..e")

    def test_push(self):
        obj = Strang(f"group::body.a.b.c")
        assert(isinstance((result:=obj.push("blah")), Strang))
        assert(result == "group::body.a.b.c..blah")
        assert(obj == "group::body.a.b.c")

    def test_push_none(self):
        obj = Strang(f"group::body.a.b.c")
        assert(isinstance((result:=obj.push(None)), Strang))
        assert(result == "group::body.a.b.c")
        assert(result is not obj)
        assert(obj == "group::body.a.b.c")

    def test_push_uuid(self):
        obj = Strang(f"group::body.a.b.c")
        assert(isinstance((result:=obj.push(f"<uuid:{UUID_STR}>")), Strang))
        assert(result == f"group::body.a.b.c..<uuid:{UUID_STR}>")
        assert(obj == "group::body.a.b.c")

    def test_push_multi(self):
        obj = Strang(f"group::body.a.b.c")
        assert(isinstance((result:=obj.push("first", "second", "third")), Strang))
        assert(result == f"group::body.a.b.c..first.second.third")
        assert(obj == "group::body.a.b.c")

    def test_push_repeated(self):
        obj = Strang(f"group::body.a.b.c")
        assert(isinstance((r1:=obj.push("first")), Strang))
        assert(r1 == f"group::body.a.b.c..first")
        assert(isinstance((r2:=r1.push("second")), Strang))
        assert(r2 == f"group::body.a.b.c..first..second")
        assert(isinstance((r3:=r2.push("third")), Strang))
        assert(r3 == f"group::body.a.b.c..first..second..third")
        assert(obj == "group::body.a.b.c")

    def test_push_number(self):
        obj = Strang(f"group::body.a.b.c")
        for x in range(10):
            num = randint(0, 100)
            assert(obj.push(num) == f"group::body.a.b.c..{num}")

    def test_to_uniq(self):
        obj = Strang(f"group::body.a.b.c")
        assert(isinstance((r1:=obj.to_uniq()), Strang))
        assert(isinstance((r1_uuid:=r1[-1]), uuid.UUID))
        assert(r1 == f"group::body.a.b.c..$gen$.<uuid:{r1_uuid}>")

    def test_to_uniq_idempotent(self):
        obj = Strang(f"group::body.a.b.c")
        r1  = obj.to_uniq()
        r2  = r1.to_uniq()
        assert(r1 is r2)

    def test_to_uniq_with_suffix(self):
        obj = Strang(f"group::body.a.b.c")
        assert(isinstance((r1:=obj.to_uniq(suffix="simple")), Strang))
        assert(isinstance((r1_uuid:=r1[-2]), uuid.UUID))
        assert(r1 == f"group::body.a.b.c..$gen$.<uuid:{r1_uuid}>.simple")

    def test_de_uniq(self):
        obj = Strang(f"group::body.a.b.c")
        r1 = obj.to_uniq()
        assert(r1.pop() == obj)
        assert(r1.de_uniq() == obj)

    def test_blah(self):
        obj = Strang(f"group::body.a.b.c")
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

class TestStrangTests:

    def test_sanity(self):
        assert(True is not False)

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
        assert(obj.is_uniq)

    def test_not_is_uniq(self):
        obj = Strang("head::tail.a.b.c")
        assert(not obj.is_uniq)

    def test_popped_uniq_is_not_uniq(self):
        obj = Strang("head::tail.a.b.c..<uuid>")
        assert(obj.is_uniq)
        popped = obj.pop()
        assert(not popped.is_uniq)

class TestStrangFormatting:

    def test_sanity(self):
        assert(True is not False)

    def test_format_group(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj:g}" == "group.blah")

    def test_format_body(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj:b}" == "body.a.b.c")

class TestStrangAnnotation:

    def test_sanity(self):
        assert(True is not False)

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
        assert(ref._typevar == int)

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
            _separator = ":|:"
            pass

        ref = StrangSub[int]("group.a.b:|:body.c.d")
        assert(ref._typevar is int)
        assert(isinstance(ref, Strang))
        assert(isinstance(ref, StrangSub))
