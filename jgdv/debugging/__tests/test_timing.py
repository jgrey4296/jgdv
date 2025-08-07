"""
TEST File updated

"""
# ruff: noqa: ANN202, B011, ANN001

# Imports
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings
import time
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest
# ##-- end 3rd party imports

##--|
from ..timing import TimeCtx, TimeDec
##--|

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
# isort: on
# ##-- end types

# ##-- type checking
# isort: off
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe
## isort: on
# ##-- end type checking

##-- logging
logging = logmod.getLogger(__name__)
logmod.getLogger("jgdv.decorators").propagate = False
##-- end logging

# Vars:

# Body:

class TestTimeCtx:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_ctor(self):
        match TimeCtx():
            case TimeCtx():
                assert(True)
            case x:
                assert(False), x

    @pytest.mark.parametrize("wait", [0.1,0.2,0.3,0.4])
    def test_basic(self, wait):
        with TimeCtx() as obj:
            time.sleep(wait)

        assert(obj.total_s > wait)

class TestTimeDec:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self, caplog):
        dec = TimeDec()

        @dec
        def basic():
            time.sleep(1)

        basic()
        assert("Timed: TestTimeDec.test_basic.<locals>.basic took" in caplog.messages[0])

    def test_cache(self, caplog):
        target_cache = pl.Path(__file__).parent / "basic.cache"
        dec = TimeDec(cache=target_cache)

        @dec
        def basic():
            time.sleep(0.2)

        basic()
        assert("Timed: TestTimeDec.test_cache.<locals>.basic took" in caplog.messages[0])
