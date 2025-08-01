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
import re
import time
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from jgdv._abstract.protocols.stdlib import Mapping_p

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
    import pathlib as pl
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
type TomlTypes = (str | int | float | bool | list[TomlTypes] | dict[str,TomlTypes] | datetime.datetime)
type ProxyWrapper[T] = Callable[[*Any], T]
# Body:

class ChainProxy_p[T](Protocol):
    """ The proxy interface

    Used for special access like::

        cg.on_fail(...).val()

    """

    def __call__(self, wrapper:Maybe[ProxyWrapper[T]]=None, fallback_wrapper:Maybe[ProxyWrapper[T]]=None) -> T: ...

    def __getattr__(self, attr:str) -> Self: ...

    def __getitem__(self, keys:int|str|tuple[str]) -> Self: ...

class ProxyEntry_p(Protocol):

    def on_fail[T](self, fallback:Maybe[T]=None, types:Maybe[type[T]]=None, *, non_root:bool=False) -> ChainProxy_p[T]: ...

    def first_of[T](self, fallback:Maybe[T]=None, types:Maybe[type[T]]=None) -> ChainProxy_p[T]: ...

    def all_of[T](self, fallback:Maybe[T]=None, types:Maybe[type[T]]=None) -> ChainProxy_p[T]: ...

    def flatten_on[T](self, fallback:Maybe[T]) -> ChainProxy_p[T]: ...

    def match_on(self, **kwargs:tuple[str,Any]) -> ChainProxy_p: ...

@runtime_checkable
class ChainGuard_p(ProxyEntry_p, Mapping_p, Protocol):
    """ The interface for a base ChainGuard object """

    @override
    def get(self, key:str, default:Maybe=None) -> Maybe: ...

    @classmethod
    def read[T:ChainGuard_p](cls:T, text:str) -> T: ...

    @classmethod
    def from_dict(cls, data:dict) -> Self: ...

    @classmethod
    def load(cls, *paths:str|pl.Path) -> Self: ...

    @classmethod
    def load_dir(cls, dirp:str|pl.Path) -> Self: ...

    @staticmethod
    def report_defaulted() -> list[str]: ...

    def __init__(self, data:Maybe=None, *, index:Maybe[list[str]]=None, mutable:bool=False) -> None: ...

    def to_file(self, path:pl.Path) -> None: ...

    def _table(self) -> dict[str,Any]: ...

    def _index(self) -> list[str]: ...

class ChainGuard_i(ChainGuard_p, Protocol):
    pass
