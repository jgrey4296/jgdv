#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011, PLR2004, ANN001
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

    def test_initial(self):
        obj = Strang("head::tail")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(str in Strang.mro())

    def test_repr(self):
        obj = Strang("head::tail")
        assert(repr(obj) == "<Strang: head::tail>")

    def test_repr_with_uuid(self):
        obj = Strang(f"head::tail.<uuid:{UUID_STR}>")
        assert(obj.uuid())
        assert(repr(obj) == "<Strang: head::tail.<uuid>>")
        assert(obj.shape == (1,2))

    def test_repr_with_brace_val(self):
        obj = Strang("head::tail.{aval}.blah")
        assert(repr(obj) == "<Strang: head::tail.{aval}.blah>")

    def test_needs_separator(self):
        with pytest.raises(StrangError):
            Strang("head|tail")

    def test_shape(self):
        obj = Strang("head.a.b::tail.c.d.blah.bloo")
        assert(obj.shape == (3,5))

class TestStrang_Access:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    ##--| __getitem__

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
        assert(val['head'] == "a.b.c")
        assert(val['body'] == "d.e.f")

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

    def test_getitem_multi_slices_not_all_sections(self):
        """
        [:1,:] gets the strang, but uses Strang.get instead of str.__getitem__
        """
        ing = "group.blah.$basic$::a..$head$"
        ang = Strang(ing)
        assert(ang[:1,:] == "group.blah.$basic$::")
        assert(ang[1:,:] == "a..$head$")

    def test_getitem_section_slice_error_on_negative(self):
        """
        [:1,:] gets the strang, but uses Strang.get instead of str.__getitem__
        """
        ing = "group.blah.$basic$::a..$head$"
        ang = Strang(ing)
        with pytest.raises(ValueError):
            ang[:-1,:]

    def test_geitem_multi_slices_with_implicit_uuid(self):
        """
        [:,:] gets the strang, but expands the values to give uuid vals as well
        """
        ing = "group.blah.$basic$::a..<uuid>"
        ang = Strang(ing)
        uuid_ing = f"group.blah.$basic$::a..<uuid:{ang.uuid()}>"
        assert(ang[:] == ing)
        assert(ang[:,:] == uuid_ing)

    def test_getitem_multi_slices_with_explicit_uuid(self):
        """
        [:,:] gets the strang, but expands the values to give uuid vals as well
        because the underlying string is explicit, [:] also shows the uuid value
        """
        uuid_obj         = uuid.uuid1()
        ing              = f"group.blah.$basic$::a..<uuid:{uuid_obj}>"
        ang              = Strang(ing)
        assert(ang.uuid() == uuid_obj)
        assert(ang[:,:]  == ing)

    ##--| __getattr__

    def test_getattr_head(self):
        obj = Strang("head.a.b::tail.c.d")
        assert(obj.head == "head.a.b")

    def test_getattr_body(self):
        obj = Strang("head.a.b::tail.c.d")
        assert(obj.body == "tail.c.d")

    def test_getattr_missing(self):
        obj = Strang("head.a.b::tail.c.d")
        with pytest.raises(AttributeError):
            assert(obj.tail)

    ##--| get

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
        assert(val.uuid())
        match val.get(1, -1), val[1,-1]:
            case uuid.UUID() as x, "<uuid>":
                assert(val.uuid() is x)
            case x:
                 assert(False), x

    def test_get_uuid_repeat(self):
        val = Strang("group.blah.awef::a.<uuid>")
        assert(val.uuid())
        assert(val.uuid() is val.uuid())

    ##--| words

    def test_get_words(self):
        val = Strang("group.blah.awef::a.b.<uuid>")
        assert(val.uuid())
        match list(val.words(1)), val[1,:]:
            case [*xs], "a.b.<uuid>":
                for x,y in zip(xs, ["a", "b", val.uuid()], strict=True):
                    assert(x == y)
                else:
                    assert(True)
            case x:
                 assert(False), x

    def test_get_words_with_case(self):
        val = Strang("group.blah.awef::a.b.<uuid>")
        assert(val.uuid())
        match list(val.words(1, case=True)), val[1,:]:
            case [*xs], "a.b.<uuid>":
                for x,y in zip(xs, ["a", ".", "b", ".", val.uuid()], strict=True):
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

    ##--| iter

    def test_iter(self):
        val = Strang("group.blah.awef::a.b.c")
        for x,y in zip(val, ["group", "blah","awef", "a", "b", "c"],
                       strict=True):
            assert(x == y)

    def test_iter_uuid(self):
        val = Strang("group.blah.awef::a.b.c.<uuid>")
        assert(val.uuid())
        for x,y in zip(val, ["group", "blah", "awef", "a", "b","c", val.get(1,-1)],
                       strict=False):
            assert(x == y)

    ##--| shape

    def test_shape(self):
        obj = Strang("a.b.c::d.e.f.g.h")
        assert(obj.shape == (3,5))

    ##--| index

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

