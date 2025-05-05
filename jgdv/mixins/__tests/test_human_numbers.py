#!/usr/bin/env python3
"""
TEST File updated

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202, B011

# Imports
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
from copy import copy
import warnings
import datetime
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest
# ##-- end 3rd party imports

from ..human_numbers import HumanNumbers_m

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
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

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
size_tests : Final[list[tuple[int, str]]] = [
    # no force sign:
    (10,         "10 B",     False),
    (100,        "100 B",    False),
    (2723,       "2723 B",   False),
    (20_000,     "19.5 KiB", False),
    (1_000_000,  "977 KiB",  False),
    (23_000_000, "21.9 MiB", False),

    # Negative, no force sign
    (-20_000,     "-19.5 KiB", False),
    (-1_000_000,  "-977 KiB",  False),
    (-23_000_000, "-21.9 MiB", False),

    # Force sign
    (20_000,     "+19.5 KiB", True),
    (1_000_000,  "+977 KiB",  True),
    (23_000_000, "+21.9 MiB", True),
    # Negative force sign
    (-20_000,     "-19.5 KiB", True),
    (-1_000_000,  "-977 KiB",  True),
    (-23_000_000, "-21.9 MiB", True),
]

# Body:
class TestHumanNumbers:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    @pytest.mark.parametrize(["num","fmt", "signed"], size_tests)
    def test_basic_size(self, num, fmt, signed):
        match HumanNumbers_m.humanize(num, force_sign=signed):
            case str() as x:
                assert(x == fmt)
            case x:
                 assert(False), x

    def test_round_time(self):
        origin = datetime.datetime.now().replace(hour=2, minute=34, second=23)
        match HumanNumbers_m.round_time(origin, round=60*60):
            case datetime.datetime() as dt:
                assert(dt.second == 0)
                assert(dt.minute == 0)
                assert(dt.microsecond == 0)
            case x:
                 assert(False), x


    ##--|

    @pytest.mark.skip
    def test_todo(self):
        pass
