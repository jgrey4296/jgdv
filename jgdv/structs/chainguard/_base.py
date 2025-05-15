#!/usr/bin/env python3
"""
The core implementation of the ChainGuard object,
which is then extended with mixins.
"""

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
from uuid import UUID, uuid1

# ##-- end stdlib imports

from .errors import GuardedAccessError
from .mixins.access_m import super_get, super_set
from . import _interface as API
from jgdv import Proto

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
    from collections.abc import ItemsView, KeysView, ValuesView
    from ._interface import TomlTypes
    from jgdv import Maybe
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

type InputData = dict[str, TomlTypes]

##--|

class GuardBase(dict):
    """
    Provides access to toml data (ChainGuard.load(apath))
    but as attributes (data.a.path.in.the.data)
    instead of key access (data['a']['path']['in']['the']['data'])

    while also providing typed, guarded access:
    data.on_fail("test", str | int).a.path.that.may.exist()

    while it can then report missing paths:
    data.report_defaulted() -> ['a.path.that.may.exist.<str|int>']
    """

    def __init__(self, data:Maybe[InputData]=None, *, index:Maybe[list[str]]=None, mutable:bool=False) -> None:
        super().__init__()
        super_set(self, "__table", data or {})
        super_set(self, "__index"   , (index or ["<root>"])[:])
        super_set(self, "__mutable" , mutable)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}:{list(self.keys())}>"

    def __len__(self) -> int:
        return len(self._table())

    def __call__(self) -> TomlTypes:
        msg = "Don't call a ChainGuard, call a GuardProxy using methods like .on_fail"
        raise GuardedAccessError(msg)

    def __iter__(self) -> Iterator:
        return iter(getattr(self, "__table").keys())

    def __contains__(self, _key: object) -> bool:
        return _key in self.keys()

    def _index(self) -> list[str]:
        return super_get(self, "__index")[:]

    def _table(self) -> dict[str,TomlTypes]:
        return super_get(self, "__table")

    def keys(self) -> KeysView[str]: # type: ignore[override]
        table = super_get(self, "__table")
        return table.keys()

    def items(self) -> ItemsView[str, TomlTypes]: # type: ignore[override]
        match super_get(self, "__table"):
            case dict() as val:
                return val.items()
            case list() as val:
                return {self._index()[-1]: val}.items()
            case GuardBase() as val:
                return val.items()
            case x:
                msg = "Unknown table type"
                raise TypeError(msg, x)

    def values(self) -> list|ValuesView[TomlTypes]: # type: ignore[override]
        match super_get(self, "__table"):
            case dict() as val:
                return val.values()
            case list() as val:
                return val
            case _:
                raise TypeError()


    def update(self, *args) -> Never: # type: ignore[override]  # noqa: ANN002
        msg = "ChainGuards are immutable"
        raise NotImplementedError(msg)
