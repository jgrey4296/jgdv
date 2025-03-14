#!/usr/bin/env python3
"""

"""
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
from .core import IdempotentDec, MetaDec, MonotonicDec

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
    from jgdv import Maybe, Either, Method, Func
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
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

    def __call__(self, target:Callable) -> Any:  # noqa: ANN401
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

    def _wrap_method_h[I, O](self, meth:Method[I, O]) -> Method[I, Maybe[O]]:

        def _prop_maybe(_self, fst, *args:Any, **kwargs:Any) -> Maybe[O]:  # noqa: ANN001, ANN401
            match fst:
                case None:
                    return None
                case x:
                    return meth(_self, x, *args, **kwargs)

        return _prop_maybe

    def _wrap_fn_h[I, O](self, fn:Func[I, O]) -> Func[I, Maybe[O]]:

        def _prop_maybe(fst:Any, *args:Any, **kwargs:Any) -> Maybe[O]:  # noqa: ANN401
            match fst:
                case None:
                    return None
                case x:
                    try:
                        return fn(x, *args, **kwargs)
                    except Exception as err:
                        err.with_traceback(TraceBuilder[2:])
                        raise

        return _prop_maybe

class DoEither(MonotonicDec):
    """ Either do the fn/method, or propagate the error """

    def _wrap_method_h[I:Any, O:Any](self, meth:Method[I, O]) -> Method[I, Either[O]]:

        def _prop_either(_self:Any, fst:Any, *args:Any, **kwargs:Any) -> Either[O]:  # noqa: ANN401
            match fst:
                case Exception() as err:
                    return err
                case x:
                    try:
                        return meth(_self, x, *args, **kwargs)
                    except Exception as err:  # noqa: BLE001
                        err.with_traceback(TraceBuilder[2:])
                        return err

        return _prop_either

    def _wrap_fn_h[I:Any, O:Any](self, fn:Func[I, O]) -> Func[I, Either[O]]:

        def _prop_either(fst:Any, *args:Any, **kwargs:Any) -> Either[O]:  # noqa: ANN401
            match fst:
                case Exception() as err:
                    return err
                case x:
                    try:
                        return fn(x, *args, **kwargs)
                    except Exception as err:  # noqa: BLE001
                        err.with_traceback(TraceBuilder[2:])
                        return err

        return _prop_either
