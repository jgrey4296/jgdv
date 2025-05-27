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
            case "a.b.c::d.e..f", {}, {}, None:
                assert(True)
            case x:
                assert(False), x

    def test_trim_rhs(self):
        ing = "a.b.c::d.e...."
        obj = StrangBasicProcessor()
        match obj.pre_process(Strang, ing):
            case "a.b.c::d.e", {}, {}, None:
                assert(True)
            case x:
                 assert(False), x

    def test_trim_lhs(self):
        ing =  "    a.b.c::d.e"
        obj = StrangBasicProcessor()
        match obj.pre_process(Strang, ing):
            case "a.b.c::d.e", {}, {}, None:
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
            case str() as x, {}, {"types": [("uuid", str() as uid)]}, None:
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


    def test_process_args(self):
        ing =  "a.b.c::d.e.f[<uuid>]"
        obj = StrangBasicProcessor()
        match obj.pre_process(Strang, ing):
            case str() as x, {}, dict() as data, None:
                assert(data.get('args_start', False))
            case x:
                assert(False), x


    def test_process_multi_args(self):
        ing =  "a.b.c::d.e.f[<uuid>,blah,bloo]"
        obj = StrangBasicProcessor()
        match obj.pre_process(Strang, ing):
            case str() as x, {}, dict() as data, None:
                assert(data.get('args_start', False))
            case x:
                assert(False), x


    def test_process_no_args(self):
        ing =  "a.b.c::d.e.f"
        obj = StrangBasicProcessor()
        match obj.pre_process(Strang, ing):
            case str() as x, {}, dict() as data, None:
                assert("args_start" not in data)
            case x:
                assert(False), x

class TestStrang_Process:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_process_section_bounds(self):
        ing                 = "a.b.c::d.e.f"
        obj                 = StrangBasicProcessor()
        base                = Strang(ing)
        base.data.sections  = ()
        assert(not bool(base.data.sections))
        obj.process(base, data={})
        assert(bool(base.data.sections))
        match base.data.sections:
            case [slice() as head, slice() as body]:
                assert(ing[head] == "a.b.c")
                assert(ing[body] == "d.e.f")
                assert(True)
            case x:
                 assert(False), x

    def test_process_words(self):
        ing              = "a.b.c.blah::d.e.f"
        obj              = StrangBasicProcessor()
        base             = Strang(ing)
        words            = ["a","b","c","blah","d","e","f"]
        base.data.words  = ()
        assert(not bool(base.data.words))
        obj.process(base, data={})
        assert(bool(base.data.words))
        match base.data.words:
            case [*xs]:
                assert(len(xs) == 7)
                for x,sl in zip(words, xs, strict=True):
                    assert(x == ing[sl])
            case x:
                 assert(False), x


    def test_process_word_idxs(self):
        ing              = "a.b.c.blah::d.e.f"
        obj              = StrangBasicProcessor()
        base             = Strang(ing)
        target_words            = ["a","b","c","blah","d","e","f"]
        base.data.sec_words = ()
        assert(not bool(base.data.sec_words))
        obj.process(base, data={})
        assert(bool(base.data.sec_words))
        actual_words = [base.data.words[y] for x in base.data.sec_words for y in x]
        for x,sl in zip(target_words, actual_words, strict=True):
            assert(x == ing[sl])

    def test_process_section_flat(self):
        ing              = "a.b.c.blah::d.e.f"
        words            = ["a","b","c","blah","d","e","f"]
        obj              = StrangBasicProcessor()
        base             = Strang(ing)
        base.data.words  = ()
        assert(not bool(base.data.words))
        obj.process(base, data={})
        match base.data.words:
            case [*xs]:
                assert(len(xs) == 7)
                for x,sl in zip(words, xs, strict=True):
                    assert(x == ing[sl])
            case x:
                assert(False), x


    def test_process_args(self):
        ing             = "a.b.c.blah::d.e.f[blah,bloo,blee]"
        words           = ["a","b","c","blah","d","e","f"]
        obj             = StrangBasicProcessor()
        ang             = Strang(ing)
        ang.data.args = None
        obj.process(ang, data={})
        assert(ang.data.args_start == ing.rindex(API.ARGS_CHARS[0]))
        assert(ang.data.sections[-1].stop <= ing.rindex(API.ARGS_CHARS[0]))
        assert(bool(ang.data.args))
        assert(set(ang.data.args) == set(["blah","bloo","blee"]))


    def test_process_args_set_uuid(self):
        ing                         = "a.b.c.blah::d.e.f[<uuid>]"
        words                       = ["a","b","c","blah","d","e","f"]
        obj                         = StrangBasicProcessor()
        _, _, post_data, _  = obj.pre_process(Strang, ing)
        ang                         = Strang(ing)
        ang.data.args               = None
        obj.process(ang, data=post_data)
        assert(ang.data.args_start  == ing.rindex(API.ARGS_CHARS[0]))
        assert(ang.data.sections[-1].stop <= ing.rindex(API.ARGS_CHARS[0]))
        assert(bool(ang.data.args))
        assert(set(ang.data.args) == set(["<uuid>"]))
        assert(isinstance(ang.data.uuid, UUID))


