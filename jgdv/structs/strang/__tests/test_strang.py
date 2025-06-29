#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011, PLR2004, ANN001
from __future__ import annotations

import uuid
import logging as logmod
import pathlib as pl
from types import GenericAlias
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

class TestStrang_Base:
    """ Ensure basic functionality of structured names,
    but ensuring StrName is a str.
    """

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_type_subclass(self):
        assert(issubclass(Strang, str))

    def test_basic_ctor(self):
        ing = "head.a::tail.b"
        obj = Strang(ing)
        assert(obj is not ing)
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, API.Strang_p))
        assert(isinstance(obj, str))
        assert(not hasattr(obj, "__dict__"))
        assert(not obj.uuid())
        assert(obj.shape == (2, 2))

    def test_ctor_with_multi_args(self):
        ing = "head.a::tail"
        args = ["a","b","c"]
        obj = Strang(ing, *args)
        assert(obj is not ing)
        assert(obj == "head.a::tail.a.b.c")

    def test_typing(self):
        obj = Strang("head::tail")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(str in Strang.mro())

    def test_needs_separator(self):
        with pytest.raises(StrangError):
            Strang("head|tail")

    def test_shape(self):
        obj = Strang("head.a.b::tail.c.d.blah.bloo")
        assert(obj.shape == (3,5))

class TestStrang_GetItem:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_equiv_to_str(self):
        ing = "group.blah.awef::a.b.c"
        ang = Strang(ing)
        assert(ang is not ing)
        assert(ang == ing)
        assert(ang[0] == ing[0])
        assert(ang[:-1] == ing[:-1])
        assert(ang[2:6] == ing[2:6])
        assert(ang[:] == ing[:])
        assert(ang[:] is not ing[:])

    def test_section_word(self):
        val = Strang("a.b.c::d.cognate.f")
        assert(val[0,0]   == "a")
        assert(val[0,1]   == "b")
        assert(val[0,-1]  == "c")
        assert(val[1,0]   == "d")
        assert(val[1,1]   == "cognate")
        assert(val[1,-1]  == "f")

    def test_section_word_slice(self):
        val = Strang("a.b.c::d.e.f.g")
        assert(val[0,:]   == "a.b.c")
        assert(val[0,:-1] == "a.b")
        assert(val[1,0::2] == "d.f")
        assert(val[1,:0:-2] == "g.e")

    def test_section_word_by_name(self):
        val = Strang("a.b.c::d.cognate.f")
        assert(val['head',0]   == "a")
        assert(val['head',1]   == "b")
        assert(val['head',-1]  == "c")
        assert(val['body',0]   == "d")
        assert(val['body',1]   == "cognate")
        assert(val['body',-1]  == "f")

    def test_section_slice(self):
        val = Strang("a.b.c::d.e.f")
        match val.data.sections[0]:
            case slice(start=x,stop=y):
                assert(x == 0)
                assert(y == 5)
            case x:
                 assert(False), x

        assert(val[0,:] == "a.b.c")
        assert(val[1,:] == "d.e.f")

    def test_section_slice_by_name(self):
        val = Strang("a.b.c::d.e.f")
        match val.data.sections[0]:
            case slice(start=x,stop=y):
                assert(x == 0)
                assert(y == 5)
            case x:
                 assert(False), x

        assert(val['head',:] == "a.b.c")
        assert(val['body',:] == "d.e.f")
        assert(val['head'] == "a.b.c")
        assert(val['body'] == "d.e.f")

    def test_multi_slice(self):
        """
        a.b.c::d.e.f
        [:,:,:-1] -> a.b.c::d.e
        """
        val = Strang("a.b.c::d.e.f")
        assert(val[:,:,:-1] == "a.b.c::d.e")
        assert(val[:,1:,:] == "b.c::d.e.f")
        assert(val[:,2,1] == "c::e")

    def test_body_mark(self):
        val = Strang("group.blah.awef::a.$head$.c")
        assert(val[1, 1] == "$head$")
        assert(val.get(1,1) is val.section(1).marks.head)
        assert(Strang.section(1).marks.head in val)

    def test_head_mark(self):
        val = Strang("group.blah.$basic$::a..$head$")
        assert(val[0, -1] == "$basic$")
        assert(val.get(0, -1) is val.section(0).marks.basic)
        assert(Strang.section(0).marks.basic in val)

    def test_multi_slices(self):
        """
        [:,:] gets the strang, but uses Strang.get instead of str.__getitem__
        """
        ing = "group.blah.$basic$::a..$head$"
        ang = Strang(ing)
        assert(ang[:,:] == ing)

    def test_multi_slices_not_all_sections(self):
        """
        [:1,:] gets the strang, but uses Strang.get instead of str.__getitem__
        """
        ing = "group.blah.$basic$::a..$head$"
        ang = Strang(ing)
        assert(ang[:1,:] == "group.blah.$basic$::")
        assert(ang[1:,:] == "a..$head$")

    def test_section_slice_error_on_negative(self):
        """
        [:1,:] gets the strang, but uses Strang.get instead of str.__getitem__
        """
        ing = "group.blah.$basic$::a..$head$"
        ang = Strang(ing)
        with pytest.raises(ValueError):
            ang[:-1,:]

    def test_multi_slices_with_implicit_uuid(self):
        """
        [:,:] gets the strang, but expands the values to give uuid vals as well
        """
        ing       = "group.blah.$basic$::a.b.c.<uuid>"
        ang       = Strang(ing)
        uuid_ing  = f"group.blah.$basic$::a.b.c.<uuid:{ang.get(1,-1)}>"
        ##--|
        assert(ang[:] == ing)
        assert(ang[:,:] == uuid_ing)

    def test_multi_slices_with_explicit_uuid(self):
        """
        [:,:] gets the strang, but expands the values to give uuid vals as well
        because the underlying string is explicit, [:] also shows the uuid value
        """
        uuid_obj         = uuid.uuid1()
        ing              = f"group.blah.$basic$..<uuid:{uuid_obj}>::a.b.c"
        ang              = Strang(ing)
        assert(ang.get(0,-1) == uuid_obj)
        assert(ang[:,:]  == ing)

