#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
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
import weakref
from uuid import UUID, uuid1

##-- end builtin imports

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
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Func
## isort: on
# ##-- end type checking

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from ._interface import DEL_LOG_K
from jgdv.decorators._interface import ClsDecorator_p

DEBUG_DESTRUCT_ON = False

def _log_del(self:Any) -> None:  # noqa: ANN401
    """ standalone del logging """
    logging.warning("Deleting: %s", self)

def _decorate_del(fn:Func[..., None]) -> Func[..., None]:
    """ wraps existing del method """
    @ftz.wraps(fn)
    def _wrapped(self, *args:Any) -> None:  # noqa: ANN001, ANN401
        logging.warning("Deleting: %s", self)
        fn(*args)

    return _wrapped

def LogDel(cls:type) -> type:  # noqa: N802
    """
    A Class Decorator, attaches a debugging statement to the object destructor
    To activate, add classvar of {jgdv.debugging._interface.DEL_LOG_K} = True
    to the class.
    """
    match (getattr(cls, DEL_LOG_K, default=False), # type: ignore[call-overload]
           hasattr(cls, "__del__")):
        case (False, _):
            pass
        case (True, True):
            assert(hasattr(cls, "__del__"))
            setattr(cls, "__del__", _decorate_del(cls.__del__))  # noqa: B010
        case (True, False):
            setattr(cls, "__del__", _log_del)  # noqa: B010
    return cls
##--|
class LogDestruction(ClsDecorator_p):
    """
    A Decorator to log when instances of a class are deleted
    """

    def _debug_del(self) -> None:
        """ standalone del logging """
        logging.warning("Deleting: %s", self)

    def _debug_del_dec(self, fn:Func) -> Callable:
        """ wraps existing del method """

        def _wrapped(_self:object, *args, **kwargs) -> None:
            logging.warning("Deleting: %s", _self)
            fn(_self, *args, **kwargs)

        return _wrapped

    @override
    def __call__[T](self, cls:type[T]) -> type[T]:
        """
        A Class Decorator, attaches a debugging statement to the object destructor
        """
        match (DEBUG_DESTRUCT_ON, hasattr(cls, "__del__")):
            case (False, _):
                pass
            case (True, True):
                setattr(cls, "__del__", self._debug_del_dec(cls.__del__)) # type: ignore[attr-defined]  # noqa: B010
            case (True, False):
                setattr(cls, "__del__", self._debug_del)  # noqa: B010
        return cls
