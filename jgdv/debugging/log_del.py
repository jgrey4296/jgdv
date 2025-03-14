#!/usr/bin/env python3
"""


"""
# ruff: noqa:

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
import time
import types
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from . import _interface as API  # noqa: N812

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
    from jgdv import Maybe, Func
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

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

def LogDel(cls:type) -> type:  # noqa: FBT001, N802
    """
    A Class Decorator, attaches a debugging statement to the object destructor
    To activate, add classvar of {jgdv.debugging._interface.DEL_LOG_K} = True
    to the class.
    """
    match (getattr(API.DEL_LOG_K, False), hasattr(cls, "__del__")):
        case (False, _):
            pass
        case (True, True):
            setattr(cls, "__del__", _decorate_del(cls.__del__))
        case (True, False):
            setattr(cls, "__del__", _log_del)
    return cls
