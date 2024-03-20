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

class DejaVuDecorator_i:
    """ Base Class for decorators that annotate callables """

    def __init__(self, funcOrCls:Callable):
        ftz.update_wrapper(self, funcOrCls)
        self._func = func

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

class DejaVuDelayDecorator_i:
    """ Base Class for decorators that take arguments, then later annotate callables

    https://stackoverflow.com/questions/9416947
      """

    def __init__(self):
        self._func = None

    def __call__(self, func):
        self._func = func
        ftz.update_wrapper(self._wrapper, self._func)
        return self._wrapper

    def _wrapper(self, *args, **kwargs):
        return
