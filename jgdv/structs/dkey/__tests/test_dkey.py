#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202, B011

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

from jgdv.structs.strang import Strang
from jgdv.mixins.annotate._interface import Default_K
from ..dkey import DKey
from ..keys import SingleDKey, NonDKey

# ##-- types
# isort: off
import abc
import collections.abc
import types
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

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

class TestBaseDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_registry_default(self):
        assert(DKey._registry[Default_K] is SingleDKey)

    def test_class_getitem(self):
        val = DKey['blah']
        assert(val is not None)
        assert(isinstance(val, types.GenericAlias))

    def test_basic_implicit(self):
        match DKey("blah", implicit=True):
            case NonDKey():
                assert(False)
            case DKey() as obj:
                assert(not hasattr(obj, "__dict__"))
                assert(isinstance(obj, str))
                assert(isinstance(obj, Strang))
                assert(hasattr(obj, "__hash__"))
            case x:
                assert(False), x

    def test_basic_explicit(self):
        match DKey("{blah}"):
            case NonDKey():
                assert(False)
            case DKey() as obj:
                assert(not hasattr(obj, "__dict__"))
                assert(isinstance(obj, str))
                assert(isinstance(obj, Strang))
                assert(hasattr(obj, "__hash__"))
            case x:
                assert(False), x

    def test_expansion_limit_format_params(self):
        match DKey("blah:e2", implicit=True):
            case DKey() as obj:
                assert(bool(obj.data.raw[0].format))
                assert(obj.data.raw[0].format == "e2")
                assert(obj.data.max_expansions == 2)
            case x:
                assert(False), x


    def test_multikey_expansion_limit_format_params(self):
        obj = DKey("{blah:e2} {bloo:e3}")
        match obj.keys():
            case [x,y]:
                assert(x.data.max_expansions == 2)
                assert(y.data.max_expansions == 3)
            case x:
                assert(False), x

    def test_hashable_implicit(self):
        obj = DKey("blah", implicit=True)
        assert(hash(obj))

    def test_hashable_explicit(self):
        obj = DKey("{blah}")
        assert(hash(obj))

    def test_eq(self):
        obj1 = DKey("blah", implicit=True)
        obj2 = DKey("blah", implicit=True)
        assert(obj1 == obj2)

    def test_eq_str(self):
        obj1 = DKey("blah", implicit=True)
        obj2 = "blah"
        assert(obj1 == obj2)

    def test_eq_not_implemented(self):
        obj1 = DKey("blah", implicit=True)
        obj2 = 21
        assert(not (obj1 == obj2))

class TestDKey_Format:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_format_indirect(self):
        obj = DKey("{blah}")
        assert(f"{obj:i}" == "blah_")

    def test_format_direct(self):
        obj = DKey("{blah}")
        assert(f"{obj:d}" == "blah")

    def test_format_wrapped(self):
        obj = DKey("{blah}")
        assert(f"{obj:w}" == "{blah}")

    def test_format_wrapped_indirect(self):
        obj = DKey("{blah}")
        assert(f"{obj:wi}" == "{blah_}")
