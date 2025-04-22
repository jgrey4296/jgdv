#!/usr/bin/env python3
"""

"""

##-- builtin imports
from __future__ import annotations

import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from uuid import UUID, uuid1
import tracemalloc
import linecache
import fnmatch

##-- end builtin imports

from . import _interface as API # noqa: N812
from jgdv import Proto, Mixin
from jgdv.mixins.human_numbers import HumanNumbers_m

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
    from jgdv import Maybe, Traceback
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type Snapshot   = tracemalloc.Snapshot
    type Statistic  = tracemalloc.Statistic
    type Difference = tracemalloc.StatisticDiff
    type Logger     = logmod.Logger
    type Filter     = tracemalloc.Filter
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Vals
##--| Body
@Mixin(HumanNumbers_m)
class MallocTool:
    """ see https://docs.python.org/3/library/tracemalloc.html

    example::

        with MallocTool(2) as dm:
            dm.whitelist(__file__)
            dm.blacklist("*tracemalloc.py", all_frames=False)
            val = 2
            dm.snapshot("simple")
            vals = [random.random() for x in range(1000)]
            dm.current()
            dm.snapshot("list")
            vals = None
            dm.current()
            dm.snapshot("cleared")

        dm.compare("simple", "list")
        dm.compare("list", "cleared")
        dm.compare("list", "simple")
        dm.inspect("list")

    """
    num_frames      : int
    started         : bool
    snapshots       : list[Snapshot]
    named_snapshots : dict[str, Snapshot]
    filters         : list[Filter]
    _logger         : Maybe[Logger]
    _log_level      : int

    def __init__(self, *, num_frames:int=5, logger:Maybe[Logger]=None, level:int=API.DEFAULT_LOG_LEVEL) -> None:
        self.num_frames      = num_frames
        self.started         = False
        self.snapshots       = []
        self.named_snapshots = {}
        self.filters         = []
        self._logger         = logger
        self._log_level      = level

    def __enter__(self) -> Self:
        tracemalloc.start(self.num_frames)
        self.started = True
        self.snapshot(name="init")
        return self

    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool: #type:ignore[exit-return]
        self.snapshot(name="final")
        self.started = False
        self._log(f"Recorded {len(self.snapshots)} snapshots")
        return False  # type: ignore[exit-return]

    def whitelist(self, file_pat:str, lineno:Maybe[int]=None, *, all_frames:bool=True) -> None:
        self.filters.append(
            tracemalloc.Filter(inclusive=True,
                               filename_pattern=file_pat,
                               lineno=lineno,
                               all_frames=all_frames),
        )

    def blacklist(self, file_pat:str, *, lineno:Maybe[int]=None, all_frames:bool=True) -> None:
        self.filters.append(
            tracemalloc.Filter(inclusive=False,
                               filename_pattern=file_pat,
                               lineno=lineno,
                               all_frames=all_frames),
            )

    def file_matches(self, name:str|pl.Path, pat:str) -> bool:
        match name:
            case str():
                return fnmatch.fnmatch(name, pat)
            case pl.Path():
                return fnmatch.fnmatch(str(name), pat)
            case x:
                raise TypeError(type(x))

    def snapshot(self, *, name:Maybe[str]=None) -> None:
        if not self.started:
            msg = "DebugMalloc needs to have been entered"
            raise RuntimeError(msg)

        snap = tracemalloc.take_snapshot()
        self.snapshots.append(snap)
        if name and name not in self.named_snapshots:
            self.named_snapshots[name] = snap

        tracemalloc.clear_traces()

    def get_snapshot(self, val:int|str) -> Snapshot:
        match val:
            case int() if 0 <= val < len(self.snapshots):
                snap = self.snapshots[val]
            case int() if val < 0:
                snap = self.snapshots[val]
            case str() if val in self.named_snapshots:
                snap = self.named_snapshots[val]
            case _:
                raise TypeError(val)

        return snap.filter_traces(self.filters)

    def current(self, val:Maybe=None) -> None:
        traced = tracemalloc.get_traced_memory()
        curr_mem = self.humanize(traced[0])  # type: ignore[attr-defined]
        peak_mem = self.humanize(traced[1])  # type: ignore[attr-defined]
        self._log("Current Memory: %s, Peak: %s", curr_mem, peak_mem)
        if val:
            self._log("Value allocated at: %s", tracemalloc.get_object_traceback(val))

    def inspect(self, val:Any, *, type:str=API.DEFAULT_REPORT) -> None:  # noqa: A002, ANN401
        self._log(f"\n-- Inspecting {val}")
        snap = self.get_snapshot(val)
        for stat in snap.statistics(type):
            self._print_stat(stat)

    def compare(self, val1:int|str, val2:int|str, *, type:str=API.DEFAULT_REPORT) -> None:  # noqa: A002
        self._log(f"\n-- Comparing {val1} to {val2}")
        snap1 = self.get_snapshot(val1)
        snap2 = self.get_snapshot(val2)

        differences = snap2.compare_to(snap1, type)
        diff_count  = len(differences)
        for i, stat in enumerate(differences):
            self._log(f"- {val1} -> {val2} diff {i}/{diff_count}:")
            self._print_diff(stat)

    def _print_diff(self, stat:Difference) -> None:
        """ Print a Trace memory comparison """
        assert(isinstance(stat, tracemalloc.StatisticDiff))
        size_diff  = self.humanize(stat.size_diff, force_sign=True)  # type: ignore[attr-defined]
        count_diff = stat.count_diff
        self._log("%s, %s blocks", size_diff, count_diff, prefix=API.CHANGE_PREFIX)
        self._print_stat(stat)

    def _print_stat(self, stat:Statistic|Difference) -> None:
        """ Print a Traced memory snapshot """
        assert(isinstance(stat, tracemalloc.Statistic|tracemalloc.StatisticDiff))
        tb = stat.traceback
        self._log(f"Frame/Count/Size: {len(stat.traceback):}, {stat.count:}, {self.humanize(stat.size)}")  # type: ignore[attr-defined]
        for x in range(len(tb) -1):
            frame = tb[x]
            path = pl.Path(frame.filename)
            self._log(f"  {path.name:<15}", "line:", f"{frame.lineno:<7}: {linecache.getline(frame.filename, frame.lineno).strip()}")

        frame = tb[-1]
        path = pl.Path(frame.filename)
        self._log(f"* {path.name:<15}", "line:", f"{frame.lineno:<7}: {linecache.getline(frame.filename, frame.lineno).strip()}")

    def _log(self, msg:str, *args:Any, prefix:str=API.DEFAULT_PREFIX) -> None:  # noqa: ANN401
        if self._logger is None:
            return None
        if not bool(msg):
            self._logger.log(self._log_level, "")
            return

        full_fmt = f"{prefix} {msg}"
        self._logger.log(self._log_level, full_fmt, *args)
