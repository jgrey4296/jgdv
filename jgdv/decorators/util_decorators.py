#!/usr/bin/env python3
"""

"""
# ruff: noqa: ERA001
# Import:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import sys
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
# ##-- end stdlib imports

from jgdv.debugging import TraceBuilder
from ._core import IdempotentDec, MetaDec, MonotonicDec

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Concatenate
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from . import _interface as API # noqa: N812

    from jgdv import Maybe, Either, Method, Func
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard, ParamSpec
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    type Logger = logmod.Logger

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class NoSideEffects(MetaDec):
    """ TODO Mark a Target as not modifying external variables """
    pass

class CanRaise(MetaDec):
    """ TODO mark a target as able to raise certain errors.
    Non-exaustive, doesn't change runtime behaviour,
    just to simplify documentation

    """
    pass

class Breakpoint(IdempotentDec):
    """
      Decorator to attach a breakpoint to a function, without pausing execution
    """

    def __call__[**I, O](self, target:Callable[I,O]) -> Callable[I,O]:
        msg = "needs RunningDebugger"
        raise NotImplementedError(msg)
    # # TODO handle repeats
    # if args[0].breakpoint:

        #     f_code = f.__code__
        #     db = RunningDebugger()
        #     # Ensure trace function is set
        #     sys.settrace(db.trace_dispatch)
        #     if not db.get_break(f_code.co_filename, f_code.co_firstlineno+2):
        #         db.set_break(f_code.co_filename,
        #                     f_code.co_firstlineno+2,
        #                     True)
        #     else:
        #         bp = Breakpoint.bplist[f_code.co_filename,
        #                             f_code.co_firstlineno+2][0]
        #         bp.enable()

        # return self._func(self, *args, **kwargs)

class DoMaybe(MonotonicDec):
    """ Make a fn or method propagate None's """
    type MethMb[Obj,X,**I,O]  = Callable[Concatenate[Obj, X, I],O]
    type FuncMb[X,**I,O]      = Callable[Concatenate[X, I],O]
                                                                                                                     # def __call__[**I, X,Obj, O](self, target:MethMb[Obj,X,I,O]|FuncMb[X,I,O], *args:Any, **kwargs:Any) -> MethMb[Obj,Maybe[X],I,O]|FuncMb[Maybe[X],I,O]: # type: ignore[override]

    @overload # type: ignore[override]
    def __call__[Obj,**I,X,O](self, target:MethMb[Obj,X,I,O], *args:Any, **kwargs:Any) -> MethMb[Obj,Maybe[X],I,O]:  # noqa: ANN401
        pass

    @overload
    def __call__[**I,X,O](self, target:FuncMb[X,I,O], *args:Any, **kwargs:Any) -> FuncMb[Maybe[X],I,O]: # noqa: ANN401
        pass

    def __call__(self, target, *args, **kwargs):
        return MonotonicDec.__call__(self, target, *args, **kwargs)

    @override
    def _wrap_method_h[Obj, X, **I, O](self, meth:MethMb[Obj,X,I,Maybe[O]]) -> MethMb[Obj,Maybe[X],I,Maybe[O]]: # type: ignore[override]

        def _prop_maybe(_self:Obj, fst:Maybe[X], *args:I.args, **kwargs:I.kwargs) -> Maybe[O]:
            match fst:
                case None:
                    return None
                case x:
                    return meth(_self, x, *args, **kwargs)

        return _prop_maybe

    @override
    def _wrap_fn_h[X, **I, O](self, fn:FuncMb[X, I, Maybe[O]]) -> FuncMb[Maybe[X], I, Maybe[O]]: # type: ignore[override]

        def _prop_maybe(fst:Maybe[X], *args:I.args, **kwargs:I.kwargs) -> Maybe[O]:
            match fst:
                case None:
                    return None
                case x:
                    try:
                        return fn(x, *args, **kwargs)
                    except Exception as err:
                        err.with_traceback(TraceBuilder[2:]) # type: ignore[misc]
                        raise

        return _prop_maybe

class DoEither(MonotonicDec):
    """ Either do the fn/method, or propagate the error """

    def _wrap_method_h[X,Y, **I, O, E:Exception](self, meth:Method[Concatenate[X, Y, I], Either[O,E]]) -> API.Decorated[Concatenate[X, Y|E, I], Either[O, E]]: # type: ignore[override]

        def _prop_either(_self:X, fst:Y|E, *args:I.args, **kwargs:I.kwargs) -> Either[O, E]:
            match fst:
                case Exception() as err:
                    return cast("E", err)
                case x:
                    try:
                        return meth(_self, x, *args, **kwargs)
                    except Exception as err:  # noqa: BLE001
                        err.with_traceback(TraceBuilder[2:]) # type: ignore[misc]
                        return cast("E", err)

        return _prop_either

    def _wrap_fn_h[X, **I, O, E:Exception](self, fn:Func[Concatenate[X, I], O]) -> Func[Concatenate[X|E, I], Either[O, E]]: # type: ignore[override]

        def _prop_either(fst:X|E, *args:I.args, **kwargs:I.kwargs) -> Either[O, E]:
            match fst:
                case Exception() as err:
                    return cast("E", err)
                case x:
                    try:
                        return fn(x, *args, **kwargs)
                    except Exception as err:  # noqa: BLE001
                        err.with_traceback(TraceBuilder[2:]) # type: ignore[misc]
                        return cast("E", err)

        return _prop_either
