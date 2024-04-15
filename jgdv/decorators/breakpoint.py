#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv._interfaces.decorator import DejaVuDecorator_i
from jgdv.debugginer.running_debugger import RunningDebugger

class DejaVuBreakpoint(DejaVuDecorator_i):
    """
      Decorator to attach a debugger to a function, without pausing execution
    """

    def __call__(self, *args, **kwargs):
        # TODO handle repeats
        if args[0].breakpoint:
            f_code = f.__code__
            db = RunningDebugger()
            # Ensure trace function is set
            sys.settrace(db.trace_dispatch)
            if not db.get_break(f_code.co_filename, f_code.co_firstlineno+2):
                db.set_break(f_code.co_filename,
                            f_code.co_firstlineno+2,
                            True)
            else:
                bp = Breakpoint.bplist[f_code.co_filename,
                                    f_code.co_firstlineno+2][0]
                bp.enable()


        return self._func(self, *args, **kwargs)
