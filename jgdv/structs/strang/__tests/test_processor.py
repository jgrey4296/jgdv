#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import uuid
import warnings
from collections.abc import (Callable, Iterable, Iterator, Mapping,
                             MutableMapping, Sequence)
from random import randint
from re import Match
from typing import Annotated, Any, ClassVar, Generic, TypeAlias, TypeVar, cast
from uuid import UUID
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest

# ##-- end 3rd party imports

from .. import _interface as API  # noqa: N812
from ..errors import StrangError
from ..processor import StrangBasicProcessor
from ..strang import Strang

##--|
logging  = logmod.root
UUID_STR = str(uuid.uuid1())

##--|

class TestStrang_PreProcess:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_clean_separators(self):
        ing =  "a.b.c::d.e....f"
        obj = StrangBasicProcessor()
        match obj.pre_process(Strang, ing):
            case "a.b.c::d.e..f", {}:
                assert(True)
            case x:
                 assert(False), x

    def test_trim_rhs(self):
        ing = "a.b.c::d.e...."
        obj = StrangBasicProcessor()
        match obj.pre_process(Strang, ing):
            case "a.b.c::d.e", {}:
                assert(True)
            case x:
                 assert(False), x

    def test_trim_lhs(self):
        ing =  "    a.b.c::d.e"
        obj = StrangBasicProcessor()
        match obj.pre_process(Strang, ing):
            case "a.b.c::d.e", {}:
                assert(True)
            case x:
                 assert(False), x

    def test_verify_structure_fail_missing(self):
        obj = StrangBasicProcessor()
        with pytest.raises(ValueError):
            obj.pre_process(Strang, "a.b.c")


    def test_compress_uuid(self):
        obj         = StrangBasicProcessor()
        ing         = f"head::a.b.c..<uuid:{UUID_STR}>"
        simple_ing  = "head::a.b.c..<uuid>"
        match obj.pre_process(Strang, ing):
            case str() as x, {"uuid": UUID() as uid}:
                assert(x == simple_ing)
                assert(str(uid) == UUID_STR)
                assert(True)
            case x:
                assert(False), x

    @pytest.mark.xfail
    def test_verify_structure_fail_surplus(self):
        obj = StrangBasicProcessor()
        with pytest.raises(ValueError):
            obj.pre_process(Strang, "a.b.c::d.e.f::g.h.i")

class TestStrang_Process:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_process_section_bounds(self):
        ing = "a.b.c::d.e.f"
        obj = StrangBasicProcessor()
        base = Strang(ing)
        base.data.bounds = ()
        assert(not bool(base.data.bounds))
        obj.process(base)
        match base.data.bounds:
            case [slice() as head, slice() as body]:
                assert(ing[head] == "a.b.c")
                assert(ing[body] == "d.e.f")
                assert(True)
            case x:
                 assert(False), x

    def test_process_section_slices(self):
        ing = "a.b.c.blah::d.e.f"
        obj = StrangBasicProcessor()
        base = Strang(ing)
        base.data.slices = ()
        assert(not bool(base.data.slices))
        obj.process(base)
        match base.data.slices:
            case [tuple() as head, tuple() as body]:
                assert(len(head) == 4)
                assert(len(body) == 3)
                for x,sl in zip(["a","b","c","blah"], head, strict=True):
                    assert(x == ing[sl])
                for x,sl in zip(["d", "e", "f"], body, strict=True):
                    assert(x == ing[sl])
            case x:
                 assert(False), x

    def test_process_section_flat(self):
        ing             = "a.b.c.blah::d.e.f"
        obj             = StrangBasicProcessor()
        base            = Strang(ing)
        base.data.flat  = ()
        assert(not bool(base.data.flat))
        obj.process(base)
        match base.data.flat:
            case [*xs]:
                assert(len(xs) == 7)
                for x,sl in zip(["a","b","c","blah","d","e","f"], xs, strict=True):
                    assert(x == ing[sl])
            case x:
                assert(False), x

