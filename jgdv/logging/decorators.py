#!/usr/bin/env python3
"""



"""
# Import:
from __future__ import annotations

# ##-- stdlib imports
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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
# ##-- end stdlib imports

from jgdv import Maybe, Lambda
from jgdv.decorators import DecoratorBase

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

type Logger = logmod.Logger

# Global Vars:
LOGDEC_PRE : Final[str] = "__logcall__"

# Body:

class LogCall(DecoratorBase):
    """ A Decorator for announcing the entry/exit of a function call

    eg:
    @LogCall(enter="Entering", exit="Exiting", level=logmod.INFO)
    def a_func()...
    """

    def __init__(self, enter:Maybe[str|Lambda]=None, exit:Maybe[str|Lambda]=None, level:int|str=logmod.INFO, logger:Maybe[Logger]=None):
        super().__init__(prefix=LOGDEC_PRE)
        self._logger = logger or logging
        self._enter_msg = enter
        self._exit_msg = exit
        match level:
            case str():
                self._level = logmod.getLevelNamesMapping().get(level, logmod.INFO)
            case int():
                self._level = level
            case _:
                raise ValueError(level)

    def _log_msg(self, msg:Maybe[str|Lambda], fn:Callable, args:list, **kwargs):
        match msg:
            case None:
                return None
            case types.FunctionType():
                msg = msg(fn, *args, **kwargs)
            case str():
                pass
            case _:
                raise TypeError(msg)

        self._logger.log(self.level)

    def _wrap_method(self, fn) -> Callable:

        def basic_wrapper(_self, *args, **kwargs):
            self._log_msg(self._enter_msg, fn, args, obj=_self, **kwargs)
            ret_val = fn(_self, *args, **kwargs)
            self._log_msg(self._exit_msg, fn, args, obj=_self, returned=ret_val, **kwargs)
            return ret_val

        return basic_wrapper

    def _wrap_fn(self, fn) -> Callable:

        def basic_wrapper(*args, **kwargs):
            self._log_msg(self._enter_msg, fn, args, obj=None, **kwargs)
            ret_val = fn(*args, **kwargs)
            self._log_msg(self._exit_msg, fn, args, obj=None, returned=ret_val, **kwargs)
            return ret_val

    def _wrap_class(self, cls) -> type:
        raise NotImplementedError()
