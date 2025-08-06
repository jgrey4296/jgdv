#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import fnmatch
import functools as ftz
import itertools as itz
import linecache
import logging as logmod
import pathlib as pl
import re
import time
import tracemalloc
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

import stackprinter
import traceback

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
from typing import Concatenate as Cons
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Traceback

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

STAT_FORMS       : Final[tuple[str, ...]] = ("traceback", "filename", "lineno")
INIT_SNAP_NAME   : Final[str] = "_init_"
FINAL_SNAP_NAME  : Final[str] = "_final_"

def must_be_started[**I, O](fn:Callable[Cons[MallocTool, I],O]) -> Callable[Cons[MallocTool, I], O]:
    return fn

    @ftz.wraps
    def _check(self:MallocTool, *args:I.args, **kwargs:I.kwargs) -> O:
        assert(self.started)
        return fn(self, *args, **kwargs)

    return _check

##--|

class MallocTool:
    r""" see `tracemalloc <https://docs.python.org/3/library/tracemalloc.html>`_
    in the stdlib. eg:

    ::

        with MallocTool(frame_count=2) as dm:
            dm.whitelist(__file__)
            dm.blacklist("\*tracemalloc.py", all_frames=False)
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
    frame_count          : int
    started              : bool
    snapshots            : list[tracemalloc.Snapshot]
    named_snapshots      : dict[str, tracemalloc.Snapshot]
    filters              : list[tracemalloc.Filter]

    _logger              : logmod.Logger
    _curr_mem_msg        : str
    _allocation_loc_msg  : str
    _inspect_msg         : str
    _cmp_enter_msg       : str
    _change_msg          : str
    _diff_msg            : str
    _stat_line_msg       : str
    _enter_msg           : str
    _exit_msg            : str
    _take_snap_msg       : str

    def __init__(self, *, frame_count:int=5, logger:Maybe[logmod.Logger]=None) -> None:
        assert(0 < frame_count)
        self._logger              = logger or logging
        self.frame_count          = frame_count
        self.started              = False
        self.snapshots            = []
        self.named_snapshots      = {}
        self.filters              = []
        self.blacklist("*tracemalloc.py", all_frames=False)
        self.blacklist(__file__)
        ##--| Messages:
        self._enter_msg                = "[TraceMalloc]: --> Entering, tracking %s frames"
        self._exit_msg                 = "[TraceMalloc]: <-- Exited, with %s snapshots"
        self._take_snap_msg            = "[TraceMalloc]: Taking Snapshot: %-15s (Current: %-10s, Peak: %s)"
        self._curr_mem_msg             = "[TraceMalloc]: Memory: (Current: %-10s, Peak: %s)"
        self._allocation_loc_msg       = "[TraceMalloc]: Value Allocated At: %s"
        self._inspect_msg              = "[TraceMalloc]: ---- Inspecting: %s ----"
        self._cmp_enter_msg            = "[TraceMalloc]: ---- Comparing (%s): %s -> %s. Objects:%s ----"
        self._gen_exit_msg             = "[TraceMalloc]: -- %s --"
        self._diff_msg                 = "[TraceMalloc]: -- (obj:%s) delta: %s, %s blocks --"
        self._stat_line_msg            = "[TraceMalloc]: (obj:%s, frame:%3s) : %-50s (%s:%s)"
        self._stat_line_no_frames_msg  = "[TraceMalloc]: (obj:%s) %-15s : %-50s (%s:%s)"

    def __enter__(self) -> Self:
        """ Ctx handler to start tracing object allocations """
        self._logger.info(self._enter_msg, self.frame_count)
        tracemalloc.start(self.frame_count)
        self.started = True
        self.snapshot(INIT_SNAP_NAME)
        return self

    @must_be_started
    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool: # type: ignore[exit-return]
        """ Stop tracing allocations """
        self.snapshot(FINAL_SNAP_NAME)
        tracemalloc.stop()
        self.started = False
        self._logger.info(self._exit_msg, len(self.snapshots))
        return False

    ##--| Setup

    def whitelist(self, file_pat:str, *, lineno:Maybe[int]=None, all_frames:bool=True) -> Self:
        """ Add a filter to whitelist a file pattern """
        self.filters.append(
            tracemalloc.Filter(True,  # noqa: FBT003
                               filename_pattern=file_pat,
                               lineno=lineno,
                               all_frames=all_frames),
            )
        return self

    def blacklist(self, file_pat:str, *, lineno:Maybe[int]=None, all_frames:bool=True) -> Self:
        """ Blacklist a file pattern """
        self.filters.append(
            tracemalloc.Filter(False,  # noqa: FBT003
                               filename_pattern=file_pat,
                               lineno=lineno,
                               all_frames=all_frames),
            )
        return self

    ##--| Control

    @must_be_started
    def snapshot(self, name:Maybe[str]=None) -> None:
        """ Take a snapshot of the current memory state """
        traced : Maybe[tuple]
        ##--|
        traced = tracemalloc.get_traced_memory()
        logging.info(self._take_snap_msg, name, self._human(traced[0]), self._human(traced[1]))
        traced = None
        snap = tracemalloc.take_snapshot()
        self.snapshots.append(snap)
        if name and name not in self.named_snapshots:
            self.named_snapshots[name] = snap

        tracemalloc.clear_traces()

    ##--| Report

    @must_be_started
    def current(self, val:Maybe[object]=None) -> None:
        """ Print a brief report about the current memory state """
        traced = tracemalloc.get_traced_memory()
        self._logger.info(self._curr_mem_msg, self._human(traced[0]), self._human(traced[1]))
        if val:
            self._logger.info(self._allocation_loc_msg, tracemalloc.get_object_traceback(val))

    def inspect(self, val:int|str, *, form:str="traceback", filter:bool=True, fullpath:bool=False) -> None:  # noqa: A002
        """ Inspect a single snapshot of the memory state  """
        assert(form in STAT_FORMS)
        self._logger.info(self._inspect_msg, val)
        snap = self._get_snapshot(val, filter=filter)
        for stat in snap.statistics(form):
            self._print_obj_stat_frames(stat, fullpath=fullpath)
        else:
            self._logger.info(self._gen_exit_msg, "inspect")

    def compare(self, val1:int|str, val2:int|str, *, form:str="traceback", filter:bool=True, fullpath:bool=False, count:int=10) -> None:  # noqa: A002, ARG002, PLR0913
        """ Compare two snapshots,
        with control over filtering, output formatting,
        and the number of objects to report about

        """
        differences : list[tracemalloc.StatisticDiff]
        assert(form in STAT_FORMS)
        snap1 = self._get_snapshot(val1, filter=filter)
        snap2 = self._get_snapshot(val2, filter=filter)

        if 1 < self.frame_count:
            printer = self._print_diff_frames
        else:
            printer = self._print_diff_noframes

        differences = snap2.compare_to(snap1, form)
        # TODO differences = self._get_top_n(differences, count=count)
        diff_count  = len(differences)
        self._logger.info(self._cmp_enter_msg, form, val1, val2, diff_count)
        for i, stat in enumerate(differences):
            printer(stat, idx=i, fullpath=fullpath)
        else:
            self._logger.info(self._gen_exit_msg, f"Compare ({diff_count}/{diff_count})")

    ##--| utils

    def _print_diff_noframes(self, stat:tracemalloc.StatisticDiff, *, idx:Maybe[int]=None, fullpath:bool=False) -> None:
        """ Print a diff without showing the stacktrace """
        assert(isinstance(stat, tracemalloc.StatisticDiff))
        tb           = stat.traceback
        frame        = tb[-1]
        size_change  = self._human(stat.size, sign=True)
        if fullpath:
            path = frame.filename
        else:
            path = pl.Path(frame.filename).name
        self._logger.info(self._stat_line_no_frames_msg,
                          idx,
                          size_change,
                          linecache.getline(frame.filename, frame.lineno).strip(),
                          path,
                          frame.lineno,
                          )


    def _print_diff_frames(self, stat:tracemalloc.StatisticDiff, *, idx:Maybe[int]=None, fullpath:bool=False) -> None:
        """ Print a diff, with stacktrace """
        assert(isinstance(stat, tracemalloc.StatisticDiff))
        self._logger.info(self._diff_msg, idx, self._human(stat.size_diff, sign=True), stat.count_diff)
        self._print_obj_stat_frames(stat, idx=idx, fullpath=fullpath)

    def _print_obj_stat_frames(self, stat:tracemalloc.Statistic|tracemalloc.StatisticDiff, *, idx:Maybe[int]=None, fullpath:bool=False) -> None:
        """ Print a stacktrace for a a given object diff """
        assert(isinstance(stat, tracemalloc.Statistic|tracemalloc.StatisticDiff))
        tb     = stat.traceback
        total  = len(tb)-1
        for i, frame in enumerate(tb):
            if fullpath:
                path = frame.filename
            else:
                path = pl.Path(frame.filename).name
            self._logger.info(self._stat_line_msg,
                              idx,
                              i-total,
                              linecache.getline(frame.filename, frame.lineno).strip(),
                              path,
                              frame.lineno,
                              )
        else:
            pass

    def _human(self, num:int, *, sign:bool=False) -> str:
        """ Format a sized number in a human readable way. optionally with a sign prefix """
        return cast("str", tracemalloc._format_size(num, sign)) # type: ignore[attr-defined]

    def _get_snapshot(self, val:int|str, *, filter:bool=True) -> tracemalloc.Snapshot:  # noqa: A002
        """ Retrieve a snapshot,
        with control of whether it is filtered or not
        """
        match val:
            case int() if 0 <= val < len(self.snapshots):
                snap = self.snapshots[val]
            case int() if val < 0:
                snap = self.snapshots[val]
            case str() if val in self.named_snapshots:
                snap = self.named_snapshots[val]
            case _:
                raise TypeError(val)

        if filter:
            return snap.filter_traces(self.filters)

        return snap

    def _check_file_pat(self, file_pat:str, file_name:str) -> bool:
        return fnmatch.fnmatch(file_name, file_pat)

    def _get_top_n(self, stats:list[tracemalloc.StatisticDiff], count:int=10) -> list[tracemalloc.StatisticDiff]:
        r""" Get the top {count} sized objects of a difference """
        raise NotImplementedError()
