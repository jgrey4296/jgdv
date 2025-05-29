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

from ..._interface import RawKey_d
from ..parser import DKeyParser

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
RAWKEY_ARGS : Final[str] = ["pre", "key", "format", "convert", "out"]
# Body:

class TestRawKey:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match RawKey_d(prefix=""):
            case RawKey_d():
                assert(True)
            case x:
                assert(False), x


    def test_error_on_extra(self):
        with pytest.raises(AssertionError):
            RawKey_d(prefix="", non_val="blah")


    def test_error_on_no_prefix(self):
        with pytest.raises(KeyError):
            RawKey_d(key="blah")

    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "blah"),
        ("blah", "bloo", "", "", "bloo"),
        ("-- ", "awegah", "<50", "p", "awegah:<50!p"),
        ("-- ", "awegah_", "<50", "p", "awegah_:<50!p"),
    ])
    def test_joined(self, pre, key, format, convert, out):
        match RawKey_d(prefix=pre, format=format, key=key, convert=convert):
            case RawKey_d() as x if x.joined() == out:
                assert(True)
            case x:
                assert(False), (x, x.joined(), out)

    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "{}"),
        ("blah", "bloo", "", "", "blah{}"),
        ("-- ", "awegah", "<50", "p", "-- {}"),
        ("-- ", "awegah_", "", "p", "-- {}"),
    ])
    def test_anon(self, pre, key, format, convert, out):
        match RawKey_d(prefix=pre, key=key, format=format, convert=convert):
            case RawKey_d() as x if x.anon() == out:
                assert(True)
            case x:
                assert(False), (x, x.anon(), out)

    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "{blah}"),
        ("blah", "bloo", "", "", "{bloo}"),
        ("-- ", "awegah", "<50", "p", "{awegah}"),
        ("-- ", "awegah_", "<50", "p", "{awegah_}"),
    ])
    def test_wrapped(self, pre, key, format, convert, out):
        match RawKey_d(prefix=pre, key=key, format=format, convert=convert):
            case RawKey_d() as x if x.wrapped() == out:
                assert(True)
            case x:
                assert(False), (x, x.wrapped(), out)


    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "blah_"),
        ("blah", "bloo", "", "", "bloo_"),
        ("-- ", "awegah", "", "p", "awegah_"),
        ("", "aweg_", "", "", "aweg_"),
    ])
    def test_indirect(self, pre, key, format, convert, out):
        match RawKey_d(prefix=pre, key=key, format=format, convert=convert):
            case RawKey_d() as x if x.indirect() == out:
                assert(True)
            case x:
                assert(False), (x, x.indirect(), out)


    @pytest.mark.parametrize(RAWKEY_ARGS, [
        ("", "blah", "", "", "blah"),
        ("blah", "bloo", "", "", "bloo"),
        ("-- ", "awegah", "", "p", "awegah"),
        ("", "aweg_", "", "", "aweg"),
    ])
    def test_direct(self, pre, key, format, convert, out):
        match RawKey_d(prefix=pre, key=key, format=format, convert=convert):
            case RawKey_d() as x if x.direct() == out:
                assert(True)
            case x:
                assert(False), (x, x.direct(), out)

class TestParser:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_empty(self):
        match next(DKeyParser().parse("blah")):
            case RawKey_d() as x:
                assert(x.prefix == "blah")
                assert(True)
            case x:
                 assert(False), x

    def test_key(self):
        match next(DKeyParser().parse("{blah}")):
            case RawKey_d() as x:
                assert(x.prefix == "")
                assert(x.key == "blah")
                assert(True)
            case x:
                 assert(False), x

    def test_impicit(self):
        match next(DKeyParser().parse("blah", implicit=True)):
            case RawKey_d() as x:
                assert(x.prefix == "")
                assert(x.key == "blah")
                assert(True)
            case x:
                 assert(False), x

    def test_open_brace(self):
        match next(DKeyParser().parse("{blah")):
            case RawKey_d() as x:
                assert(x.key == None)
                assert(x.prefix == "{blah")
                assert(True)
            case x:
                 assert(False), x


    def test_close_brace(self):
        match next(DKeyParser().parse("blah}")):
            case RawKey_d() as x:
                assert(x.key == None)
                assert(x.prefix == "blah}")
                assert(True)
            case x:
                 assert(False), x
