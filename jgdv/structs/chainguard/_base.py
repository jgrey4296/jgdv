
#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
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

# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
import typing
import weakref
from collections import ChainMap
from collections.abc import ItemsView, KeysView, ValuesView
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv.structs.chainguard import TomlTypes

# ##-- end 1st party imports

from .errors import GuardedAccessError
from .mixins.access_m import super_get, super_set

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class GuardBase(Mapping[str, TomlTypes]):
    """
    Provides access to toml data (ChainGuard.load(apath))
    but as attributes (data.a.path.in.the.data)
    instead of key access (data['a']['path']['in']['the']['data'])

    while also providing typed, guarded access:
    data.on_fail("test", str | int).a.path.that.may.exist()

    while it can then report missing paths:
    data.report_defaulted() -> ['a.path.that.may.exist.<str|int>']
    """

    def __init__(self, data:dict[str,TomlTypes]=None, *, index:Maybe[list[str]]=None, mutable:bool=False):
        super().__init__()
        super_set(self, "__table", data or {})
        super_set(self, "__index"   , (index or ["<root>"])[:])
        super_set(self, "__mutable" , mutable)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}:{list(self.keys())}>"

    def __len__(self) -> int:
        return len(self._table())

    def __call__(self) -> TomlTypes:
        raise GuardedAccessError("Don't call a ChainGuard, call a GuardProxy using methods like .on_fail")

    def __iter__(self) -> iter:
        return iter(getattr(self, "__table").items())

    def __contains__(self, _key: object) -> bool:
        return _key in self.keys()

    def _index(self) -> list[str]:
        return super_get(self, "__index")[:]

    def _table(self) -> dict[str,TomlTypes]:
        return super_get(self, "__table")

    def keys(self) -> KeysView[str]:
        table = super_get(self, "__table")
        return table.keys()

    def items(self) -> ItemsView[str, TomlTypes]:
        match super_get(self, "__table"):
            case dict() as val:
                return val.items()
            case list() as val:
                return dict({self._index()[-1]: val}).items()
            case GuardBase() as val:
                return val.items()
            case x:
                raise TypeError("Unknown table type", x)

    def values(self) -> ValuesView[TomlTypes]:
        match super_get(self, "__table"):
            case dict() as val:
                return val.values()
            case list() as val:
                return val
            case _:
                raise TypeError()
