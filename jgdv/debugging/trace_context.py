#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
from collections import defaultdict
import linecache
import enum
import functools as ftz
import math
import itertools as itz
import inspect
import logging as logmod
import gc
import re
import sys
import time
import weakref
import trace
from uuid import UUID, uuid1
import pathlib as pl

# ##-- end stdlib imports

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
# isort: on
# ##-- end types

# ##-- type checking
# isort: off
if typing.TYPE_CHECKING:
    from ._interface import TraceEvent
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Traceback, Frame
## isort: on
# ##-- end type checking

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##-- system guards
if not hasattr(sys, "_getframe"):
        msg = "Can't use TraceBuilder on this system, there is no sys._getframe"
        raise ImportError(msg)
if not hasattr(sys, "settrace"):
    msg = "Cant use a TraceContext on this system, it has no sys.settrace"
    raise ImportError(msg)

##-- end system guards

##--|
DEFAULT_MESSAGES  : Final[dict[str, str]] = {
    "call"        : "----> %s",
    "caller"      : "%-20s ----> %s (l:%s)",
    "return"      : "%-20s <---- %s",
    "line"        : "\t%s:%s : %s",
}

EXEC_LINE      : Final[str]  = r"({}) >>>> {}"
NON_EXEC_LINE  : Final[str]  = r"({}) .... {}"
FIRST_LINE     : Final[str]  = r"({}) .... {} (NEW FILE: {})"

def must_have_results[T:TraceContext, **I, O](fn:Callable[Cons[T, I],O]) -> Callable[Cons[T, I], O]:
    return fn

    @ftz.wraps
    def _check(self:T, *args:I.args, **kwargs:I.kwargs) -> O:
        assert(self.results)
        return fn(self, *args, **kwargs)

    return _check

class TraceObj:
    __slots__ = ("count", "file", "func", "line_no", "package")
    file     : Maybe[str]
    package  : Maybe[str]
    func     : str
    line_no  : int
    count    : int

    def __init__(self, frame:Frame) -> None:
        self.file     = frame.f_code.co_filename
        self.package  = frame.f_globals.get("__package__", None)
        self.func     = frame.f_code.co_qualname
        self.line_no  = frame.f_lineno
        self.count    = 0

    @override
    def __repr__(self) -> str:
        return f"<{self.package}:{self.func}:{self.line_no}>"

    @property
    def line(self) -> str:
        assert(self.file)
        return linecache.getline(self.file, self.line_no)

##--|

class TraceWriter:

    def __init__(self) -> None:
        pass

    def format_trace(self, trace:list[TraceObj]) -> str:
        result : list[str] = []
        for obj in trace:
            result.append(obj.line)
        else:
            return "\n".join(result)

    def format_file_execution(self, *, file:str, trace:dict[int, TraceObj]) -> str:
        # TODO : use a semantic parse to diff executable from non-executable lines
        result : list[str] = []
        source = linecache.getlines(str(file))
        for i,x in enumerate(source, 1):
            match i:
                case 1:
                    result.append(FIRST_LINE.format(i, x.removesuffix("\n"), pl.Path(file).name))
                case int() as potential if potential in trace:
                    # Line executed
                    result.append(EXEC_LINE.format(i, x).removesuffix("\n"))
                case _:
                    # No execution
                    result.append(NON_EXEC_LINE.format(i, x).removesuffix("\n"))

        else:
            return "\n".join(result)

##--|

