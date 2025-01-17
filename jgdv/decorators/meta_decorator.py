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

class MetaDecorator(DecoratorBase):
    """
    Adds metadata without modifying runtime behaviour of target
    """

    def __init__(self, value:str|list[str], **kwargs):
        kwargs.setdefault("mark", "_meta_marked")
        kwargs.setdefault("data", "_meta_vals")
        super().__init__(**kwargs)
        match value:
            case list():
                self._data = value
            case _:
                self._data = [value]

    def add_annotations(self, target, ttype:_TargetType_e) -> list:
        """ Apply metadata to target

        prepend annotations, so written decorator order is the same as written arg order:
        (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        """
        data                        = self._data[:]
        new_annotations             = data + target.__dict__.get(self._data_key, [])
        setattr(target, self._data_key, new_annotations)
        return new_annotations
