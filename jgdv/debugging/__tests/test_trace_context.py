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
import warnings
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest
# ##-- end 3rd party imports

##--|
from ..trace_context import TraceContext
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
##-- end logging

# Vars:
class TraceExample:

    def start(self) -> None:  # noqa: N802
        blah = 2 + 2
        bloo = 3 + blah
        self._subtestfn(True)  # noqa: FBT003
        self._othertestfn(False)  # noqa: FBT003
        self._subtestfn(bloo > 2)  # noqa: PLR2004

    def _subtestfn(self, val:bool) -> int:  # noqa: FBT001
        amnt : int
        if val:
            amnt = 20
        else:
            amnt = 30

        return amnt

    def _othertestfn(self, val:bool) -> int:
        self._subtestfn(val)
        return 30

# Body:

##--|
class TestTraceContext:

    @pytest.fixture(scope="function")
    def setup(self):
        pass

    ##--|

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_ctor(self):
        match TraceContext(targets=()):
            case TraceContext():
                assert(True)
            case x:
                assert(False), x

    def test_call_trace(self, caplog):
        expect = [
            "TestTraceContext.test_call_trace ----> TraceExample.start",
            "TraceExample.start   ----> TraceExample._subtestfn",
            "TraceExample.start   ----> TraceExample._othertestfn",
            "TraceExample._othertestfn ----> TraceExample._subtestfn",
            "TraceExample.start   ----> TraceExample._subtestfn",
            "TestTraceContext.test_call_trace ----> TraceContext.__exit__",
        ]
        obj = TraceContext(targets="call",
                           list_funcs=False,
                           list_callers=False,
                           )

        example = TraceExample()
        with obj:
            example.start()

        assert(bool(obj.trace))
        assert(bool(caplog.messages))
        assert(len(caplog.messages) == len(expect))
        for exp,ret in zip(expect, caplog.messages, strict=True):
            assert(exp in ret)


    def test_blacklist(self, caplog):
        expect = [
            "TestTraceContext.test_blacklist ----> TraceExample.start",
            "TraceExample.start   ----> TraceExample._subtestfn",
            "TraceExample.start   ----> TraceExample._othertestfn",
            "TraceExample._othertestfn ----> TraceExample._subtestfn",
            "TraceExample.start   ----> TraceExample._subtestfn",
            # This is Removed:
            # "TestTraceContext.test_blacklist ----> TraceContext.__exit__",
        ]
        obj = TraceContext(targets="call",
                           list_funcs=False,
                           list_callers=False,
                           )
        obj.blacklist("TraceContext.__exit__")

        example = TraceExample()
        with obj:
            example.start()

        assert(bool(obj.trace))
        assert(bool(caplog.messages))
        assert(len(caplog.messages) == len(expect))
        for exp,ret in zip(expect, caplog.messages, strict=True):
            assert(exp in ret)


    def test_return_trace(self, caplog):
        expect = [
            "TraceExample.start   <---- TraceExample._subtestfn",
            "TraceExample._othertestfn <---- TraceExample._subtestfn",
            "TraceExample.start   <---- TraceExample._othertestfn",
            "TraceExample.start   <---- TraceExample._subtestfn",
            "TestTraceContext.test_return_trace <---- TraceExample.start",
        ]
        obj = TraceContext(targets=("return"),
                           list_funcs=False,
                           list_callers=False,
                           )

        example = TraceExample()
        with obj:
            example.start()

        assert(bool(obj.trace))
        assert(bool(caplog.messages))
        assert(len(caplog.messages) == len(expect))
        for exp,ret in zip(expect, caplog.messages, strict=True):
            assert(exp in ret)


    def test_line_trace(self, caplog):
        expect = [
            "jgdv.debugging.__tests:61 : blah = 2 + 2",
            "jgdv.debugging.__tests:62 : bloo = 3 + blah",
            "jgdv.debugging.__tests:63 : self._subtestfn(True)  # noqa: FBT003",
            "jgdv.debugging.__tests:69 : if val:",
            "jgdv.debugging.__tests:70 : amnt = 20",
            "jgdv.debugging.__tests:74 : return amnt",
            "jgdv.debugging.__tests:64 : self._othertestfn(False)  # noqa: FBT003",
            "jgdv.debugging.__tests:77 : self._subtestfn(val)",
            "jgdv.debugging.__tests:69 : if val:",
            "jgdv.debugging.__tests:72 : amnt = 30",
            "jgdv.debugging.__tests:74 : return amnt",
            "jgdv.debugging.__tests:78 : return 30",
            "jgdv.debugging.__tests:65 : self._subtestfn(bloo > 2)  # noqa: PLR2004",
            "jgdv.debugging.__tests:69 : if val:",
            "jgdv.debugging.__tests:70 : amnt = 20",
            "jgdv.debugging.__tests:74 : return amnt",
            "jgdv.debugging:217 : sys.settrace(None)",
        ]
        obj = TraceContext(targets="line",
                           list_funcs=False,
                           list_callers=False,
                           )

        example = TraceExample()
        with obj:
            example.start()

        assert(bool(obj.trace))
        assert(bool(caplog.messages))
        assert(len(caplog.messages) == len(expect))
        for exp,ret in zip(expect, caplog.messages, strict=True):
            assert(exp in ret)


    def test_no_logging(self, caplog):
        obj = TraceContext(targets=("call",),
                           list_funcs=True,
                           list_callers=False,
                           logger=False,
                           )

        example = TraceExample()
        with obj:
            example.start()

        assert(not bool(caplog.messages))
        assert(bool(obj.called))


    def test_write_out(self, caplog):
        write_target = pl.Path(__file__).with_suffix(".coverage")
        obj = TraceContext(targets=("call", "line", "return"),
                           list_funcs=False,
                           list_callers=False,
                           logger=None,
                           )

        example = TraceExample()
        with obj:
            example.start()

        # assert(not bool(caplog.messages))
        obj.write_coverage(target=write_target)
        assert(False)
        
    ##--|

    @pytest.mark.skip
    def test_todo(self):
        pass
