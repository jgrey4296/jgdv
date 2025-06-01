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
from jgdv import identity_fn

from ... import DKey, IndirectDKey
from ..._interface import ExpInst_d
from ..expander import DKeyExpander
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

class TestExpInst_d:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = ExpInst_d(value="blah", fallback="bloo")
        assert(obj.value == "blah")
        assert(obj.rec == -1)
        assert(obj.fallback == "bloo")

    def test_no_val_errors(self):
        with pytest.raises(KeyError):
            ExpInst_d(fallback="bloo")

    def test_match(self):
        match ExpInst_d(value="blah", fallback="bloo"):
            case ExpInst_d(value="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_match_fail(self):
        match ExpInst_d(value="bloo", fallback="bloo"):
            case ExpInst_d(rec=True):
                assert(False)
            case _:
                assert(True)

class TestExpander:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match DKeyExpander():
            case DKeyExpander() as x:
                assert(x._ctor is None)
            case x:
                assert(False), x

    def test_pre_lookup(self):
        pass

    def test_do_lookup(self):
        pass

    def test_pre_recurse(self):
        pass

    def test_do_recursion(self):
        pass

    def test_flatten(self):
        pass

    def test_coerce_result(self):
        pass

    def test_finalise(self):
        pass

    def test_check_result(self):
        pass

class TestExpansion:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = DKey("test", implicit=True)
        state = {"test": "blah"}
        match obj.expand(state):
            case "blah":
                assert(True)
            case x:
                assert(False), x

    def test_basic_fail(self):
        obj = DKey("aweg", implicit=True)
        state = {"test": "blah"}
        match obj.expand(state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_nonkey_expansion(self):
        obj = DKey("aweg")
        state = {"test": "blah"}
        match obj.expand(state):
            case "aweg":
                assert(True)
            case x:
                assert(False), x

    def test_simple_recursive(self):
        """
        {test} -> {blah} -> bloo
        """
        obj = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "bloo"}
        match obj.expand(state):
            case "bloo":
                assert(True)
            case x:
                assert(False), x

    def test_double_recursive(self):
        """
        {test} -> {blah} -> {aweg}/{bloo} -> qqqq/{aweg} -> qqqq/qqqq
        """
        obj = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}/{bloo}", "aweg":"qqqq", "bloo":"{aweg}"}
        match obj.expand(state):
            case "qqqq/qqqq":
                assert(True)
            case x:
                assert(False), x

    def test_coerce_type(self):
        obj = DKey("test", implicit=True, ctor=pl.Path)
        state = {"test": "blah"}
        match obj.expand(state):
            case pl.Path():
                assert(True)
            case x:
                assert(False), x

    def test_check_type(self):
        obj = DKey("test", implicit=True, ctor=pl.Path)
        state = {"test": pl.Path("blah")}
        match obj.expand(state):
            case pl.Path():
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
        {key} -> state[key:value] -> value
        """
        obj = DKey("test", implicit=True)
        state = {"test": "blah"}
        match obj.expand(state):
            case "blah":
                assert(True)
            case x:
                assert(False), x

    def test_hit_ignores_indirect(self):
        """
        {key} -> state[key:value, key_:val2] -> value
        """
        obj = DKey("test", implicit=True)
        state = {"test": "blah", "test_":"aweg"}
        match obj.expand(state):
            case "blah":
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss(self):
        """
        {key} -> state[] -> None
        """
        obj = DKey("test", implicit=True)
        state = {}
        match obj.expand(state):
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
        match obj.expand(state, fallback=25):
            case 25:
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_with_ctor_fallback(self):
        """
        {key} -> state[] -> 25
        """
        obj = DKey("test", fallback=25, implicit=True)
        state = {}
        match obj.expand(state):
            case 25:
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_prefer_call_fallback_over_ctor(self):
        """
        {key} -> state[] -> 25
        """
        obj = DKey("test", fallback=10, implicit=True)
        state = {}
        match obj.expand(state, fallback=25):
            case 25:
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_indirect(self):
        """
        {key_} -> state[] -> {key_}
        """
        obj = DKey("test_", implicit=True)
        assert(DKey.MarkOf(obj) == DKey.Marks.INDIRECT)
        state = {}
        match obj.expand(state):
            case DKey() as k if k == "test_":
                assert(DKey.MarkOf(k) == DKey.Marks.INDIRECT)
                assert(True)
            case x:
                assert(False), x

    def test_soft_miss(self):
        """
        {key} -> state[key_:blah] -> {blah}
        """
        obj = DKey("test", implicit=True)
        state = {"test_": "blah"}
        match obj.expand(state):
            case DKey() as k if k == "blah":
                assert(True)
            case x:
                assert(False), x

    def test_soft_hit_direct(self):
        """
        {key_} -> state[key:value] -> value
        """
        obj = DKey("test_", implicit=True)
        assert(DKey.MarkOf(obj) is DKey.Marks.INDIRECT)
        state = {"test": "blah"}
        match obj.expand(state):
            case "blah":
                assert(True)
            case x:
                assert(False), x

    def test_soft_hit_indirect(self):
        """
        {key_} -> state[key_:value] -> {value}
        """
        obj = DKey("test_", implicit=True)
        assert(DKey.MarkOf(obj) is DKey.Marks.INDIRECT)
        state = {"test_": "blah"}
        match obj.expand(state):
            case "blah":
                assert(True)
            case x:
                assert(False), x

    def test_indirect_prefers_indirect_over_direct(self):
        """
        {key_} -> state[key_:value, key:val2] -> {value}
        """
        obj = DKey("test_", implicit=True)
        assert(DKey.MarkOf(obj) is DKey.Marks.INDIRECT)
        state = {"test_": "blah", "test": "aweg"}
        match obj.expand(state):
            case "blah":
                assert(True)
            case x:
                assert(False), x

class TestMultiExpansion:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = DKey("{test} {test}")
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "blah"}
        match obj.expand(state):
            case "blah blah":
                assert(True)
            case x:
                assert(False), x

    def test_coerce_to_path(self):
        obj = DKey("{test}/{test}", ctor=pl.Path)
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "blah"}
        match obj.expand(state):
            case pl.Path():
                assert(True)
            case x:
                assert(False), x

    def test_coerce_subkey(self):
        obj = DKey("{test!p}/{test}")
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        assert(obj.keys()[0].data.convert == "p")
        state = {"test": "blah"}
        match obj.expand(state):
            case str() as x:
                assert(x == str(pl.Path.cwd() / "blah/blah"))
                assert(True)
            case x:
                assert(False), x

    def test_coerce_multi(self):
        obj = DKey("{test!p} : {test!p}")
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        assert(obj.keys()[0].data.convert == "p")
        state = {"test": "blah"}
        match obj.expand(state):
            case str() as x:
                assert(x == "".join([str(pl.Path.cwd() / "blah"),
                                    " : ",
                                    str(pl.Path.cwd() / "blah")]))
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_subkey(self):
        obj = DKey("{test}/{aweg}")
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "blah"}
        match obj.expand(state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_soft_miss_subkey(self):
        obj = DKey("{test}/{aweg}")
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "blah", "aweg_":"test"}
        match obj.expand(state):
            case "blah/blah":
                assert(True)
            case x:
                assert(False), x

    def test_indirect_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "blah", "aweg_":"test"}
        match obj.expand(state):
            case "blah/blah":
                assert(True)
            case x:
                assert(False), x

    def test_indirect_key_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "blah", "aweg":"test"}
        match obj.expand(state):
            case "blah/test":
                assert(True)
            case x:
                assert(False), x

    def test_indirect_miss_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "blah"}
        match obj.expand(state):
            case "blah/{aweg_}":
                assert(True)
            case x:
                assert(False), x

    def test_multikey_of_one(self):
        obj = DKey("{test}", mark=DKey.Marks.MULTI)
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "{blah}", "blah": "blah/{aweg_}"}
        match obj.expand(state):
            case "blah/{aweg_}":
                assert(True)
            case x:
                assert(False), x

    def test_multikey_recursion(self):
        obj = DKey("{test}", mark=DKey.Marks.MULTI)
        assert(DKey.MarkOf(obj) is DKey.Marks.MULTI)
        state = {"test": "{test}", "blah": "blah/{aweg_}"}
        match obj.expand(state, limit=10):
            case "test":
                assert(True)
            case x:
                assert(False), x

class TestCoercion:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_coerce_param_path(self):
        obj = DKey("{test!p}")
        state = {"test": "blah"}
        assert(obj.data.convert == "p")
        match obj.expand(state):
            case pl.Path():
                assert(True)
            case x:
                assert(False), x

    def test_coerce_param_int(self):
        obj = DKey("{test!i}")
        state = {"test": "25"}
        assert(obj.data.convert == "i")
        match obj.expand(state):
            case 25:
                assert(True)
            case x:
                assert(False), x

    def test_coerce_param_fail(self):
        obj = DKey("{test!i}")
        state = {"test": "blah"}
        assert(obj.data.convert == "i")
        with pytest.raises(ValueError):
            obj.expand(state)

class TestFallbacks:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_fallback(self):
        key = DKey("blah", implicit=True, fallback="aweg")
        match key():
            case "aweg":
                assert(True)
            case x:
                 assert(False), x

    def test_fallback_typecheck(self):
        key = DKey("blah", implicit=True, fallback="aweg", check=str)
        match key():
            case "aweg":
                assert(True)
            case x:
                 assert(False), x

    @pytest.mark.parametrize("ctor", [list, dict, set])
    def test_fallback_type_factory(self, ctor):
        key = DKey("blah", implicit=True, fallback=ctor)
        match key():
            case list()|dict()|set():
                assert(True)
            case x:
                 assert(False), x
