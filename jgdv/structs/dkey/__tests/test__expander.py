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
from jgdv.structs.dkey import DKey
from jgdv import identity_fn

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

class TestExpansion:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = DKey("test", implicit=True)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case "blah":
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
            case "aweg":
                assert(True)
            case x:
                assert(False), x

    def test_recursive(self):
        obj = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "bloo"}
        match obj.local_expand(state):
            case "bloo":
                assert(True)
            case x:
                assert(False), x

    def test_coerce_type(self):
        obj = DKey("test", implicit=True, ctor=pl.Path)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case pl.Path():
                assert(True)
            case x:
                assert(False), x

    def test_check_type(self):
        obj = DKey("test", implicit=True, check=pl.Path)
        assert(obj._expansion_type is identity_fn)
        state = {"test": pl.Path("blah")}
        match obj.local_expand(state):
            case pl.Path():
                assert(True)
            case x:
                assert(False), x

    def test_limited_depth_expansion(self):
        obj = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}", "aweg": "qqqq"}
        match obj.local_expand(state, limit=1):
            case "{blah}":
                assert(True)
            case x:
                assert(False), x

class TestIndirection:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_hit(self):
        """
        {key} -> state[key:val] -> val
        """
        obj = DKey("test", implicit=True)
        state = {"test": "blah"}
        match obj.local_expand(state, limit=1):
            case "blah":
                assert(True)
            case x:
                assert(False), x

    def test_hit_ignores_indirect(self):
        """
        {key} -> state[key:val, key_:val2] -> val
        """
        obj = DKey("test", implicit=True)
        state = {"test": "blah", "test_":"aweg"}
        match obj.local_expand(state, limit=1):
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
        match obj.local_expand(state, limit=1):
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
        match obj.local_expand(state, fallback=25, limit=1):
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
        match obj.local_expand(state, limit=1):
            case 25:
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_with_ctor_hierarchy(self):
        """
        {key} -> state[] -> 25
        """
        obj = DKey("test", fallback=10, implicit=True)
        state = {}
        match obj.local_expand(state, fallback=25, limit=1):
            case 25:
                assert(True)
            case x:
                assert(False), x

    def test_soft_miss(self):
        """
        {key} -> state[key_:val] -> {val_}
        """
        obj = DKey("test", implicit=True)
        state = {"test_": "blah"}
        match obj.local_expand(state, limit=1):
            case DKey() as x:
                assert(x == "blah")
                assert(True)
            case x:
                assert(False), x

    def test_indirect_hit_direct(self):
        """
        {key_} -> state[key:val] -> val
        """
        obj = DKey("test_", implicit=True)
        state = {"test": "blah"}
        match obj.local_expand(state, limit=1):
            case "blah":
                assert(True)
            case x:
                assert(False), x

    def test_indirect_hit_indirect(self):
        """
        {key_} -> state[key_:val] -> {val}
        """
        obj = DKey("test_", implicit=True)
        state = {"test_": "blah"}
        match obj.local_expand(state, limit=1):
            case DKey() as k:
                assert(k == "blah")
                assert(True)
            case x:
                assert(False), x

    def test_indirect_miss(self):
        """
        {key_} -> state[] -> {key_}
        """
        obj = DKey("test_", implicit=True)
        state = {}
        match obj.local_expand(state, limit=1):
            case DKey() as k:
                assert(k == "test_")
            case x:
                assert(False), x

class TestMultiExpansion:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = DKey("{test} {test}")
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case "blah blah":
                assert(True)
            case x:
                assert(False), x

    def test_coerce_to_path(self):
        obj = DKey("{test}/{test}", ctor=pl.Path)
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case pl.Path():
                assert(True)
            case x:
                assert(False), x

    def test_coerce_subkey(self):
        obj = DKey("{test!p}/{test}")
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        assert(obj.keys()[0]._conv_params == "p")
        state = {"test": "blah"}
        match obj.local_expand(state):
            case str() as x:
                assert(x == str(pl.Path.cwd() / "blah/blah"))
                assert(True)
            case x:
                assert(False), x


    def test_coerce_multi(self):
        obj = DKey("{test!p} : {test!p}")
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        assert(obj.keys()[0]._conv_params == "p")
        state = {"test": "blah"}
        match obj.local_expand(state):
            case str() as x:
                assert(x == "".join([str(pl.Path.cwd() / "blah"),
                                    " : ",
                                    str(pl.Path.cwd() / "blah")]))
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_subkey(self):
        obj = DKey("{test}/{aweg}")
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_soft_miss_subkey(self):
        obj = DKey("{test}/{aweg}")
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        state = {"test": "blah", "aweg_":"test"}
        match obj.local_expand(state):
            case "blah/blah":
                assert(True)
            case x:
                assert(False), x

    def test_indirect_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        state = {"test": "blah", "aweg_":"test"}
        match obj.local_expand(state):
            case "blah/blah":
                assert(True)
            case x:
                assert(False), x

    def test_indirect_key_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        state = {"test": "blah", "aweg":"test"}
        match obj.local_expand(state):
            case "blah/test":
                assert(True)
            case x:
                assert(False), x


    def test_indirect_miss_subkey(self):
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is DKey.mark.MULTI)
        state = {"test": "blah"}
        match obj.local_expand(state):
            case "blah/{aweg_}":
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
            case pl.Path():
                assert(True)
            case x:
                assert(False), x

    def test_coerce_param_int(self):
        obj = DKey("{test!i}")
        state = {"test": "25"}
        assert(obj._conv_params == "i")
        match obj.local_expand(state):
            case int() as x:
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