class TestStrang_PostProcess_UUIDs:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_head_uuids(self):
        obj = StrangBasicProcessor()
        val = Strang("a.b.c.<uuid>::d.e.f")
        assert(val.uuid())
        val.data.meta = ()
        assert(not bool(val.data.meta))
        obj.post_process(val)
        assert(bool(val.data.meta))
        assert(val.uuid())
        match val.data.meta[0][-1]:
            case API.StrangMarkAbstract_e() as x if x == API.DefaultBodyMarks_e.unique:
                assert(True)
            case x:
                assert(False), x

    def test_body_uuids(self):
        obj = StrangBasicProcessor()
        val = Strang("a.b.c::d.e.<uuid>")
        assert(val.uuid())
        val.data.meta = ()
        assert(not bool(val.data.meta))
        obj.post_process(val)
        assert(val.uuid())
        match val.data.meta[1][-1]:
            case API.StrangMarkAbstract_e() as x if x == API.DefaultBodyMarks_e.unique:
                assert(True)
            case x:
                 assert(False), x

    def test_exact_uuid(self):
        obj = Strang(f"head::tail.<uuid:{UUID_STR}>")
        assert(obj.uuid())
        assert(obj.data.meta[1][-1] is API.DefaultBodyMarks_e.unique)
        match obj.get(1,-1):
            case uuid.UUID():
                assert(True)
            case x:
                 assert(False), type(x)

    def test_rebuild_uuid(self):
        ing = f"head::tail.<uuid:{UUID_STR}>"
        s1 = Strang(ing)
        s2 = Strang(str(s1))
        assert(s1.uuid() == s2.uuid())
        assert(isinstance(s1.get(1,-1), uuid.UUID))
        assert(isinstance(s2.get(1,-1), uuid.UUID))
        assert(s1.get(1,-1) == s2.get(1,-1))
        assert(s1[1,-1] == s2[1,-1])

    def test_rebuild_generated_uuid(self):
        s1 = Strang("head::tail.<uuid>")
        s2 = Strang(str(s1))
        assert(s1.uuid())
        assert(s2.uuid())
        assert(isinstance(s1.get(1,-1), uuid.UUID))
        assert(isinstance(s2.get(1,-1), uuid.UUID))
        assert(s1[:,:] == s2[:,:])

    def test_multiple_uuids_errors(self):
        with pytest.raises(StrangError):
            Strang("head::tail.<uuid>.<uuid>")

class TestStrang_PostProcess_Marks:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_head_marks(self):
        head           = API.DefaultHeadMarks_e
        obj            = StrangBasicProcessor()
        val            = Strang("a.b.$basic$::d.e.f")
        val.data.meta  = ()
        assert(not bool(val.data.meta))
        obj.post_process(val)
        assert(bool(val.data.meta))
        match val.data.meta[0][-1]:
            case x if x is head.basic:
                assert(val.get(0,-1) is head.basic)
                assert(True)
            case x:
                assert(False), x

    def test_body_marks(self):
        body = API.DefaultBodyMarks_e
        obj = StrangBasicProcessor()
        val = Strang("a.b.c::d.e.$head$")
        val.data.meta = ()
        assert(not bool(val.data.meta))
        obj.post_process(val)
        assert(bool(val.data.meta))
        match val.data.meta[1][-1]:
            case x if x is body.head:
                assert(val.get(1,-1) is body.head)
                assert(True)
            case x:
                assert(False), x

    def test_implicit_mark_start(self):
        body = API.DefaultBodyMarks_e
        obj = StrangBasicProcessor()
        val = Strang(f"head::_.tail.blah")
        val.data.meta = ()
        assert(not bool(val.data.meta))
        obj.post_process(val)
        assert(bool(val.data.meta))
        match val.data.meta[1][0]:
            case x if x is body.hide:
                assert(val.get(1,0) is body.hide)
            case x:
                assert(False), x

    def test_implicit_mark_end(self):
        body           = API.DefaultBodyMarks_e
        obj            = StrangBasicProcessor()
        val            = Strang(f"head::tail.blah._")
        val.data.meta  = ()
        assert(not bool(val.data.meta))
        obj.post_process(val)
        assert(bool(val.data.meta))
        match val.data.meta[1][-1]:
            case x if x is body.hide:
                assert(val.get(1,-1) is body.hide)
            case x:
                assert(False), x

    def test_implicit_skip_mark(self):
        body           = API.DefaultBodyMarks_e
        obj            = StrangBasicProcessor()
        val            = Strang(f"head::tail..blah")
        val.data.meta  = ()
        assert(not bool(val.data.meta))
        obj.post_process(val)
        assert(bool(val.data.meta))
        match val.data.meta[1][1]:
            case x if x is body.empty:
                assert(val.get(1,1) is body.empty)
            case x:
                assert(False), x

    def test_implicit_mark_fail(self):
        """ An implicit mark, not at the start or end, wont be converted """
        body = API.DefaultBodyMarks_e
        obj = StrangBasicProcessor()
        val = Strang(f"head::a._.tail.blah")
        val.data.meta = ()
        assert(not bool(val.data.meta))
        obj.post_process(val)
        assert(bool(val.data.meta))
        match val.data.meta[1][1]:
            case x if x is not body.hide:
                assert(val.get(1,0) is not body.hide)
            case x:
                assert(False), x

    def test_extension_mark(self):
        obj = Strang(f"head::+.tail.blah")
        assert(obj.get(1,0) == Strang.section(1).marks.extend)

    # @pytest.mark.parametrize(["val"], [(x,) for x in iter(Strang.bmark_e)])
    # def test_build_named_mark(self, val):
    #     obj = Strang(f"head::{val}.blah")
    #     assert(obj._body_meta[0] == val)
    #     assert(obj[0] == val)
