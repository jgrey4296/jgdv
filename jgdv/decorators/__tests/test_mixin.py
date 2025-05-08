#!/usr/bin/env python3
"""

"""
# ruff: noqa: B011
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import warnings
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest

# ##-- end 3rd party imports

# ##-- 1st party imports
from .. import _interface as API
from .._core import (
    Decorator,
    IdempotentDec,
    MonotonicDec,
)

from jgdv.decorators.mixin import Mixin
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

logging = logmod.root

##-- mixins

class Simple_m:

    def blah(self):
        return 2

    def bloo(self):
        return 4

class Second_m:

    def aweg(self):
        return super().bloo()

##-- end mixins

##-- super chain

class ChainBase:

    def vals(self) -> list:
        return ["ChainBase"]

class m1:

    def vals(self) -> list:
        return ["m1", *super().vals()]

class m2:

    def vals(self) -> list:
        return ["m2", *super().vals()]

class m3:

    def vals(self) -> list:
        return ["m3", *super().vals()]

##-- end super chain

class TestMixinDecorator:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):

        @Mixin(None, Simple_m)
        class Example:

            def bloo(self):
                return 10

        obj = Example()
        assert(obj.blah() == 2)
        assert(obj.bloo() == 10)

    def test_two_mixins(self):

        @Mixin(None, Second_m, Simple_m)
        class Example:

            def bloo(self):
                return 10

        obj = Example()
        assert(obj.blah() == 2)
        assert(obj.bloo() == 10)
        # Aweg->super()->Simple_m.bloo
        assert(obj.aweg() == 4)

    def test_append_mixin(self):

        @Mixin(Second_m, None, Simple_m)
        class Example:
            val : ClassVar[int] = 25

            def bloo(self):
                return 10

        obj = Example()
        assert(obj.blah() == 2)
        assert(obj.bloo() == 10)
        # Aweg->super()->Example.bloo
        assert(obj.aweg() == 10)
        assert(Example.val == 25)

    def test_super_chain_traditional(self):

        class ChainTop(m1, m2, m3, ChainBase):

            def vals(self) -> list:
                return ["ChainTop", *super().vals()]

        obj      = ChainTop()
        real     = obj.vals()
        expected = ["ChainTop", "m1", "m2", "m3", "ChainBase"]
        for x,y in zip(real, expected, strict=True):
            assert(x == y), real

    def test_pre_super_chain_decorated(self):

        @Mixin(m1, m2, m3, None)
        class PreChainTop(ChainBase):

            def vals(self) -> list:
                return ["ChainTop", *super().vals()]

        obj     = PreChainTop()
        real     = obj.vals()
        expected = ["m1", "m2", "m3", "ChainTop", "ChainBase"]
        for x,y in zip(real, expected, strict=True):
            assert(x == y), real

    def test_post_super_chain_decorated(self):

        @Mixin(None, m1, m2, m3)
        class PostChainTop(ChainBase):

            def vals(self) -> list:
                return ["ChainTop", *super().vals()]

        obj      = PostChainTop()
        real     = obj.vals()
        expected = ["ChainTop", "m1", "m2", "m3", "ChainBase"]
        for x,y in zip(real, expected, strict=True):
            assert(x == y), real

    def test_spit_super_chain_decorated(self):

        @Mixin(m1, None, m2, m3)
        class PostChainTop(ChainBase):

            def vals(self) -> list:
                return ["ChainTop", *super().vals()]

        obj      = PostChainTop()
        real     = obj.vals()
        expected = ["m1", "ChainTop", "m2", "m3", "ChainBase"]
        for x,y in zip(real, expected, strict=True):
            assert(x == y), real


    def test_multi_dec_super_chain(self):

        @Mixin(m1, None)
        @Mixin(m2, m3)
        class PostChainTop(ChainBase):

            def vals(self) -> list:
                return ["ChainTop", *super().vals()]

        obj      = PostChainTop()
        real     = obj.vals()
        expected = ["m1", "ChainTop", "m2", "m3", "ChainBase"]
        for x,y in zip(real, expected, strict=True):
            assert(x == y), real

    def test_duplicate_errors(self):

        with pytest.raises(TypeError):

            @Mixin(m1, m1)
            class PostChainTop(ChainBase):
                pass
