#!/usr/bin/env python3
"""
A Proxy for ChainGuard,
  which allows you to use the default attribute access
  (data.a.b.c)
  even when there might not be an `a.b.c` path in the data.

  Thus:
  data.on_fail(default_value).a.b.c()

  Note: To distinguish between not giving a default value,
  and giving a default value of `None`,
  wrap the default value in a tuple: (None,)
"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import atexit#  for @atexit.register
import collections
import contextlib
import datetime
import enum
import faulthandler
import functools as ftz
import hashlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types as types_
import weakref
from copy import deepcopy
from time import sleep
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Proto
from .._base import GuardBase
from .._interface import TomlTypes, ChainProxy_p
from ..errors import GuardedAccessError
from .base import GuardProxy

# ##-- end 1st party imports

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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
from typing import Never

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(ChainProxy_p)
class GuardFailureProxy(GuardProxy):
    """
    A Wrapper for guarded access to toml values.
    you get the value by calling it.
    Until then, it tracks attribute access,
    and reports that to GuardBase when called.
    It also can type check its value and the value retrieved from the toml data
    """

    def __init__(self, data:GuardBase, types:Any=None, index:Maybe[list[str]]=None, fallback:TomlTypes|Never=Never):
        super().__init__(data, types=types, index=index)
        if fallback == (None,):
            self._fallback = None
        else:
            self._fallback = fallback

        if fallback:
            self._match_type(self._fallback)

    def __call__(self, wrapper:Maybe[callable[[TomlTypes], Any]]=None, fallback_wrapper:Maybe[callable[[TomlTypes], Any]]=None) -> Any:
        """
        Reify a proxy into an actual value, or its fallback.
        Optionally call a wrapper function on the actual value,
        or a fallback_wrapper function on the fallback
        """
        self._notify()
        wrapper : callable[[TomlTypes], TomlTypes] = wrapper or (lambda x: x)
        fallback_wrapper                           = fallback_wrapper or (lambda x: x)
        match self._data, self._fallback:
            case x, y if x is Never and y is Never:
                raise ValueError("No Value, and no fallback")
            case x, None if x is Never or x is None:
                val = None
            case x, data if x is Never or x is None:
                val = fallback_wrapper(data)
            case GuardBase() as data, _:
                val = wrapper(dict(data))
            case _ as data, _:
                val = wrapper(data)

        return self._match_type(val)

    def __getattr__(self, attr:str) -> GuardProxy:
        try:
            match self._data:
                case x if x is Never:
                    raise GuardedAccessError()
                case GuardBase():
                    return self._inject(self._data[attr], attr=attr)
                case _:
                    return self._inject(attr=attr)
        except GuardedAccessError:
            return self._inject(clear=True, attr=attr)

    def __getitem__(self, keys:str|tuple[str]) -> GuardProxy:
        curr = self
        match keys:
            case tuple():
                for key in keys:
                    curr = curr.__getattr__(key)
            case str():
                curr = self.__getattr__(keys)

        return curr

    def _inject(self, val:tuple[Any]=Never, attr:Maybe[str]=None, clear:bool=False) -> GuardProxy:
        match val:
            case _ if clear:
                val = Never
            case x if x is Never:
                val = self._data
            case _:
                pass

        return GuardFailureProxy(val,
                                 types=self._types,
                                 index=self._index(attr),
                                 fallback=self._fallback)
