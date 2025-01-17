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
import typing
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
# ##-- end stdlib imports

from .core import DecoratorBase, _TargetType_e

# ##-- type aliases
# isort: off
if typing.TYPE_CHECKING:
   from jgdv import Maybe

# isort: on
# ##-- end type aliases

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class DataDecorator(DecoratorBase):
    """ Adds Data to the target for use in the decorator """

    def __init__(self, keys:str|list[str], **kwargs):
        kwargs.setdefault("mark", "_d_marked")
        kwargs.setdefault("data", "_d_vals")
        super().__init__(**kwargs)
        match keys:
            case list():
                self._data = keys
            case _:
                self._data = [keys]

    def __call__(self, fn):
        if not bool(self._data):
            return fn

        return super().__call__(fn)

    def add_annotations(self, fn, ttype:_TargetType_e) -> list:
        """ Apply metadata to target

        prepend annotations, so written decorator order is the same as written arg order:
        (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        """
        data                        = self._data[:]
        new_annotations             = data + fn.__dict__.get(self._data_key, [])
        fn.__dict__[self._data_key] = new_annotations
        return new_annotations