class TraceContext:
    """ Utility to simplify using the trace library, as a context manager

      see https://docs.python.org/3/library/trace.html
    """
    ##--| internal
    _blacklist  : list[str]
    _write_to   : Maybe[pl.Path]
    _curr_func  : TraceObj
    _logger     : Maybe[logmod.Logger]
    _formatter  : TraceWriter
    _whitelist  : list[str]
    ##--| options
    cache       : Maybe[pl.Path]
    trace_targets  : tuple[TraceEvent, ...]
    list_funcs     : bool
    list_callers   : bool
    timestamp      : bool
    log_fmts       : dict[str, str]
    ##--| results
    called         : set[str]
    callers  : defaultdict[str, set[str]]
    counts   : defaultdict[tuple[str, str], int]
    trace    : list[TraceObj]
    lines    : list[TraceObj]

    def __init__(self, *, targets:Maybe[Iterable[TraceEvent]], logger:Maybe[logmod.Logger|Literal[False]]=None, cache:Maybe[pl.Path]=None, list_funcs:bool=False, list_callers:bool=False, timestamp:bool=False, log_fmts:Maybe[dict]=None) -> None:  # noqa: PLR0913
        x : Any
        ##--|
        self._blacklist  = [sys.exec_prefix]
        self._whitelist  = []
        self._formatter  = TraceWriter()
        match targets:
            case str() as x:
                self.trace_targets = (cast("TraceEvent", x),)
            case [*xs]:
                self.trace_targets = tuple(xs)
            case None:
                self.trace_targets = ("call",)
            case x:
                raise TypeError(type(x))

        assert(all(x in ("call", "line", "return", "exception", "opcode") for x in self.trace_targets))
        self.cache         = cache
        self.list_funcs    = list_funcs
        self.list_callers  = list_callers
        self.timestamp     = timestamp
        self.callers       = defaultdict(set)
        self.called        = set()
        self.counts        = defaultdict(lambda: 0)
        self.trace         = []
        self.log_fmts      = DEFAULT_MESSAGES.copy()
        if log_fmts:
            self.log_fmts.update(log_fmts)

        match logger:
            case False:
                self._logger = None
            case None:
                self._logger = logging
            case logmod.Logger() as log:
                self._logger = log
            case x:
                raise TypeError(type(x))

    def __enter__(self) -> Self:
        sys.settrace(self.sys_trace_h) # type: ignore[arg-type]
        return self

    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool: # type: ignore[exit-return]
        sys.settrace(None)
        return False

    ##--| Filtering

    def blacklist(self, *args:str) -> Self:
        """ Add string's to ignore to the context """
        self._blacklist += args
        return self

    def whitelist(self, *args:str) -> Self:
        self._whitelist += args
        return self

    def ignores(self, curr:Maybe[str|TraceObj]) ->  bool:

        match curr:
            case None:
                return False
            case str() as x if bool(self._whitelist):
                return not any(y in x for y in self._whitelist)
            case str() as x:
                return any(y in x for y in self._blacklist)
            case TraceObject() as obj if bool(self._whitelist):
                return not any(x in self._whitelist for x in [obj.package, obj.file, obj.func])
            case TraceObject() as obj:
                return any(x in self._blacklist for x in [obj.package, obj.file, obj.func])
    ##--| tracer and handlers

    def sys_trace_h(self, frame:Frame, event:TraceEvent, arg:Any) -> Maybe[Callable]:  # noqa: ANN401
        """ The main handler method added to sys for tracing. """
        if self.ignores(frame.f_code.co_qualname):
            return None
        match event:
            case "call":
                self._trace_call(frame)
            case "line":
                self._trace_line(frame)
            case "return":
                self._trace_return(frame)
            case "exception":
                pass
            case "opcode":
                pass
            case x:
                raise TypeError(type(x), x)

        return self.sys_trace_h

    def _trace_call(self, frame:Frame) -> None:
        if "call" not in self.trace_targets:
            return
        self._curr_func = TraceObj(frame)
        self._add_called()
        if frame.f_back:
            parent = TraceObj(frame.f_back)
            # Tracking caller -> callee
            self._add_caller(parent)
            self._log("caller", parent.func, self._curr_func.func, self._curr_func.line_no)
        else:
            self._log("call", self._curr_func)
        # Tracking called functions
        self.called.add(self._curr_func.func)
        # Trace
        self._add_trace(self._curr_func)

    def _trace_line(self, frame:Frame) -> None:
        if "line" not in self.trace_targets:
            return
        curr = TraceObj(frame)
        self._log("line", curr.package, curr.line_no, curr.line.strip())
        self._add_trace(curr)

    def _trace_return(self, frame:Frame) -> None:
        if "return" not in self.trace_targets:
            return None

        assert(frame.f_back)
        curr    = TraceObj(frame)
        parent  = TraceObj(frame.f_back)
        self._log("return", parent.func, curr.func)
        self._add_trace(curr)

    ##--| assertions

    def assert_called(self, name:str) -> None:
        assert(name in self.called)

    def assert_count(self, package:str, name:str, *, min:Maybe[int]=None, max:Maybe[int]=None) -> None:  # noqa: A002
        assert((package, name) in self.counts)
        match self.counts.get((package, name), None):
            case None:
                raise AssertionError()
            case int() as x:
                assert((min or 0) <= x)
                assert(x < (max or math.inf))

    ##--| IO

    def write_coverage(self, *, filter:Maybe[str]=None, in_tree:bool=False, target:pl.Path, package:Maybe[str]=None) -> dict[str,str]:
        trace      : list[TraceObj]
        grouped    : defaultdict[str, dict[int, TraceObj]]
        formatted  : dict[str, str]
        ##--|
        # Get the trace
        trace = self.trace
        # filter it
        trace = [x for x in trace if True]
        # Group into files
        grouped = defaultdict(dict)
        for obj in trace:
            assert(obj.file is not None)
            grouped[obj.file][obj.line_no] = obj

        formatted = {}
        for file, _trace in grouped.items():
            # format it
            formatted[file] = self._formatter.format_file_execution(file=file, trace=_trace)

        match target:
            case None:
                pass
            case pl.Path() as f:
                # Write it to file
                joined = "\n".join(formatted.values())
                f.write_text(joined)

        match in_tree:
            case False:
                pass
            case True:
                pass

        return formatted

    ##--| utils

    def _log(self, key:str, *args) -> None:
        if self._logger is None:
            return

        match self.log_fmts.get(key, None):
            case None:
                return
            case str() as fmt:
                self._logger.info(fmt, *args)

    def _add_trace(self, curr:TraceObj) -> None:
        self.trace.append(curr)

    def _add_caller(self, caller:TraceObj) -> None:
        if not self.list_callers:
            return
        self.callers[caller.func].add(self._curr_func.func)

    def _add_called(self) -> None:
        if not self.list_funcs:
            return
        assert(self._curr_func.package)
        self.called.add(self._curr_func.func)
        self.counts[(self._curr_func.package, self._curr_func.func)] += 1

    def _add_timestamp(self) -> None:
        pass