class TestStrang_EQ:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    ##--| has

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
        assert(obj.uuid())
        assert(obj2.uuid())
        assert(obj is not obj2)
        assert(str(obj) is not str(obj2))
        assert(obj.get(1,-1) != obj2.get(1,-1))
        assert(hash(obj) != hash(obj2))

        assert(hash(str(obj)) == str.__hash__(str(obj)))
        assert(str.__hash__(str(obj)) != str.__hash__(str(obj2)))

    ##--| ==

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

    def test_not_eq_uuids(self):
        obj   = Strang("head::tail.a.<uuid>")
        other = Strang("head::tail.a.<uuid>")
        assert(obj.uuid())
        assert(other.uuid())
        assert(obj.uuid() != other.uuid())
        assert(isinstance(obj.get(1,-1), uuid.UUID))
        assert(isinstance(other.get(1,-1), uuid.UUID))

        assert(hash(obj) != hash(other))
        assert(obj is not other)

        assert(not obj.__eq__(other))
        assert(obj.__eq__(other) is (obj == other))
        result = obj != other
        assert(result)

class TestStrang_LT:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    ##--| <

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
        assert(not obj.uuid())
        assert(obj2.uuid())
        assert( obj < obj2 )

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
        obj = Strang("head::tail.a.b.c")
        obj2 = Strang("head::tail.a.b.c")
        assert(obj == obj2)
        assert(obj <= obj2 )

    def test_le_on_uuid(self):
        obj  = Strang("head::tail.a.b.c.<uuid>")
        obj2 = Strang(obj)
        assert(obj.uuid())
        assert(obj2.uuid())
        assert(obj.uuid() == obj2.uuid())
        assert(obj == obj2)
        assert(obj <= obj2 )

    def test_le_fail_on_gen_uuid(self):
        obj  = Strang("head::tail.a.b.<uuid>")
        obj2 = Strang("head::tail.a.b.<uuid>")
        assert(obj.uuid())
        assert(obj2.uuid())
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
        match obj.uuid():
            case uuid.UUID() as x:
                assert(x in obj)
            case x:
                assert(False), x

    def test_contains_uuid_fail(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(obj.uuid())
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

    def test_match_against_strang(self):
        obj  = Strang("head::tail.a.b.c")
        match obj:
            case Strang("head::tail.a.b.c"):
                assert(True)
            case _:
                assert(False)

    @pytest.mark.xfail
    def test_match_uuuid(self):
        obj  = Strang("head::tail.a.b.c.<uuid>")
        match obj:
            case Strang(uuid=uuid.UUID()):
                assert(True)
            case x:
                assert(False), x

    def test_match_sections(self):
        obj  = Strang("head::tail.a.b.c")
        match obj:
            case Strang(head=x, body=y):
                assert(x == "head")
                assert(y == "tail.a.b.c")
            case x:
                assert(False), x

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

    ##--| uniqueness

    def test_is_uniq(self):
        obj = Strang("head::tail.a.b.c.<uuid>")
        assert(obj.uuid())

    def test_not_is_uniq(self):
        obj = Strang("head::tail.a.b.c")
        assert(not obj.uuid())

    def test_popped_uniq_is_not_uniq(self):
        obj = Strang("head::tail.a.b.c..<uuid>")
        assert(obj.uuid())
        popped = obj.pop()
        assert(not popped.uuid())

class TestStrang_Modify:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    ##--| Push

    def test_push(self):
        obj = Strang("group::body.a.b.c")
        match obj.push("blah"):
            case Strang("group::body.a.b.c..blah"):
                assert(True)
            case x:
                assert(False), x

    def test_push_preserves_uuid(self):
        obj = Strang("group::body.a.b.c.<uuid>")
        match obj.push("blah"):
            case Strang() as x:
                assert(x[:] == f"{obj[:]}..blah")
                assert(x.uuid() == obj.uuid()), obj.diff_uuids(x.uuid())
                assert(True)
            case x:
                assert(False), x

    def test_push_none(self):
        obj = Strang("group::body.a.b.c")
        match obj.push(None):
            case Strang() as x if x == obj:
                assert(True)
            case x:
                assert(False), x

    def test_push_multi(self):
        obj = Strang("group::body.a.b.c")
        match obj.push("d", "e", "f"):
            case Strang("group::body.a.b.c..d.e.f"):
                assert(True)
            case x:
                assert(False), x

    def test_push_multi_with_nones(self):
        obj = Strang("group::body.a.b.c")
        match obj.push("d", "e", None, "f"):
            case Strang("group::body.a.b.c..d.e..f") as x:
                assert(True)
            case x:
                assert(False), x

    def test_push_basic_uuid_str(self):
        obj = Strang("group::body.a.b.c")
        match obj.push("<uuid>"):
            case Strang() as x:
                assert(x[:] == "group::body.a.b.c..<uuid>")
            case x:
                assert(False), x

    def test_push_explicit_uuid_str(self):
        obj         = Strang("group::body.a.b.c")
        uuid_obj    = uuid.uuid1()
        ing         = f"group::body.a.b.c..<uuid:{uuid_obj}>"
        simple_ing  = f"{obj}..<uuid>"
        match obj.push(f"<uuid:{uuid_obj}>"):
            case Strang(val) as x if val == simple_ing:
                assert(str(x) == ing)
                assert(x.uuid() == uuid_obj)
            case x:
                assert(False), x

    def test_push_uuid_object(self):
        obj       = Strang("group::body.a.b.c")
        new_uuid  = uuid.uuid1()
        match obj.push(new_uuid):
            case Strang("group::body.a.b.c..<uuid>") as x:
                assert(x.uuid() == new_uuid), x.diff_uuids(new_uuid)
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

    def test_push_mark(self):
        obj = Strang("group::body")
        mark = obj.section(-1).marks.head
        match obj.push(mark):
            case Strang("group::body..$head$") as x:
                assert(mark in x)
                assert(True)
            case x:
                assert(False), x

    def test_push_mark_idempotent(self):
        obj = Strang("group::body")
        mark = obj.section(-1).marks.head
        match obj.push(mark):
            case Strang("group::body..$head$") as x:
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
            case Strang("group::body..$head$") as x:
                assert(mark in x)
            case x:
                assert(False), x

    def test_push_mark_repeat(self):
        obj   = Strang("group::body")
        mark  = obj.section(-1).marks.extend
        match obj.push(mark, mark, mark):
            case Strang("group::body..+.+.+") as x:
                assert(True)
            case x:
                assert(False), x

    ##--| Pop

    def test_pop_no_marks(self):
        obj = Strang("group::body.a.b.c")
        match obj.pop():
            case Strang("group::body.a.b.c") as x:
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

    ##--| to unique

    def test_to_uniq(self):
        obj = Strang("group::body.a.b.c")
        match obj.to_uniq():
            case Strang() as x:
                assert(x.uuid())
                assert(x == "group::body.a.b.c..<uuid>")

    def test_to_uniq_with_suffix(self):
        obj = Strang("group::body.a.b.c")
        assert(isinstance((r1:=obj.to_uniq("simple")), Strang))
        assert(r1.uuid())
        assert(r1 == "group::body.a.b.c..<uuid>.simple")

    def test_to_uniq_pop_returns(self):
        obj = Strang("group::body.a.b.c")
        r1 = obj.to_uniq()
        assert(r1.pop() == obj)

    def test_to_uniq_idempotent(self):
        obj = Strang("group::body.a.b.c")
        r1  = obj.to_uniq()
        r2  = r1.to_uniq()
        assert(obj != r1)
        assert(obj != r2)
        assert(r1 == r2)

    def test_de_uniq(self):
        obj = Strang("group::body.a.b.c")
        uniq = obj.to_uniq()
        match uniq.de_uniq():
            case Strang("group::body.a.b.c") as x:
                assert(True)
            case x:
                assert(False), x

    def test_de_uniq_suffixed(self):
        obj = Strang("group::body.a.b.c")
        uniq = obj.to_uniq("blah", "bloo","blee")
        match uniq.de_uniq():
            case Strang("group::body.a.b.c") as x:
                assert(True)
            case x:
                assert(False), x

class TestStrang_UUIDs:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_implicit(self):
        obj = Strang("group::body.a.b.c..<uuid>")
        assert(obj.uuid())

    def test_implicit_str(self):
        ing = "group::body.a.b.c..<uuid>"
        ang = Strang(ing)
        assert(ang.uuid())
        assert(str(ang) == f"group::body.a.b.c..<uuid:{ang.uuid()}>")
        assert(ang[:] == ing)

    def test_explicit(self):
        uid_obj = uuid.uuid1()
        ing = f"group::body.a.b.c..<uuid:{uid_obj}>"
        ang = Strang(ing)
        assert(ang.uuid())

    def test_explicit_str(self):
        uid_obj = uuid.uuid1()
        ing = f"group::body.a.b.c..<uuid:{uid_obj}>"
        ang = Strang(ing)
        assert(ang.uuid())
        assert(str(ang) == ing)
        assert(ang[:] == "group::body.a.b.c..<uuid>")

    def test_canon(self):
        obj = Strang(f"group::body.a.b.c..<uuid:{UUID_STR}>")
        assert(obj[:] == "group::body.a.b.c..<uuid>")
        assert(obj.canon() == "group::body.a.b.c..<uuid>")

class TestStrang_Formatting:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_format_group(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj:g}" == "group.blah")

    def test_format_body(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj:b}" == "body.a.b.c")

    def test_format_word(self):
        obj = Strang("group.blah::body.a.b.c")
        assert(f"{obj[1,0]}" == "body")

class TestStrang_Annotation:
    """ Test custom parameterized subclassing

    """

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_unannotated(self):
        obj = Strang("group::body")
        assert(Strang._typevar is None)
        assert(obj._typevar is None)

    def test_type_annotated(self):

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        assert(issubclass(IntStrang, Strang))
        assert(IntStrang._typevar is int)
        inst = IntStrang("blah::a.b.c")
        assert(inst._typevar is int)
        assert(not hasattr(inst, "__dict__"))

    def test_type_reannotate(self):
        cls   = Strang[int]
        cls2  = Strang[int]
        assert(cls is cls2)

    def test_str_annotation(self):

        class BlahStrang(Strang['blah']):
            __slots__ = ()
            pass

        assert(issubclass(BlahStrang, Strang))
        assert(BlahStrang._typevar == "blah")

    def test_annotated_instance(self):

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        ref = IntStrang("group.a.b::body.c.d")
        assert(isinstance(ref, Strang))
        assert(issubclass(IntStrang, Strang))
        assert(ref._typevar is int)

    def test_match_type(self):

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        match IntStrang("group.a.b::body.c.d"):
            case IntStrang():
                assert(True)
            case _:
                assert(False)

    def test_match_on_strang(self):

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        match IntStrang("group.a.b::body.c.d"):
            case Strang("group.a.b::body.c.d"):
                assert(True)
            case _:
                assert(False)

    def test_match_on_literal(self):

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        match IntStrang("group.a.b::body.c.d"):
            case "group.a.b::body.c.d":
                assert(True)
            case _:
                assert(False)

    def test_match_on_str(self):

        class IntStrang(Strang[int]):
            __slots__ = ()
            pass

        match IntStrang("group.a.b::body.c.d"):
            case str():
                assert(True)
            case _:
                assert(False)

    def test_match_on_subtype(self):
        subtype = Strang[int]

        class IntStrang(Strang[int]):
            __slots__ =()
            pass

        match IntStrang("group.a.b::body.c.d"):
            case x if isinstance(x, subtype):
                assert(True)
            case _:
                assert(False)

    def test_match_on_subtype_fail(self):

        class IntStrang(Strang[int]):
            __slots__ =()
            pass

        match Strang("group.a.b::body.c.d"):
            case IntStrang() as x:
                assert(False), type(x)
            case x:
                assert(True)

    def test_match_on_subtype_fail_b(self):
        cls     = Strang[int]
        notcls  = Strang[float]
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
                ("third", ".", "", str, None, True),
            )

        assert(issubclass(ThreeSections, Strang))
        match ThreeSections("a.b.c::d/e/f:|:g"):
            case ThreeSections() as val:
                assert(not hasattr(val, "__dict__"))
                assert(val.first == "a.b.c")
                assert(val.second == "d/e/f")
                assert(val.third == "g")
            case x:
                assert(False), x

    def test_three_sections_errors_on_malformed(self) -> None:

        class ThreeSections(Strang):
            """ A strang with 3 sections """
            __slots__ = ()
            _sections : ClassVar = API.Sections_d(
                # name, case, end, types, marks, required
                ("first", ".", "::", str, None, True),
                ("second", "/", ":|:", str, None, True),
                ("third", ".", "", str, None, True),
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
                ("first", ".", "::", str, None, True),
                ("second", ".", "::", str, None, False),
                ("third", ".", "$", str, None, True),
            )

        assert(issubclass(OptSectionStrang, Strang))
        ang1 = OptSectionStrang("a.b.c::d.e.f$")
        ang2 = OptSectionStrang("a.b.c::j.k.l::d.e.f$")

        assert(ang1.first == ang2.first)
        assert(ang1.second == "")
        assert(ang2.second == "j.k.l")
        assert(ang1.third == ang2.third)

    @pytest.mark.xfail
    def test_subclass_annotate(self) -> None:

        class StrangSub(Strang):
            _separator : ClassVar[str] = ":|:"
            pass

        ref = StrangSub[int]("group.a.b:|:body.c.d")
        assert(ref._typevar is int)
        assert(isinstance(ref, Strang))
        assert(isinstance(ref, StrangSub))

    @pytest.mark.xfail
    def test_subclass_annotate_independence(self) -> None:

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

@pytest.mark.xfail
class TestStrangParameterized:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_with_params(self):
        obj = Strang("head::tail.a.b.c[blah]")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, str))
        assert(obj[-1] == "c[blah]")
