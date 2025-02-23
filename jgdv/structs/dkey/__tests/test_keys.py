#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202

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

from jgdv.structs.dkey import DKey, DKeyBase
from jgdv.structs.dkey.keys import SingleDKey, MultiDKey, NonDKey, IndirectDKey

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

class TestSingleDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_must_force(self):
        with pytest.raises(RuntimeError):
            SingleDKey("blah", force=False)

    def test_basic(self):
        match DKey("blah", implicit=True, force=SingleDKey):
            case SingleDKey():
                assert(True)
            case x:
                assert(False), x

    def test_eq(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        obj2 = DKey("blah", implicit=True, force=SingleDKey)
        assert(obj1 == obj2)

    def test_eq_str(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        obj2 = "blah"
        assert(obj1 == obj2)

    def test_eq_not_implemented(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        obj2 = 21
        assert(not (obj1 == obj2))

    def test_hash(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        obj2 = "blah"
        assert(hash(obj1) == hash(obj2))

class TestMultiDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_must_force(self):
        with pytest.raises(RuntimeError):
            MultiDKey("blah", force=False)

    def test_basic(self):
        match DKey("{blah} {bloo}", force=MultiDKey):
            case MultiDKey():
                assert(True)
            case x:
                assert(False), x

    def test_eq(self):
        obj1 = DKey("{blah} {bloo}", force=MultiDKey)
        obj2 = DKey("{blah} {bloo}", force=MultiDKey)
        assert(obj1 == obj2)

    def test_eq_str(self):
        obj1 = DKey("{blah} {bloo}", force=MultiDKey)
        obj2 = "{blah} {bloo}"
        assert(obj1 == obj2)

    def test_eq_not_implemented(self):
        obj1 = DKey("{blah} {bloo}", force=MultiDKey)
        obj2 = 21
        assert(not (obj1 == obj2))

    def test_subkeys(self):
        obj = DKey("{first} {second} {third}")
        for sub in obj.keys():
            assert(isinstance(sub, SingleDKey))

    def test_anon(self):
        obj = DKey("{first} {second} {third}")
        assert(obj._anon == "{} {} {}")

    def test_anon_2(self):
        obj = DKey("{b}", mark=DKey.Mark.MULTI)
        assert(isinstance(obj, MultiDKey))
        assert(obj._anon == "{}")

    def test_hash(self):
        obj1 = DKey("{blah}", mark=DKey.Mark.MULTI)
        obj2 = "{blah}"
        assert(hash(obj1) == hash(obj2))

class TestNonDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_must_force(self):
        with pytest.raises(RuntimeError):
            NonDKey("blah", force=False)

    def test_basic(self):
        match DKey("blah", force=NonDKey):
            case NonDKey():
                assert(True)
            case x:
                assert(False), x

    def test_eq(self):
        obj1 = DKey("blah", force=NonDKey)
        obj2 = DKey("blah", force=NonDKey)
        assert(obj1 == obj2)

    def test_eq_str(self):
        obj1 = DKey("blah", force=NonDKey)
        obj2 = "blah"
        assert(obj1 == obj2)

    def test_eq_not_implemented(self):
        obj1 = DKey("blah", force=NonDKey)
        obj2 = 21
        assert(not (obj1 == obj2))

    def test_hash(self):
        obj1 = DKey("blah", implicit=False, force=NonDKey)
        obj2 = "blah"
        assert(hash(obj1) == hash(obj2))

class TestIndirectDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_must_force(self):
        with pytest.raises(RuntimeError):
            IndirectDKey("blah", force=False)

    @pytest.mark.parametrize("name", ["blah", "blah_"])
    def test_basic(self, name):
        match DKey(name, force=IndirectDKey):
            case IndirectDKey():
                assert(True)
            case x:
                assert(False), x

    @pytest.mark.parametrize("name", ["blah", "blah_"])
    def test_eq(self, name):
        obj1 = DKey(name, implicit=True, force=IndirectDKey)
        obj2 = DKey(name, implicit=True, force=IndirectDKey)
        assert(obj1 == obj2)

    @pytest.mark.parametrize("name", ["blah"])
    def test_eq_with_underscore(self, name):
        obj1 = DKey(name, implicit=True, force=IndirectDKey)
        obj2 = DKey(f"{name}_", implicit=True, force=IndirectDKey)
        assert(obj1 == obj2)

    @pytest.mark.parametrize("name", ["blah", "blah_"])
    def test_eq_str(self, name):
        obj1 = DKey(name, implicit=True, force=IndirectDKey)
        obj2 = name
        assert(obj1 == obj2)

    def test_eq_indirect(self):
        obj1 = DKey("blah", force=IndirectDKey)
        obj2 = "blah_"
        assert(obj1 == obj2)

    def test_eq_not_implemented(self):
        obj1 = DKey("blah", force=IndirectDKey)
        obj2 = 21
        assert(not (obj1 == obj2))

    def test_hash(self):
        obj1 = DKey("blah_", implicit=True, force=IndirectDKey)
        obj2 = "blah_"
        assert(hash(obj1) == hash(obj2))