class TestStrang_GetAttr:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_head(self):
        obj = Strang("head.a.b::tail.c.d")
        assert(obj.head == "head.a.b")

    def test_body(self):
        obj = Strang("head.a.b::tail.c.d")
        assert(obj.body == "tail.c.d")

    def test_missing(self):
        obj = Strang("head.a.b::tail.c.d")
        with pytest.raises(AttributeError):
            assert(obj.tail)

class TestStrang_Get:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_str(self):
        val = Strang("group.blah.awef::a.blah.2")
        match val.get(1,1), val[1,1]:
            case "blah", "blah":
                assert(True)
            case x:
                 assert(False), x

    def test_int(self):
        val = Strang("group.blah.awef::a.blah.<int:3>")
        match val.get(1,-1), val[1,-1]:
            case 3, "<int>":
                assert(True)
            case x:
                assert(False), (type(x), x)

    def test_uuid(self):
        val = Strang("group.blah.awef::a.<uuid>")
        assert(not val.uuid())
        match val.get(1, -1), val[1,-1]:
            case uuid.UUID() as x, "<uuid>":
                assert(True)
            case x:
                assert(False), x

    def test_uuid_repeat(self):
        val = Strang("group.blah.awef.<uuid>::a.ab.c")
        assert(val.get(0,-1) is val.get(0,-1))

class TestStrang_Words:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_get_words(self):
        val = Strang("group.blah.awef.<uuid>::a.b")
        assert(not val.uuid())
        match list(val.words(0)), val[0,:]:
            case [*xs], "group.blah.awef.<uuid>":
                for x,y in zip(xs, ["group","blah", "awef", val.get(0,-1)], strict=True):
                    assert(x == y)
                else:
                    assert(True)
            case x:
                 assert(False), x

    def test_get_words_with_sep_marks(self):
        skip_mark = Strang.section(1).marks.skip()
        base = "group::a.b.c..d.e.f"
        val     = Strang(base)
        expect  = ["a", "b", "c", skip_mark, "d", "e", "f"]
        expect_joined = "a.b.c..d.e.f"
        assert(not val.uuid())
        match list(val.words(1)), val[1,:]:
            case [*xs], str() as extracted if extracted == expect_joined:
                for x,y in zip(xs, expect, strict=True):
                    assert(x == y)
                else:
                    assert(True)
            case x:
                 assert(False), x

    def test_get_words_with_case(self):
        val = Strang("group.blah.awef::a.b.<uuid>")
        assert(not val.uuid())
        match list(val.words(1, case=True)), val[1,:]:
            case [*xs], "a.b.<uuid>":
                for x,y in zip(xs, ["a", ".", "b", ".", val.get(1,-1)], strict=True):
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

class TestStrang_Iter:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_iter(self):
        val = Strang("group.blah.awef::a.b.c")
        for x,y in zip(val, ["group", "blah","awef", "a", "b", "c"],
                       strict=True):
            assert(x == y)

    def test_iter_uuid(self):
        val = Strang("group.blah.awef::a.b.c.<uuid>")
        assert(not val.uuid())
        for x,y in zip(val, ["group", "blah", "awef", "a", "b","c", val.get(1,-1)],
                       strict=False):
            assert(x == y)

class TestStrang_Shape:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_shape(self):
        obj = Strang("a.b.c::d.e.f.g.h")
        assert(obj.shape == (3,5))

class TestStrang_Index:

    def test_index(self):
        ing = "a.b.c::c.e.f"
        ang = Strang(ing)
        assert(ing.index("b") == ang.index("b"))

    def test_index_mark(self):
        ing = "a.b.c::d.e.$head$.f"
        ang = Strang(ing)
        assert(ang.index("$head$") == ang.index(Strang.section(1).marks.head))

    def test_index_mark_empty_str(self):
        """ find('') is useless,
        but find(mark.empty) can
        """
        ing = "a.b.c::d.e..f"
        ang = Strang(ing)
        with pytest.raises(ValueError):
            ang.index("")

        index1 = ang.index(ang.section(1).marks.empty)
        index2 = ang.index(1,2)
        assert(index1 == index2)

    def test_index_slice(self):
        ing = "a.b.c::d.blah.f"
        ang = Strang(ing)
        assert(ang.index(1,1) == ing.index("blah"))

    def test_index_word_slice(self):
        ing = "a.b.c::d.blah.f"
        ang = Strang(ing)
        idx1 = ang.index('body',1)
        idx2 = ing.index("blah")
        assert(idx1 == idx2)

    def test_index_fail(self):
        ing = "a.b.c::d.e.f"
        ang = Strang(ing)
        with pytest.raises(ValueError):
            ang.index("g")

    def test_index_mark_fail(self):
        ing = "a.b.c::d.e.f"
        ang = Strang(ing)
        with pytest.raises(ValueError):
            ang.index(Strang.section(1).marks.head)

    def test_rindex(self):
        ing = "a.b.c::c.e.f"
        ang = Strang(ing)
        assert(ing.rindex("c") == ang.rindex("c"))

    def test_rindex_mark_empty_str(self):
        """ find('') is useless,
        but find(mark.empty) can
        """
        ing = "a.b.c::d.e..f"
        ang = Strang(ing)
        with pytest.raises(ValueError):
            ang.rindex("")

        rindex1 = ang.rindex(ang.section(1).marks.empty)
        rindex2 = ang.rindex(1,2)
        assert(rindex1 == rindex2)

    def test_rindex_fail(self):
        ing = "a.b.c::c.e.f"
        ang = Strang(ing)
        with pytest.raises(ValueError):
            ang.rindex("g")


    def test_rindex_no_matching_mark(self):
        ing = "a.b.c::c.e.f"
        ang = Strang(ing)
        with pytest.raises(ValueError):
            ang.rindex(API.DefaultBodyMarks_e.skip())

