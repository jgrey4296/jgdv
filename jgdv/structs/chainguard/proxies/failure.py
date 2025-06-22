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
from typing import Never

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from .._interface import ChainGuard_i

    type Wrapper = Callable[[TomlTypes], Any]

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

NO_FALLBACK : Final[tuple] = ()
##--|
@Proto(ChainProxy_p)
class GuardFailureProxy(GuardProxy):
    """
    A Wrapper for guarded access to toml values.
    you get the value by calling it.
    Until then, it tracks attribute access,
    and reports that to GuardBase when called.
    It also can type check its value and the value retrieved from the toml data
    """

    def __init__(self, data:Maybe[TomlTypes|GuardBase], types:Maybe=None, index:Maybe[list[str]]=None, fallback:Maybe[TomlTypes|tuple]=NO_FALLBACK) -> None:
        super().__init__(data, types=types, index=index, fallback=fallback)
        match self._fallback:
            case tuple():
                pass
            case _:
                self._match_type(self._fallback)

    @override
    def __call__(self, wrapper:Maybe[Wrapper]=None, fallback_wrapper:Maybe[Wrapper]=None, **kwargs:Any) -> Any:
        """
        Reify a proxy into an actual value, or its fallback.
        Optionally call a wrapper function on the actual value,
        or a fallback_wrapper function on the fallback
        """
        self._notify()
        wrapper           = wrapper or (lambda x: x)
        fallback_wrapper  = fallback_wrapper or (lambda x: x)
        match self._data, self._fallback:
            case None, tuple() as x if x == ():
                msg = "No Value, and no fallback"
                raise ValueError(msg)
            case GuardBase() as data, _:
                val = wrapper(data)
            case None, data:
                val = fallback_wrapper(data) # type: ignore[arg-type]
            case _ as data, _:
                val = wrapper(data) # type: ignore[arg-type]

        return self._match_type(val)

    def __getattr__(self, attr:str) -> GuardProxy:
        try:
            match self._data:
                case None:
                    raise GuardedAccessError()  # noqa: TRY301
                case GuardBase():
                    return self._inject(self._data[attr], attr=attr)
                case _:
                    return self._inject(attr=attr)
        except GuardedAccessError:
            return self._inject(clear=True, attr=attr)

    def __getitem__(self, keys:str|tuple[str]) -> GuardProxy:
        curr : GuardProxy = self
        match keys:
            case tuple():
                for key in keys:
                    curr = getattr(curr, key)
            case str():
                curr = getattr(self, keys)

        return curr

