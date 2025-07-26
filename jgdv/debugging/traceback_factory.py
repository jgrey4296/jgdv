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
##-- end system guards

##--|

class TracebackFactory:
    """ A Helper to simplify access to tracebacks.
    By Default, removes the frames of this tracebuilder from the trace
    ie     : TraceBuilder._get_frames() -> TraceBuilder.__init__() -> call -> call -> root
    will be: call -> call -> root

    use item acccess to limit the frames,
    eg: tb[2:], will remove the two most recent frames from the traceback

    Use as:
    tb = TraceBuilder()
    raise Exception().with_traceback(tb[:])
    """

    def __class_getitem__(cls, item:slice) -> Maybe[Traceback]:
        tbb = cls()
        return tbb[item]

    def __init__(self, *, chop_self:bool=True) -> None:
        self.frames : list[Frame] = []
        self._get_frames()
        if chop_self:
            self.frames = self.frames[2:]

    def __getitem__(self, val:Maybe[slice]=None) -> Maybe[Traceback]:
        match val:
            case None:
                return self.to_tb()
            case slice() | int():
                return self.to_tb(self.frames[val])
            case _:
                msg = "Bad value passed to TraceHelper"
                raise TypeError(msg, val)

    def _get_frames(self) -> None:
        """ from https://stackoverflow.com/questions/27138440
        Builds the frame stack from most recent to least,
        """
        depth = 0
        while True:
            try:
                frame : Frame = sys._getframe(depth)
                depth += 1
            except ValueError:
                break
            else:
                self.frames.append(frame)

    def to_tb(self, frames:Maybe[list[Frame]]=None) -> Maybe[Traceback]:
        top    = None
        frames = frames or self.frames
        for frame in frames:
            top = types.TracebackType(top, frame,
                                      frame.f_lasti,
                                      frame.f_lineno)
        else:
            return top

