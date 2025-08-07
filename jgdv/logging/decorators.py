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
import weakref
from uuid import UUID, uuid1
# ##-- end stdlib imports

from jgdv import Maybe
from jgdv.decorators import Decorator

from ._interface import Logger, LOGDEC_PRE

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
    from typing import TypeGuard, Concatenate
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Lambda
## isort: on
# ##-- end type checking

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Global Vars:

# Body:

class LogCall(Decorator):
    """ A Decorator for announcing the entry/exit of a function call

    eg:
    @LogCall(enter="Entering", exit="Exiting", level=logmod.INFO)
    def a_func()...
    """

    def __init__(self, enter:Maybe[str|Lambda]=None, exit:Maybe[str|Lambda]=None, level:int|str=logmod.INFO, logger:Maybe[Logger]=None) -> None:  # noqa: A002
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

    def _log_msg(self, msg:Maybe[str|Lambda], fn:Callable, args:Iterable, **kwargs:Any) -> None:  # noqa: ANN401
        match msg:
            case None:
                return None
            case types.FunctionType():
                msg = msg(fn, *args, **kwargs)
            case str():
                pass
            case _:
                raise TypeError(msg)

        self._logger.log(self._level, msg)

    def _wrap_method[X, **I, O](self, fn:Callable[Concatenate[X, I],O]) -> Callable[Concatenate[X, I],O]:

        def basic_wrapper(_self:X, *args:I.args, **kwargs:I.kwargs) -> O:
            self._log_msg(self._enter_msg, fn, args, obj=_self, **kwargs)
            ret_val = fn(_self, *args, **kwargs)
            self._log_msg(self._exit_msg, fn, args, obj=_self, returned=ret_val, **kwargs)
            return ret_val

        return basic_wrapper

    def _wrap_fn[**I, O](self, fn:Callable[I, O]) -> Callable[I, O]:

        def basic_wrapper(*args:I.args, **kwargs:I.kwargs) -> O:
            self._log_msg(self._enter_msg, fn, args, obj=None, **kwargs)
            ret_val = fn(*args, **kwargs)
            self._log_msg(self._exit_msg, fn, args, obj=None, returned=ret_val, **kwargs)
            return ret_val

        return basic_wrapper

    def _wrap_class[T](self, cls:type[T]) -> type[T]:
        raise NotImplementedError()