class TestStrang_PostProcess_UUIDs:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_head_uuids(self):
        obj = StrangBasicProcessor()
        val = Strang("a.b.c.<uuid>::d.e.f")
        val.data.uuid = None
        val.data.meta = ()
        assert(not bool(val.data.meta))
        assert(not val.uuid())
        obj.post_process(val, {"types": [("uuid", None)]})
        assert(bool(val.data.meta))
        assert(not val.uuid())
        match val.data.meta[3]:
            case UUID():
                assert(True)
            case x:
                assert(False), x

    def test_body_uuids(self):
        obj = StrangBasicProcessor()
        val = Strang("a.b.c::d.e.<uuid>")
        assert(not val.uuid())
        val.data.meta = ()
        assert(not bool(val.data.meta))
        obj.post_process(val, {"types" : [("uuid", None)]})
        assert(not val.uuid())
        match val.data.meta[-1]:
            case UUID():
                assert(True)
            case x:
                 assert(False), x

    def test_exact_uuid(self):
        obj = Strang(f"head::tail.<uuid:{UUID_STR}>")
        assert(not obj.uuid())
        match obj.get(1,-1):
            case uuid.UUID():
                assert(True)
            case x:
                 assert(False), type(x)

    def test_rebuild_uuid(self):
        ing = f"head::tail.<uuid:{UUID_STR}>"
        s1 = Strang(ing)
        s2 = Strang(s1[:,:])
        assert(s1.uuid() == s2.uuid())
        assert(isinstance(s1.get(1,-1), uuid.UUID))
        assert(isinstance(s2.get(1,-1), uuid.UUID))
        assert(s1.get(1,-1) == s2.get(1,-1))
        assert(s1[1,-1] == s2[1,-1])

    def test_rebuild_generated_uuid(self):
        s1 = Strang("head::tail.<uuid>")
        s2 = Strang(s1[:,:])
        assert(not s1.uuid())
        assert(not s1.uuid())
        assert(isinstance(s1.get(1,-1), uuid.UUID))
        assert(isinstance(s2.get(1,-1), uuid.UUID))
        assert(s1[:,:] == s2[:,:])

    def test_too_many_uuids(self):
        with pytest.raises(StrangError):
            Strang("head::tail[<uuid>,<uuid>]")


    def test_multiple_uuids(self):
        obj = Strang("head::tail.<uuid>.<uuid>")
        match obj.get(1,1), obj.get(1,2):
            case UUID(), UUID():
                assert(True)
            case x:
                assert(False), x

class TestStrang_PostProcess_Marks:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_head_marks(self):
        head           = API.DefaultHeadMarks_e
        obj            = StrangBasicProcessor()
        val            = Strang("a.b.$basic$::d.e.f")
        val.data.meta  = ()
        assert(not bool(val.data.meta))
        obj.post_process(val, {})
        assert(bool(val.data.meta))
        match val.data.meta[2]:
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
        obj.post_process(val, {})
        assert(bool(val.data.meta))
        match val.data.meta[-1]:
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
        obj.post_process(val, {})
        assert(bool(val.data.meta))
        match val.data.meta[1]:
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
        obj.post_process(val, {})
        assert(bool(val.data.meta))
        match val.data.meta[-1]:
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
        obj.post_process(val, {})
        assert(bool(val.data.meta))
        match val.data.meta[2]:
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
        obj.post_process(val, {})
        assert(bool(val.data.meta))
        match val.data.meta[1]:
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
