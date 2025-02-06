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
RAWKEY_ARGS : Final[str] = ["pre", "key", "format", "conv", "out"]
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

    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "blah"),
        ("blah", "bloo", "", "", "bloo"),
        ("-- ", "awegah", "<50", "p", "awegah:<50!p"),
        ("-- ", "awegah_", "<50", "p", "awegah_:<50!p"),
    ])
    def test_joined(self, pre, key, format, conv, out):
        match RawKey(prefix=pre, format=format, key=key, conv=conv):
            case RawKey() as x if x.joined() == out:
                assert(True)
            case x:
                assert(False), (x, x.joined(), out)


    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "{}"),
        ("blah", "bloo", "", "", "blah{}"),
        ("-- ", "awegah", "<50", "p", "-- {}"),
        ("-- ", "awegah_", "", "p", "-- {}"),
    ])
    def test_anon(self, pre, key, format, conv, out):
        match RawKey(prefix=pre, key=key, format=format, conv=conv):
            case RawKey() as x if x.anon() == out:
                assert(True)
            case x:
                assert(False), (x, x.anon(), out)

    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "{blah}"),
        ("blah", "bloo", "", "", "{bloo}"),
        ("-- ", "awegah", "<50", "p", "{awegah}"),
        ("-- ", "awegah_", "<50", "p", "{awegah_}"),
    ])
    def test_wrapped(self, pre, key, format, conv, out):
        match RawKey(prefix=pre, key=key, format=format, conv=conv):
            case RawKey() as x if x.wrapped() == out:
                assert(True)
            case x:
                assert(False), (x, x.wrapped(), out)

    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "blah_"),
        ("blah", "bloo", "", "", "bloo_"),
        ("-- ", "awegah", "", "p", "awegah_"),
        ("", "aweg_", "", "", "aweg_"),
    ])
    def test_indirect(self, pre, key, format, conv, out):
        match RawKey(prefix=pre, key=key, format=format, conv=conv):
            case RawKey() as x if x.indirect() == out:
                assert(True)
            case x:
                assert(False), (x, x.indirect(), out)


    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "blah"),
        ("blah", "bloo", "", "", "bloo"),
        ("-- ", "awegah", "", "p", "awegah"),
        ("", "aweg_", "", "", "aweg"),
    ])
    def test_direct(self, pre, key, format, conv, out):
        match RawKey(prefix=pre, key=key, format=format, conv=conv):
            case RawKey() as x if x.direct() == out:
                assert(True)
            case x:
                assert(False), (x, x.direct(), out)
