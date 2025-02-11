#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202, B011

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings

# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv.structs.dkey import DKey, IndirectDKey
from jgdv import identity_fn

from jgdv.structs.dkey._expander import ExpInst
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class TestExpInst:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = ExpInst("blah", fallback="bloo")
        assert(obj.val == "blah")
        assert(obj.rec == -1)
        assert(obj.fallback == "bloo")

    def test_match(self):
        match ExpInst("blah", fallback="bloo"):
            case ExpInst(val="blah"):
                assert(True)
            case x:
                assert(False), x


    def test_match_fail(self):
        match ExpInst("bloo", fallback="bloo"):
            case ExpInst(rec=True):
                assert(False)
            case _:
                assert(True)

class TestExpansion:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = DKey("test", implicit=True)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val="blah", literal=True):
                assert(True)
            case x:
                assert(False), x

    def test_basic_fail(self):
        obj = DKey("aweg", implicit=True)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_nonkey_expansion(self):
        obj = DKey("aweg")
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val="aweg", literal=True):
                assert(True)
            case x:
                assert(False), x

    def test_simple_recursive(self):
        """
        {test} -> {blah} -> bloo
        """
        obj = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "bloo"}
        match obj.local_expand(state):
            case ExpInst(val="bloo"):
                assert(True)
            case x:
                assert(False), x


    def test_double_recursive(self):
        """
        {test} -> {blah} -> {aweg}/{bloo} -> qqqq/{aweg} -> qqqq/qqqq
        """
        obj = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}/{bloo}", "aweg":"qqqq", "bloo":"{aweg}"}
        match obj.local_expand(state):
            case ExpInst(val="qqqq/qqqq"):
                assert(True)
            case x:
                assert(False), x

    def test_coerce_type(self):
        obj = DKey("test", implicit=True, ctor=pl.Path)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val=pl.Path()):
                assert(True)
            case x:
                assert(False), x

    def test_check_type(self):
        obj = DKey("test", implicit=True, ctor=pl.Path)
        state = {"test": pl.Path("blah")}
        match obj.local_expand(state):
            case ExpInst(val=pl.Path()):
                assert(True)
            case x:
                assert(False), x

    def test_expansion_cascade(self):
        """ {test} -> {blah},
        *not* qqqq
        """
        obj = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}", "aweg": "qqqq"}
        assert(obj.expand(state, limit=1) == "blah")
        assert(obj.expand(state, limit=2) == "aweg")
        assert(obj.expand(state, limit=3) == "qqqq")


    @pytest.mark.skip("TODO")
    def test_additional_sources_recurse(self):
        """ see doot test_dkey.TestDKeyExpansion.test_indirect_wrapped_expansion
        """
        assert(False)


