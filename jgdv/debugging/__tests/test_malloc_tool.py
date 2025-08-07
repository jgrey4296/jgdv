#!/usr/bin/env python3
"""
TEST File updated

"""
# ruff: noqa: ANN202, B011, ANN001, F841, C405

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

import random
##--|
from ..malloc_tool import MallocTool
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
EXPECT_NO_FRAMES : Final[str] = """
[TraceMalloc]: --> Entering, tracking 1 frames
[TraceMalloc]: Taking Snapshot: _init_          (Current: 0 B       , Peak: 0 B)
[TraceMalloc]: Taking Snapshot: before
[TraceMalloc]: Taking Snapshot: after
[TraceMalloc]: Taking Snapshot: cleared
[TraceMalloc]: Taking Snapshot: _final_         (Current: 0 B       , Peak: 0 B)
[TraceMalloc]: <-- Exited, with 5 snapshots
[TraceMalloc]: ---- Comparing (traceback): before -> after. Objects:2 ----
[TraceMalloc]: (obj:0) +32.0 KiB       : vals = [random.random() for x in range(1000)]
[TraceMalloc]: (obj:1) +216 B          : a_dict = {"blah": 23, "bloo": set([1,2,3,4])}
[TraceMalloc]: -- Compare (2/2) --
"""

EXPECT_MULTI_FRAMES : Final[str] = """
[TraceMalloc]: --> Entering, tracking 3 frames
[TraceMalloc]: Taking Snapshot: _init_          (Current: 0 B       , Peak: 0 B)
[TraceMalloc]: Taking Snapshot: before
[TraceMalloc]: Taking Snapshot: after
[TraceMalloc]: Taking Snapshot: cleared         (Current: 16 B      , Peak: 16 B)
[TraceMalloc]: Taking Snapshot: _final_         (Current: 0 B       , Peak: 0 B)
[TraceMalloc]: <-- Exited, with 5 snapshots
[TraceMalloc]: ---- Comparing (traceback): before -> after. Objects:2 ----
[TraceMalloc]: -- (obj:0) delta:
[TraceMalloc]: (obj:0, frame: -2) : res = hook_impl.function(*args)                    (_callers.py:103)
[TraceMalloc]: (obj:0, frame: -1) : result = testfunction(**testargs)                  (python.py:159)
[TraceMalloc]: (obj:0, frame:  0) : vals = [random.random() for x in range(1000)]
[TraceMalloc]: -- (obj:1) delta:
[TraceMalloc]: (obj:1, frame: -2) : res = hook_impl.function(*args)                    (_callers.py:103)
[TraceMalloc]: (obj:1, frame: -1) : result = testfunction(**testargs)                  (python.py:159)
[TraceMalloc]: (obj:1, frame:  0) : a_dict = {"blah": 23, "bloo": set([1,2,3,4])}
[TraceMalloc]: -- Compare (2/2) --

"""

EXPECT_INSPECT : Final[str] = """
[TraceMalloc]: --> Entering, tracking 1 frames
[TraceMalloc]: Taking Snapshot: _init_          (Current: 0 B       , Peak: 0 B)
[TraceMalloc]: Taking Snapshot: before
[TraceMalloc]: Taking Snapshot: after
[TraceMalloc]: Taking Snapshot: cleared
[TraceMalloc]: Taking Snapshot: _final_         (Current: 0 B       , Peak: 0 B)
[TraceMalloc]: <-- Exited, with 5 snapshots
[TraceMalloc]: ---- Inspecting: after ----
[TraceMalloc]: (obj:None, frame:  0) : vals = [random.random() for x in range(1000)]
[TraceMalloc]: (obj:None, frame:  0) : a_dict = {"blah": 23, "bloo": set([1,2,3,4])}
[TraceMalloc]: -- inspect --
"""

# Body:

class TestMalloc:

    @pytest.fixture(scope="function")
    def setup(self):
        pass

    ##--|

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_ctor(self):
        match MallocTool():
            case MallocTool():
                assert(True)
            case x:
                assert(False), x

    def test_compare_single_frame(self, caplog):
        expected = [x.strip() for x in EXPECT_NO_FRAMES.splitlines() if bool(x.strip())]
        with MallocTool(frame_count=1) as dm:
            dm.whitelist(__file__)
            dm.blacklist("*.venv")
            val = 2
            dm.snapshot("before")
            vals = [random.random() for x in range(1000)]
            a_dict = {"blah": 23, "bloo": set([1,2,3,4])}
            dm.snapshot("after")
            empty_dict = {"basic": [10, 20]}
            vals = None
            dm.snapshot("cleared")

        dm.compare("before", "after", filter=True, fullpath=False)
        for x,y in zip(expected, caplog.messages, strict=True):
            assert(x in y.strip())

    def test_compare_multi_frame(self, caplog):
        expected = [x.strip() for x in EXPECT_MULTI_FRAMES.splitlines() if bool(x.strip())]
        with MallocTool(frame_count=3) as dm:
            dm.whitelist(__file__)
            dm.blacklist("*.venv")
            val = 2
            dm.snapshot("before")
            vals = [random.random() for x in range(1000)]
            a_dict = {"blah": 23, "bloo": set([1,2,3,4])}
            dm.snapshot("after")
            empty_dict = {"basic": [10, 20]}
            vals = None
            dm.snapshot("cleared")

        dm.compare("before", "after", filter=True, fullpath=False)
        for x,y in zip(expected, caplog.messages, strict=True):
            assert(x in y.strip())

    def test_basic_inspect(self, caplog):
        expected = [x.strip() for x in EXPECT_INSPECT.splitlines() if bool(x.strip())]
        with MallocTool(frame_count=1) as dm:
            dm.whitelist(__file__)
            dm.blacklist("*.venv")
            val = 2
            dm.snapshot("before")
            vals = [random.random() for x in range(1000)]
            a_dict = {"blah": 23, "bloo": set([1,2,3,4])}
            dm.snapshot("after")
            empty_dict = {"basic": [10, 20]}
            vals = None
            dm.snapshot("cleared")

        dm.inspect("after")
        for x,y in zip(expected, caplog.messages, strict=True):
            assert(x in y.strip())
