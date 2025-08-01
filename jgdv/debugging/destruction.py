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

    from jgdv import Maybe
## isort: on
# ##-- end type checking

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv.decorators._interface import ClsDecorator_p

DEBUG_DESTRUCT_ON = False

class LogDestruction(ClsDecorator_p):
    """
    A Decorator to log when instances of a class are deleted
    """

    def _debug_del(self):
        """ standalone del logging """
        logging.warning("Deleting: %s", self)

    def _debug_del_dec(fn):
        """ wraps existing del method """
        def _wrapped(*args):
            logging.warning("Deleting: %s", self)
            fn(*args)

    def __call__(self):
        """
        A Class Decorator, attaches a debugging statement to the object destructor
        """
        match (DEBUG_DESTRUCT_ON, hasattr(cls, "__del__")):
            case (False, _):
                pass
            case (True, True):
                setattr(cls, "__del__", self._debug_del_dec(cls.__del__))
            case (True, False):
                setattr(cls, "__del__", self._debug_instance_del)
        return cls
