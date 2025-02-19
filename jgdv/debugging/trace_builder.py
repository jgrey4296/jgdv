#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import sys
import time
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
from types import TracebackType, FrameType

if TYPE_CHECKING:
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

if not hasattr(sys, "_getframe"):
    raise ImportError("Can't use TraceBuilder on this system, there is no sys._getframe")

##--|
class TraceBuilder:
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

    def __init__(self, *, chop_self=True):
        self.frames : list[FrameType] = []
        self._get_frames()
        if chop_self:
            self.frames = self.frames[2:]

    def __getitem__(self, val=None) -> TracebackType:
        match val:
            case None:
                return self.to_tb()
            case slice() | int():
                return self.to_tb(self.frames[val])
            case _:
                raise TypeError("Bad value passed to TraceHelper", val)

    def _get_frames(self) -> None:
        """ from https://stackoverflow.com/questions/27138440
        Builds the frame stack from most recent to least,
        """
        depth = 0
        while True:
            try:
                frame : FrameType = sys._getframe(depth)
                depth += 1
            except ValueError:
                break
            else:
                self.frames.append(frame)

    def to_tb(self, frames=None) -> TracebackType:
        top = None
        frames = frames or self.frames
        for frame in frames:
            top = TracebackType(top, frame,
                                frame.f_lasti,
                                frame.f_lineno)
        else:
            return top
