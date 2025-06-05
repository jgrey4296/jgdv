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
from jgdv.structs.strang.errors import StrangError
from ..dkey import DKey
from ..keys import SingleDKey, MultiDKey, NonDKey, IndirectDKey

# ##-- types
# isort: off
import abc
import collections.abc
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

class TestSingleDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_ctor(self):
        assert(DKey.MarkOf(SingleDKey) == DKey.Marks.FREE)

    def test_basic(self):
        match DKey("blah", implicit=True, force=SingleDKey):
            case SingleDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, SingleDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
            case x:
                assert(False), x


    def test_basic_by_class_accesss(self):
        match DKey[DKey.Marks.FREE]("blah", implicit=True):
            case SingleDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, SingleDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
            case x:
                assert(False), x


    def test_fail_on_multiple_keys(self):
        with pytest.raises(StrangError):
            DKey("{blah} awef {bloo}", force=SingleDKey)

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

    def test_str(self):
        obj1 = DKey("{blah}")
        obj2 = "blah"
        assert(obj1 == obj2)

    def test_format_wrapped(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        obj2 = "{blah}"
        assert(f"{obj1:w}" == obj2)

    def test_format_indirect(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        obj2 = "blah_"
        assert(f"{obj1:i}" == obj2)

    def test_format_indirect_wrapped(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        obj2 = "{blah_}"
        assert(f"{obj1:wi}" == obj2)

    def test_getitem_key_fails(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        with pytest.raises(IndexError):
            obj1[0,0]

    def test_get_key_basic(self):
        obj1 = DKey("blah", implicit=True, force=SingleDKey)
        with pytest.raises(IndexError):
            obj1.get(0,0)

    def test_get_key_from_wrapped(self, force=SingleDKey):
        obj1 = DKey("{blah}")
        with pytest.raises(IndexError):
            obj1.get(0,0)

class TestMultiDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match DKey("{blah} {bloo}", force=MultiDKey):
            case MultiDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, MultiDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
            case x:
                assert(False), x


    def test_basic_by_class_access(self):
        match DKey[DKey.Marks.MULTI]("{blah} {bloo}"):
            case MultiDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, MultiDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
            case x:
                assert(False), x


    def test_basic_unannotated(self):
        match DKey("{blah} {bloo}"):
            case MultiDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, MultiDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
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
        obj = DKey("{first} {second} {third}", force=MultiDKey)
        assert(isinstance(obj, MultiDKey))
        for sub in obj.keys():
            assert(isinstance(sub, SingleDKey)), type(sub)

    def test_subkeys_two(self):
        obj = DKey("{test} then {blah}")
        assert(isinstance(obj, MultiDKey))
        assert(len(obj.keys()) == 2)

    def test_anon(self):
        obj = DKey("{first} {second} {third}", force=MultiDKey)
        assert(isinstance(obj, MultiDKey))
        assert(obj.anon == "{} {} {}")

    def test_anon_2(self):
        obj = DKey("{b}", mark=DKey.Marks.MULTI)
        assert(isinstance(obj, MultiDKey))
        assert(obj.anon == "{}")

    def test_hash(self):
        obj1 = DKey("{blah}", force=MultiDKey)
        assert(isinstance(obj1, MultiDKey))
        obj2 = "blah"
        assert(hash(obj1) == hash(obj2))

    def test_multikey_hash(self):
        obj1 = DKey("{blah} blee {bloo}", force=MultiDKey)
        obj2 = "{blah} blee {bloo}"
        assert(hash(obj1) == hash(obj2))

    def test_str(self):
        obj1 = DKey("{blah} {bloo}", mark=DKey.Marks.MULTI)
        obj2 = "{blah} {bloo}"
        assert(obj1[:] == obj2)
        assert(str(obj1) == obj2)

    def test_getitem_succeeds(self):
        obj1 = DKey("{blah} {bloo}", mark=DKey.Marks.MULTI)
        assert(obj1[0,0] == "{blah}")
        assert(obj1[0,1] == "{bloo}")

    def test_get_succeeds(self):
        obj1 = DKey("{blah} {bloo}", mark=DKey.Marks.MULTI)
        assert(obj1.get(0,0) == "blah")
        assert(obj1.get(0,1) == "bloo")

class TestNonDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match DKey("blah", force=NonDKey):
            case NonDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, NonDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
            case x:
                assert(False), x


    def test_basic_by_class_access(self):
        match DKey[DKey.Marks.NULL]("blah"):
            case NonDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, NonDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
            case x:
                assert(False), x


    def test_basic_unannotated(self):
        match DKey("blah"):
            case NonDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, NonDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
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


    def test_format(self):
        obj1 = DKey("blah", implicit=False, force=NonDKey)
        assert(str(obj1) == f"{obj1:w}")
        assert(str(obj1) == f"{obj1:i}")
        assert(str(obj1) == f"{obj1:wi}")

class TestIndirectDKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    @pytest.mark.parametrize("name", ["blah", "blah_"])
    def test_basic(self, name):
        match DKey(name, implicit=True, force=IndirectDKey):
            case IndirectDKey() as x:
                assert(not hasattr(x, "__dict__"))
                assert(isinstance(x, IndirectDKey))
                assert(isinstance(x, DKey))
                assert(isinstance(x, Strang))
                assert(isinstance(x, str))
            case x:
                assert(False), x

    def test_basic_by_class_access(self):
        match DKey[DKey.Marks.INDIRECT]("{blah}"):
            case IndirectDKey():
                assert(True)
            case x:
                assert(False), type(x)

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
        obj1 = DKey("blah", force=IndirectDKey, implicit=True)
        obj2 = "blah_"
        assert(obj1 == obj2)

    def test_eq_not_implemented(self):
        obj1 = DKey("blah", force=IndirectDKey, implicit=True)
        obj2 = 21
        assert(isinstance(obj1, IndirectDKey))
        assert(not (obj1 == obj2))

    def test_hash_eq_trimmed(self):
        obj1 = DKey("blah_", implicit=True, force=IndirectDKey)
        obj2 = "blah"
        assert(hash(obj1) == hash(obj2))
