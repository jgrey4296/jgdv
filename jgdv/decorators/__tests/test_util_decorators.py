#!/usr/bin/env python3
"""
TEST File updated

"""
# ruff: noqa: ANN202, B011

# Imports
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest
# ##-- end 3rd party imports

from ..util_decorators import MethodMaybe, FnMaybe
from typing import reveal_type

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
DoMaybe_M = MethodMaybe()
DoMaybe_F = FnMaybe()

# Body:
class TestSuite:

    ##--|
    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133


    def test_basic_method(self) -> None:

        class Example:

            @DoMaybe_M
            def bfunc(self, val:int) -> Maybe[int]:
                return val

        reveal_type(Example.bfunc)
        obj = Example()
        match obj.bfunc(2):
            case 2:
                assert(True)
            case x:
                assert(False), x

        match obj.bfunc(None):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_basic_fn(self) -> None:

        @DoMaybe_F
        def bfunc(val:int, val2:str) -> Maybe[int]:
            return val

        reveal_type(bfunc)
        match bfunc(2, "blah"):
            case 2:
                assert(True)
            case x:
                assert(False), x

        match bfunc(None, "blah"):
            case None:
                assert(True)
            case x:
                assert(False), x