class TestStrang_EQ:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_eq_to_str(self):
        obj = Strang("head::tail.a.b.c")
        other = "head::tail.a.b.c"
        assert(obj == other)

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

    def test_not_eq_uuids(self):
        obj   = Strang("head::tail.a.<uuid>")
        other = Strang("head::tail.a.<uuid>")
        match obj.get(1,-1), other.get(1,-1):
            case uuid.UUID() as x, uuid.UUID() as y if x != y:
                assert(obj.__eq__(other) is (obj == other))
                assert(obj != other)
            case x:
                assert(False), x

    def test_not_eq_to_str(self):
        obj    = Strang("head::tail.a.b.c")
        other  = "tail.a.b.c.d"
        assert(obj != other)

class TestStrang_Hash:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_hash(self):
        obj  = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c")
        assert(hash(obj) == hash(obj2))

    def test_hash_same_as_str_hash(self):
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
        assert(obj is not obj2)
        assert(str(obj) is not str(obj2))
        assert(hash(obj) != hash(obj2))

class TestStrang_LT:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    ##--| <

    def test_lt(self):
        obj   = Strang("head::tail.a.b.c")
        obj2  = Strang("head::tail.a.b.c.d")
        assert(obj < obj2 )

    def test_lt_mark(self):
        obj   = Strang("head::tail.a.b..c")
        obj2  = Strang("head::tail.a.b..c.d")
        assert(obj < obj2 )

    def test_lt_uuid(self):
        obj   = Strang("head::tail.a.b.c")
        obj2  = Strang("head::tail.a.b.c.<uuid>")
        assert(obj < obj2 )

    def test_lt_fail(self):
        obj   = Strang("head::tail.a.b.c")
        obj2  = Strang("head::tail.a.c.c.d")
        assert(not obj < obj2 )

    def test_lt_fail_on_head(self):
        obj   = Strang("head.blah::tail.a.b.c")
        obj2  = Strang("head::tail.a.b.c.d")
        assert(not obj < obj2 )

    ##--| <=

    def test_le(self):
        obj   = Strang("head::tail.a.b.d")
        obj2  = Strang("head::tail.a.b.d")
        assert(not obj < obj2 )
        assert(obj <= obj2)

    def test_le_on_self(self):
        obj         = Strang("head::tail.a.b.c")
        obj2        = Strang("head::tail.a.b.c")
        assert(obj  == obj2)
        assert(obj  <= obj2 )

    def test_le_on_uuid(self):
        obj  = Strang("head::tail.a.b.c.<uuid>")
        obj2 = Strang(obj[:,:])
        assert(obj.uuid() == obj2.uuid())
        assert(obj == obj2)
        assert(obj <= obj2)

    def test_le_fail_on_uuids(self):
        obj  = Strang("head::tail.a.b.<uuid>")
        obj2 = Strang("head::tail.a.b.<uuid>")
        assert(not obj < obj2 )
        assert(not obj <= obj2)

