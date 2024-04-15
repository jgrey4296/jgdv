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

DEBUG_DESTRUCT_ON = False

class LogDestruction(DejaVuDecorator_i):

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