class TestIndirection:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_hit(self):
        """
        {key} -> state[key:val] -> val
        """
        obj = DKey("test", implicit=True)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_hit_ignores_indirect(self):
        """
        {key} -> state[key:val, key_:val2] -> val
        """
        obj = DKey("test", implicit=True)
        state = {"test": "blah", "test_":"aweg"}
        match obj.local_expand(state):
            case ExpInst(val="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss(self):
        """
        {key} -> state[] -> None
        """
        obj = DKey("test", implicit=True)
        state = {}
        match obj.local_expand(state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_with_call_fallback(self):
        """
        {key} -> state[] -> 25
        """
        obj = DKey("test", implicit=True)
        state = {}
        match obj.local_expand(state, fallback=25):
            case ExpInst(val=25):
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_with_ctor_fallback(self):
        """
        {key} -> state[] -> 25
        """
        obj = DKey("test", fallback=25, implicit=True)
        state = {}
        match obj.local_expand(state):
            case ExpInst(val=25):
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_prefer_call_fallback_over_ctor(self):
        """
        {key} -> state[] -> 25
        """
        obj = DKey("test", fallback=10, implicit=True)
        state = {}
        match obj.local_expand(state, fallback=25):
            case ExpInst(val=25):
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_indirect(self):
        """
        {key_} -> state[] -> {key_}
        """
        obj = DKey("test_", implicit=True)
        assert(obj._mark is DKey.Mark.INDIRECT)
        state = {}
        match obj.local_expand(state):
            case ExpInst(val=DKey() as k) if k == "test_":
                assert(k._mark is DKey.Mark.INDIRECT)
                assert(True)
            case x:
                assert(False), x
    def test_soft_miss(self):
        """
        {key} -> state[key_:blah] -> {blah}
        """
        obj = DKey("test", implicit=True)
        state = {"test_": "blah"}
        match obj.local_expand(state):
            case ExpInst(val=DKey() as x) if x == "blah":
                assert(True)
            case x:
                assert(False), x

    def test_soft_hit_direct(self):
        """
        {key_} -> state[key:val] -> val
        """
        obj = DKey("test_", implicit=True)
        assert(obj._mark is DKey.Mark.INDIRECT)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val=str() as x) if str(x) == "blah":
                assert(True)
            case x:
                assert(False), x

    def test_soft_hit_indirect(self):
        """
        {key_} -> state[key_:val] -> {val}
        """
        obj = DKey("test_", implicit=True)
        assert(obj._mark is DKey.Mark.INDIRECT)
        state = {"test_": "blah"}
        match obj.local_expand(state):
            case ExpInst(val=DKey() as k) if str(k) == "blah":
                assert(True)
            case x:
                assert(False), x


class TestMultiExpansion:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = DKey("{test} {test}")
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val="blah blah"):
                assert(True)
            case x:
                assert(False), x

    def test_coerce_to_path(self):
        obj = DKey("{test}/{test}", ctor=pl.Path)
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val=pl.Path()):
                assert(True)
            case x:
                assert(False), x

    def test_coerce_subkey(self):
        obj = DKey("{test!p}/{test}")
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        assert(obj.keys()[0]._conv_params == "p")
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val=str() as x):
                assert(x == str(pl.Path.cwd() / "blah/blah"))
                assert(True)
            case x:
                assert(False), x

    def test_coerce_multi(self):
        obj = DKey("{test!p} : {test!p}")
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        assert(obj.keys()[0]._conv_params == "p")
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val=str() as x):
                assert(x == "".join([str(pl.Path.cwd() / "blah"),
                                    " : ",
                                    str(pl.Path.cwd() / "blah")]))
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_subkey(self):
        obj = DKey("{test}/{aweg}")
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_soft_miss_subkey(self):
        obj = DKey("{test}/{aweg}")
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "blah", "aweg_":"test"}
        match obj.local_expand(state):
            case ExpInst(val="blah/blah"):
                assert(True)
            case x:
                assert(False), x

    def test_indirect_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "blah", "aweg_":"test"}
        match obj.local_expand(state):
            case ExpInst(val="blah/blah"):
                assert(True)
            case x:
                assert(False), x

    def test_indirect_key_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "blah", "aweg":"test"}
        match obj.local_expand(state):
            case ExpInst(val="blah/test"):
                assert(True)
            case x:
                assert(False), x

    def test_indirect_miss_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case ExpInst(val="blah/{aweg_}"):
                assert(True)
            case x:
                assert(False), x


    def test_multikey_of_one(self):
        obj = DKey("{test}", mark=DKey.Mark.MULTI)
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "{blah}", "blah": "blah/{aweg_}"}
        match obj.local_expand(state):
            case ExpInst(val="blah/{aweg_}"):
                assert(True)
            case x:
                assert(False), x


    def test_multikey_recursion(self):
        obj = DKey("{test}", mark=DKey.Mark.MULTI)
        assert(DKey.MarkOf(obj) is DKey.Mark.MULTI)
        state = {"test": "{test}", "blah": "blah/{aweg_}"}
        match obj.local_expand(state, limit=10):
            case ExpInst(val=str() as x) if x == "test":
                assert(True)
            case x:
                assert(False), x

class TestCoercion:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_coerce_param_path(self):
        obj = DKey("{test!p}")
        state = {"test": "blah"}
        assert(obj._conv_params == "p")
        match obj.local_expand(state):
            case ExpInst(val=pl.Path()):
                assert(True)
            case x:
                assert(False), x

    def test_coerce_param_int(self):
        obj = DKey("{test!i}")
        state = {"test": "25"}
        assert(obj._conv_params == "i")
        match obj.local_expand(state):
            case ExpInst(val=int() as x):
                assert(x == 25)
                assert(True)
            case x:
                assert(False), x

    def test_coerce_param_fail(self):
        obj = DKey("{test!i}")
        state = {"test": "blah"}
        assert(obj._conv_params == "i")
        with pytest.raises(ValueError):
            obj.local_expand(state)
