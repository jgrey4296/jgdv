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

from jgdv.structs.dkey._parser import RawKey, DKeyParser

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

class TestRawKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match RawKey(prefix="", key="blah"):
            case RawKey():
                assert(True)
            case x:
                assert(False), x


    def test_joined(self):
        match RawKey(prefix="", key="blah", conv="p"):
            case RawKey() as x if x.joined() == "blah!p":
                assert(True)
            case x:
                assert(False), x


    @pytest.mark.parametrize("name", ["blah", "bloo", "blee", "aweg"])
    def test_wrapped(self, name):
        match RawKey(prefix="", key=name):
            case RawKey() as x if x.wrapped() == f"{{{name}}}":
                assert(True)
            case x:
                assert(False), x


    @pytest.mark.parametrize("name", ["blah", "bloo_", "blee_", "aweg"])
    def test_indirect(self, name):
        ind = "".join([name.removesuffix("_"), "_"])
        match RawKey(prefix="", key=name):
            case RawKey() as x if x.indirect() == ind:
                assert(True)
            case x:
                assert(False), x