class TestStrang_Contains:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    ##--| in

    def test_contains(self):
        obj  = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b")
        assert(obj2 in obj)

    def test_not_contains(self):
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.c.b")
        assert(obj not in obj2)

    def test_contains_word(self):
        obj = Strang("head::tail.a.b.c")
        assert("tail" in obj)

    def test_contains_uuid(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        match obj.get(1,-1):
            case uuid.UUID() as x:
                assert(x in obj)
            case x:
                assert(False), x

    def test_contains_uuid_fail(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(not obj.uuid())
        assert(uuid.uuid1() not in obj)

    def test_contains_mark(self):
        obj = Strang("head::tail.a.b.c.$gen$.<uuid>")
        assert(Strang.section('body').marks.gen in obj)

    def test_contains_mark_fail(self):
        obj = Strang("head::tail.a.b.c.$gen$.<uuid>")
        assert(Strang.section('body').marks.head not in obj)

    ##--| match

    def test_match_against_str(self):
        obj  = Strang("head::tail.a.b.c")
        match obj:
            case "head::tail.a.b.c":
                assert(True)
            case _:
                assert(False)

    def test_match_sections(self):
        obj  = Strang("head::tail.a.b.c")
        match obj:
            case Strang(head=x, body=y):
                assert(x == "head")
                assert(y == "tail.a.b.c")
            case x:
                assert(False), x

    def test_match_sections_positionally(self):
        obj  = Strang("head::tail.a.b.c")
        match obj:
            case Strang("head", "tail.a.b.c"):
                assert(True)
            case _:
                assert(False)

    def test_match_sections_literally(self):
        obj  = Strang("head.a.b::tail.a.b.c")
        match obj:
            case Strang(head="head.a.b"):
                assert(True)
            case x:
                assert(False), x

    def test_match_sections_as_str(self):
        obj  = Strang("head.a.b::tail.a.b.c")
        match obj:
            case Strang(head=str() as x):
                assert(x == "head.a.b")
            case x:
                assert(False), x

    def test_match_missing_sections_fail(self):
        obj  = Strang("head::tail.a.b.c")
        match obj:
            case Strang(head=_, tail=_):
                assert(False)
            case _:
                assert(True)

class TestStrang_Modify:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    ##--| Push

    def test_push(self):
        obj = Strang("group::body.a.b.c")
        match obj.push("blah"):
            case Strang(body="body.a.b.c..blah"):
                assert(True)
            case x:
                assert(False), x

    def test_push_none_no_op(self):
        obj = Strang("group::body.a.b.c")
        match obj.push(None):
            case Strang() as x if x == obj:
                assert(True)
            case x:
                assert(False), x

    def test_push_multi(self):
        obj = Strang("group::body.a.b.c")
        match obj.push("d", "e", "f"):
            case Strang(body="body.a.b.c..d.e.f"):
                assert(True)
            case x:
                assert(False), x

    def test_push_multi_with_nones(self):
        obj = Strang("group::body.a.b.c")
        match obj.push("d", "e", None, "f"):
            case Strang(body="body.a.b.c..d.e..f") as x:
                assert(True)
            case x:
                assert(False), x

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
            assert(obj.push(num) == f"group::body.a.b.c..{num}")

    def test_push_with_new_args(self):
        target_uuid  = uuid.uuid1()
        base         = "group::a.b.c"
        obj          = Strang(base)
        obj2         = Strang(f"{base}[<uuid>]", uuid=target_uuid)
        expect       = "group::body.a.b.c[<uuid>]"
        result       = obj.push(new_args=[target_uuid])
        assert(result is not obj)
        assert(not obj.uuid())
        assert(result.uuid() == target_uuid)

    def test_push_new_args_overwrites_old(self):
        target_uuid  = uuid.uuid1()
        base         = "group::a.b.c[<uuid>, blah]"
        obj          = Strang(base)
        expect       = "group::body.a.b.c[<uuid>]"
        result       = obj.push(new_args=[target_uuid])
        assert(result is not obj)
        assert(result.uuid() == target_uuid)
        assert(result.args() != obj.args())

    ##--| UUIDs

    def test_push_preserves_uuid_in_body(self):
        obj = Strang("group::body.a.b.c.<uuid>")
        match obj.push("blah"):
            case Strang() as x:
                assert(x[:] == f"{obj[:]}..blah")
                assert(obj.get(1,4) == x.get(1,4))
            case x:
                assert(False), x

    def test_push_does_not_preserve_uuid_arg(self):
        obj = Strang("group::body.a.b.c[<uuid>]")
        assert(obj.uuid())
        match obj.push("blah"):
            case Strang() as x:
                assert(not x.uuid())
            case x:
                assert(False), x

    def test_push_basic_uuid_str(self):
        obj = Strang("group::body.a.b.c")
        match obj.push("<uuid>"):
            case Strang() as x:
                assert(x[:] == "group::body.a.b.c..<uuid>")
                assert(str(x) == f"group::body.a.b.c..<uuid:{x.get(1,-1)}>")
            case x:
                assert(False), x

    def test_push_explicit_uuid_str(self):
        obj         = Strang("group::body.a.b.c")
        uuid_word   = f"<uuid:{uuid.uuid1()}>"
        ing         = f"group::body.a.b.c..{uuid_word}"
        match obj.push(uuid_word):
            case Strang() as x:
                assert(str(x) == ing)
            case x:
                assert(False), x

    def test_push_uuid_object(self):
        obj       = Strang("group::body.a.b.c")
        new_uuid  = uuid.uuid1()
        match obj.push(new_uuid):
            case Strang(body="body.a.b.c..<uuid>") as x:
                assert(x.get(1,-1) == new_uuid)
            case x:
                assert(False), x

    ##--| Marking

    def test_push_mark(self):
        obj = Strang("group::body")
        mark = obj.section(-1).marks.head
        match obj.push(mark):
            case Strang(body="body..$head$") as x:
                assert(mark in x)
                assert(True)
            case x:
                assert(False), x

    def test_push_mark_idempotent(self):
        obj = Strang("group::body")
        mark = obj.section(-1).marks.head
        match obj.push(mark):
            case Strang(body="body..$head$") as x:
                repeat = x.push(mark)
                assert(mark in x)
                assert(mark in repeat)
                assert(repeat == x)
            case x:
                assert(False), x

    def test_push_mark_idempotent_alt(self):
        obj = Strang("group::body")
        mark = obj.section(-1).marks.head
        match obj.push(mark, mark, mark):
            case Strang(body="body..$head$") as x:
                assert(mark in x)
            case x:
                assert(False), x

    def test_push_mark_repeat(self):
        obj   = Strang("group::body")
        mark  = obj.section(-1).marks.extend
        match obj.push(mark, mark, mark):
            case Strang(body="body..+.+.+") as x:
                assert(True)
            case x:
                assert(False), x

    def test_mark_from_str(self):
        obj   = Strang("group::body")
        match obj.mark("$head$"):
            case Strang() as x:
                assert(x[1,-1] == "$head$")
            case x:
                assert(False), x

    def test_mark_literal(self):
        obj   = Strang("group::body")
        match obj.mark(API.DefaultBodyMarks_e.head):
            case Strang() as x:
                assert(x[1,-1] == "$head$")
            case x:
                assert(False), x

    def test_mark_fail(self):
        obj   = Strang("group::body")
        with pytest.raises(ValueError):
            obj.mark("badval")

    ##--| Pop

    def test_pop_no_marks(self):
        obj = Strang("group::body.a.b.c")
        match obj.pop():
            case Strang(body="body.a.b.c") as x:
                assert(x == obj)
                assert(x is obj)
            case x:
                assert(False), x

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
        obj = Strang("group::+.body.a.b.c..$head$..<uuid>")
        assert(isinstance((result:=obj.pop(top=True)), Strang))
        assert(result == "group::+.body.a.b.c")

class TestStrang_UUIDs:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_implicit(self):
        obj = Strang("group::body.a.b.c..<uuid>")
        match obj.get(1,-1):
            case uuid.UUID():
                assert(not obj.uuid())
            case x:
                assert(False), x

    def test_implicit_str(self):
        ing = "group::body.a.b.c..<uuid>"
        ang = Strang(ing)
        full_ing = f"group::body.a.b.c..<uuid:{ang.get(1,-1)}>"
        assert(not ang.uuid())
        assert(str(ang) == full_ing)
        assert(ang[:] == ing)
        assert(ang[:,:] == full_ing)

    def test_explicit(self):
        uid_obj = uuid.uuid1()
        ing = f"group::body.a.b.c..<uuid:{uid_obj}>"
        ang = Strang(ing)
        assert(isinstance(ang.get(1,-1), uuid.UUID))
        assert(not ang.uuid())

    def test_explicit_str(self):
        uid_obj = uuid.uuid1()
        ing = f"group::body.a.b.c..<uuid:{uid_obj}>"
        ang = Strang(ing)
        assert(not ang.uuid())
        assert(ang.get(1,-1) == uid_obj)

    def test_uuid_carries_to_new_instances(self):
        uid_obj = uuid.uuid1()
        ing = f"group::body.a.b.c..<uuid:{uid_obj}>"
        ang1 = Strang(ing)
        ang2 = Strang(ang1)
        assert(ang1[:] == ang2[:])
        assert(ang1 == ang2)
        assert(ang1.uuid() == ang2.uuid())

    def test_unique_uuid_carries_to_new_instances(self):
        uuid_obj = uuid.uuid1()
        ing = f"group..<uuid:{uuid_obj}>::body.a.b.c"
        ang1 = Strang(ing)
        ang2 = Strang(ang1)
        assert(ang1[0,-1] == ang2[0, -1])

    ##--| to unique

    def test_to_uniq(self):
        obj = Strang("group::body.a.b.c")
        match obj.to_uniq():
            case Strang() as x:
                assert(x.uuid())
            case x:
                raise TypeError(type(x))

    def test_to_uniq_with_suffix(self):
        obj = Strang("group::body.a.b.c")
        match obj.to_uniq("blah"):
            case Strang() as x:
                assert(x[:] == "group::body.a.b.c.blah[<uuid>]")
                assert(x.uuid())
            case x:
                assert(False), x

    def test_to_uniq_pop_returns_self(self):
        obj              = Strang("group::body.a.b.c")
        r1               = obj.to_uniq()
        assert(r1 is not obj)
        assert(r1.uuid())
        assert(r1.pop()  == r1)

    def test_to_uniq_idempotent(self):
        obj = Strang("group::body.a.b.c")
        r1  = obj.to_uniq()
        r2  = r1.to_uniq()
        assert(r1.uuid())
        assert(r2.uuid())
        assert(obj != r1)
        assert(obj != r2)
        assert(r1 == r2)
        assert(r1.uuid() == r2.uuid())

    def test_de_uniq(self):
        obj     = Strang("group::body.a.b.c[<uuid>]")
        target  = "group::body.a.b.c"
        assert(obj.uuid())
        match obj.de_uniq():
            case Strang() as x:
                assert(not x.uuid())
                assert(x == target)
                assert(f"{x:a=}" == "")
                assert(True)
            case x:
                assert(False), x

    def test_is_unique(self):
        obj = Strang("head::tail.a.b.c[<uuid>]")
        assert(obj.uuid())

    def test_is_unique_with_uuid(self):
        obj = Strang("head::tail.a.b.c.<uuid>[<uuid>]")
        assert(obj.uuid())
        assert(obj.uuid() != obj.get(1,-1))

    def test_is_not_unique(self):
        obj = Strang("head::tail.a.b.c")
        assert(not obj.uuid())

    def test_is_not_unique_alt(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(not obj.uuid())

    def test_not_is_unique_alt(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(not obj.uuid())

    def test_popped_uniq_is_not_uniq(self):
        obj     = Strang("head::tail.a.b.c..<uuid>")
        popped  = obj.pop()
        assert(popped.shape == (1,4))
        assert(not obj.uuid())
        assert(not popped.uuid())
        assert(obj != popped)

    ##--| args

    def test_str_arg_uuid(self):
        ing = "group::a.b.c[<uuid>]"
        ang = Strang(ing)
        assert(ang.uuid())

    def test_explicit_str_arg_uuid(self):
        uid = uuid.uuid1()
        ing = f"group::a.b.c[<uuid:{uid}>]"
        ang = Strang(ing)
        assert(ang.uuid() == uid)

    def test_kwarg_uuid(self):
        uid = uuid.uuid1()
        ing = f"group::a.b.c[<uuid>]"
        ang = Strang(ing, uuid=uid)
        assert(ang.uuid() == uid)

    def test_error_on_multiple_head_uuids(self):
        ing       = "group::a.b.c[<uuid>,<uuid>]"
        with pytest.raises(StrangError):
            Strang(ing)

class TestStrang_Formatting:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    ##--| repr

    def test_repr_with_brace_val(self):
        obj = Strang("head::tail.{aval}.blah")
        assert(repr(obj) == "<Strang: head::tail.{aval}.blah>")

    def test_repr_uses_no_expansion(self):
        raw               = "head::tail.<uuid>.a.b.c"
        obj               = Strang(raw)
        assert(repr(obj)  == f"<Strang: {obj[:]}>")

    ##--| str

    def test_str_is_full_expansion(self):
        raw             =  "head::tail.<uuid>.a.b.c"
        obj             = Strang(raw)
        body_uuid       = f"<uuid:{obj.get(1,1)}>"
        full_expansion  = f"head::tail.{body_uuid}.a.b.c"
        assert(str(obj) == full_expansion)

    ##--| str slice

    def test_basic_slice_no_expansion(self):
        raw            = "head::tail.<uuid>.a.b.c"
        obj            = Strang(raw)
        assert(obj[:]  == raw)

    def test_basic_slice_but_args_no_expansion(self):
        raw            = "head::tail.<uuid>.a.b.c[<uuid>]"
        obj            = Strang(raw)
        assert(obj[:]  == raw)

    ##--| slice+

    def test_advanced_slice_expands_with_no_args(self):
        raw              = "head::tail.<uuid>.a.b.c"
        obj              = Strang(raw)
        body_uuid        = f"<uuid:{obj.get(1,1)}>"
        expanded         = f"head::tail.{body_uuid}.a.b.c"
        assert(obj[:,:]  == expanded)

    def test_advanced_slice_expands_with_args(self):
        raw              = "head::tail.<uuid>.a.b.c[<uuid>]"
        obj              = Strang(raw)
        body_uuid        = f"<uuid:{obj.get(1,1)}>"
        expanded         = f"head::tail.{body_uuid}.a.b.c"
        assert(obj[:,:]  == expanded)

    def test_format_group(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj[0,:]}" == "group.blah")

    def test_format_body(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj[1,:]}" == "body.a.b.c")

    def test_format_word(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj[1,0]}" == "body")

    ##--| 'u' spec

    def test_format_uuid(self):
        raw                =  "head::tail.a.b.c[<uuid>]"
        obj                = Strang(raw)
        obj_uuid           = f"<uuid:{obj.uuid()}>"
        assert(f"{obj:u}"  == obj_uuid)

    ##--| 'a+' spec

    def test_format_full_expansion(self):
        raw                 = "head::tail.<uuid>.a.b.c"
        obj                 = Strang(raw)
        body_uuid           = f"<uuid:{obj.get(1,1)}>"
        expanded            = f"head::tail.{body_uuid}.a.b.c"
        assert(f"{obj:a+}"  == expanded)

    def test_format_args_a_plus(self):
        raw                =  "head::tail.a.b.c[<uuid>]"
        obj                = Strang(raw)
        uuid_obj           = f"<uuid:{obj.uuid()}>"
        assert(f"{obj:a+}"  == f"head::tail.a.b.c[{uuid_obj}]")

    def test_format_no_args_a_plus(self):
        raw                 =  "head::tail.a.b.c"
        obj                 = Strang(raw)
        assert(f"{obj:a+}"  == "head::tail.a.b.c")

    ##--| 'a' spec

    def test_format_args_a_simple(self):
        raw                 =  "head::tail.a.b.c[<uuid>]"
        obj                 = Strang(raw)
        assert(f"{obj:a}"  == "head::tail.a.b.c[<uuid>]")

    def test_format_no_args_a_simple(self):
        raw                 =  "head::tail.a.b.c"
        obj                 = Strang(raw)
        assert(f"{obj:a}"  == "head::tail.a.b.c")

    ##--| 'a-' spec

    def test_format_args_a_minus(self):
        raw                 =  "head::tail.a.b.c[<uuid>]"
        obj                 = Strang(raw)
        assert(f"{obj:a-}"  == "head::tail.a.b.c")

    def test_format_no_args_a_minus(self):
        raw                 =  "head::tail.a.b.c"
        obj                 = Strang(raw)
        assert(f"{obj:a-}"  == "head::tail.a.b.c")

    ##--| 'a=' spec

    def test_format_args_a_equal(self):
        raw                 =  "head::tail.a.b.c[<uuid>]"
        obj                 = Strang(raw)
        assert(f"{obj:a=}"  == "<uuid>")

    def test_format_no_args_a_equal(self):
        raw                 =  "head::tail.a.b.c"
        obj                 = Strang(raw)
        assert(f"{obj:a=}"  == "")

    ##--| joined

    def test_full_slice_includes_uuid(self):
        raw             =  "head::tail.<uuid>.a.b.c[<uuid>]"
        obj             = Strang(raw)
        body_uuid       = f"<uuid:{obj.get(1,1)}>"
        obj_uuid        = f"<uuid:{obj.uuid()}>"
        basic           =  "head::tail.<uuid>.a.b.c"
        expanded        = f"head::tail.{body_uuid}.a.b.c"
        simple_args     =  "head::tail.<uuid>.a.b.c[<uuid>]"
        full_expansion  = f"head::tail.{body_uuid}.a.b.c[{obj_uuid}]"

        assert(obj.uuid())
        assert(obj[:]   == raw)
        assert(obj[:,:]     == expanded)
        assert(f"{obj:u}"   == obj_uuid)
        assert(f"{obj:a-}"  == basic)
        assert(f"{obj:a}"   == simple_args)
        assert(f"{obj:a+}"  == full_expansion)
        assert(str(obj)     == full_expansion)

class TestStrang_Annotation:
    """ Test custom parameterized subclassing

    """

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_unannotated(self):
        assert(Strang.cls_annotation() == ())
        obj = Strang("group::body")
        assert(obj.cls_annotation() == ())

    def test_simple_annotation(self):
        Strang._clear_registry()
        obj = Strang[int]
        assert(obj is not None)
        assert(obj.__origin__ is Strang)
        assert(obj.__args__ == (int,))

    def test_subclass_annotation(self):
        Strang._clear_registry()
        assert(not bool(Strang._registry))
        assert(isinstance(Strang[int], GenericAlias))

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        assert(bool(Strang._registry))
        assert(id(Strang.__annotations__) != id(IntStrang.__annotations__))
        assert(IntStrang.cls_annotation()   == (int,))
        assert(issubclass(IntStrang, Strang))
        assert(issubclass(IntStrang, Strang[int])) # type: ignore[misc]
        assert(IntStrang is Strang[int])

    def test_type_annotated(self):

        Strang._clear_registry()

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        assert(issubclass(IntStrang, Strang))
        assert(IntStrang.cls_annotation() == (int,))
        inst = IntStrang("blah::a.b.c")
        assert(inst.cls_annotation() == (int,))
        assert(not hasattr(inst, "__dict__"))

    def test_match_on_strang(self):

        Strang._clear_registry()

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        match IntStrang("group.a.b::body.c.d"):
            case Strang(body="body.c.d"):
                assert(True)
            case _:
                assert(False)

    def test_match_on_literal(self):

        Strang._clear_registry()

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        match IntStrang("group.a.b::body.c.d"):
            case "group.a.b::body.c.d":
                assert(True)
            case _:
                assert(False)

    def test_match_on_str(self):

        Strang._clear_registry()

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        match IntStrang("group.a.b::body.c.d"):
            case str():
                assert(True)
            case _:
                assert(False)

    def test_match_on_subtype(self):
        Strang._clear_registry()

        class IntStrang(Strang[int]):
            __slots__ =()
            pass

        subtype = Strang[int]
        match IntStrang("group.a.b::body.c.d"):
            case x if isinstance(x, subtype):
                assert(True)
            case _:
                assert(False)

    def test_match_on_subtype_fail(self):
        Strang._clear_registry()

        class IntStrang(Strang[int]):
            __slots__ =()
            pass

        match Strang("group.a.b::body.c.d"):
            case IntStrang() as x:
                assert(False), type(x)
            case x:
                assert(True)

    def test_match_on_subtype_fail_b(self):
        Strang._clear_registry()
        cls     = Strang[int]
        notcls  = Strang[float]
        with pytest.raises(TypeError):
            match Strang[int]("group.a.b::body.c.d"):
                case notcls(): # type: ignore[misc]
                    assert(False)
                case cls(): # type: ignore[misc]
                    assert(True)
                case _:
                    assert(False)

class TestStrang_Subclassing:
    """ Check some basic variations of Strang Subclasses,
    like changing the sections

    """

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_three_sections(self) -> None:

        class ThreeSections(Strang):
            """ A strang with 3 sections """
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", "::", str, None, True),
                ("second", "/", ":|:", str, None, True),
                ("third", ".", None, str, None, True),
            )

        match ThreeSections("a.b.c::d/e/f:|:g"):
            case ThreeSections() as val:
                assert(not hasattr(val, "__dict__"))
                assert(val.first == "a.b.c")
                assert(val.second == "d/e/f")
                assert(val.third == "g")
            case x:
                assert(False), x
        assert(issubclass(ThreeSections, Strang))
        assert(isinstance(ThreeSections, API.Strang_p))

    def test_three_sections_errors_on_malformed(self) -> None:

        class ThreeSections(Strang):
            """ A strang with 3 sections """
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", "::", str, None, True),
                ("second", "/", ":|:", str, None, True),
                ("third", ".", None, str, None, True),
            )

        assert(issubclass(ThreeSections, Strang))
        # Check it  errors on malformed
        with pytest.raises(StrangError):
            ThreeSections("a.b.c::d.e.f")

    def test_single_section(self) -> None:

        class OneSection(Strang):
            """ A strang with one section """
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", None, str, None, True),
            )

        assert(issubclass(OneSection, Strang))
        match OneSection("a.b.c::d.e.f"):
            case OneSection() as x:
                assert(x.first == "a.b.c::d.e.f")
                assert(True)
            case x:
                assert(False), x

    def test_end_section(self) -> None:

        class EndSectionStrang(Strang):
            """ A strang with one section """
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", "::", str, None, True),
                ("second", ".", "$", str, None, True),
            )

        assert(issubclass(EndSectionStrang, Strang))
        with pytest.raises(StrangError):
            EndSectionStrang("a.b.c::d.e.f")

        match EndSectionStrang("a.b.c::d.e.f$"):
            case EndSectionStrang() as x:
                assert(x == "a.b.c::d.e.f$")
                assert(True)
            case x:
                assert(False), x

    def test_optional_section(self) -> None:

        class OptSectionStrang(Strang):
            """ A strang with one section """
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", "::",  str, None, True),
                ("second", ".", "::", str, None, False),
                ("third", ".", "$",   str, None, True),
            )

        assert(issubclass(OptSectionStrang, Strang))
        ang1 = OptSectionStrang("a.b.c::d.e.f$")
        ang2 = OptSectionStrang("a.b.c::j.k.l::d.e.f$")

        assert(ang1.first == ang2.first)
        assert(ang1.second == "")
        assert(ang2.second == "j.k.l")
        assert(ang1.third == ang2.third)

    def test_subclass_annotate(self) -> None:

        class StrangSub(Strang):
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", ":|:",  str, None, True),
                ("third", ".", None,   str, None, True),
            )

        ref = StrangSub[int]("group.a.b:|:body.c.d")
        assert(ref.cls_annotation() == ())
        assert(isinstance(ref, Strang))
        assert(isinstance(ref, StrangSub))

    def test_subclass_annotate_independence(self) -> None:

        class StrangSub(Strang):
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", ":|:",  str, None, True),
                ("third", ".", None,   str, None, True),
            )

        ref = StrangSub[int]("group.a.b:|:body.c.d")
        assert(ref.cls_annotation() == ())
        assert(isinstance(ref, Strang))
        assert(isinstance(ref, StrangSub))

        obj : Strang = Strang("group::tail.a.b.c")
        assert(isinstance(obj, Strang))
        assert(not isinstance(obj, StrangSub))

    def test_subclass_matches_protocol(self) -> None:

        class StrangSub(Strang):
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", ":|:",  str, None, True),
                ("third", ".", None,   str, None, True),
            )

        match StrangSub("group:|:tail.a.b.c"):
            case API.Strang_p():
                assert(True)
            case x:
                assert(False), x

    def test_subclass_matches_strang(self) -> None:

        class StrangSub(Strang):
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", ":|:",  str, None, True),
                ("third", ".", None,   str, None, True),
            )

        match StrangSub("group:|:tail.a.b.c"):
            case Strang():
                assert(True)
            case x:
                assert(False), x

class TestStrang_Args:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_slice_with_args(self):
        obj = Strang("head::tail.a.b.c[blah,bloo,blee]")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(obj[1,-1] == "c")

    def test_with_no_args(self):
        obj = Strang("head::tail.a.b.c")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(obj[1,-1] == "c")

    def test_uuid_arg(self):
        obj = Strang("head::tail.a.b.c[<uuid>]")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(obj[1,-1] == "c")
        assert(obj.uuid())

    def test_basic_slice_includes_args(self):
        obj = Strang("head::tail.a.b.c[<uuid>]")
        assert(obj.uuid())
        assert(obj[:] == "head::tail.a.b.c[<uuid>]")

    def test_full_slice_includes_uuid(self):
        raw             =  "head::tail.<uuid>.a.b.c[<uuid>]"
        obj             = Strang(raw)
        body_uuid       = f"<uuid:{obj.get(1,1)}>"
        obj_uuid        = f"<uuid:{obj.uuid()}>"
        basic           =  "head::tail.<uuid>.a.b.c"
        expanded        = f"head::tail.{body_uuid}.a.b.c"
        simple_args     =  "head::tail.<uuid>.a.b.c[<uuid>]"
        full_expansion  = f"head::tail.{body_uuid}.a.b.c[{obj_uuid}]"

        assert(obj.uuid())
        assert(obj[:]   == raw)
        assert(obj[:,:]     == expanded)
        assert(f"{obj:u}"   == obj_uuid)
        assert(f"{obj:a-}"  == basic)
        assert(f"{obj:a}"   == simple_args)
        assert(f"{obj:a+}"  == full_expansion)
        assert(str(obj)     == full_expansion)

    def test_args(self):
        obj = Strang("head.a.b::tail.c.d[blah]")
        match obj.args():
            case ["blah"]:
                assert(True)
            case x:
                assert(False), x

    def test_multi_args(self):
        obj = Strang("head.a.b::tail.c.d[blah, bloo]")
        match obj.args():
            case ["blah", "bloo"]:
                assert(True)
            case x:
                assert(False), x

    def test_empty_args(self):
        obj = Strang("head.a.b::tail.c.d")
        match obj.args():
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_args_to_uniq(self):
        obj = Strang("head.a.b::tail.c.d[blah]")
        uniq = obj.to_uniq()
        match uniq.args():
            case ["<uuid>", "blah"]:
                assert(True)
            case x:
                assert(False), x

    def test_popped_uniq_retains_args(self):
        obj = Strang("head.a.b::tail.c.d[blah]")
        uniq = obj.to_uniq()
        popped = uniq.pop(top=True)
        match popped.args():
            case ["<uuid>", "blah"]:
                assert(True)
            case x:
                assert(False), x
