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
from . import _interface as API  # noqa: N812
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

type InputData = dict
TABLE_K    : Final[str] = "__table"
INDEX_K    : Final[str] = "__index"
MUTABLE_K  : Final[str] = "__mutable"
ROOT_STR   : Final[str] = "<root>"
super_get             = object.__getattribute__
super_set             = object.__setattr__
USCORE   : Final[str] = "_"
DASH     : Final[str] = "-"
MUTABLE  : Final[str] = "__mutable"
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

    def __init__(self, data:Maybe[InputData]=None, *, index:Maybe[Iterable[int|str]]=None, mutable:bool=False) -> None:
        super().__init__()
        super_set(self, TABLE_K, data or {})
        super_set(self, INDEX_K, tuple(index or [ROOT_STR]))
        super_set(self, MUTABLE_K, mutable)

    @override
    def __repr__(self) -> str:
        match self._table():
            case dict() as d:
                return f"<{self.__class__.__name__}:{list(d.keys())}>"
            case d:
                return f"<{self.__class__.__name__}:{d}>"

    @override
    def __eq__(self, other:object) -> bool:
        match other:
            case GuardBase() as base:
                return  self._table() == base._table()
            case dict() as adict:
                return self._table() == adict
            case _:
                return False

    @override
    def __hash__(self) -> int: # type: ignore[override]
        return hash(self._table())

    @override
    def __len__(self) -> int:
        return len(self._table())

    def __call__(self) -> None:
        msg = "Don't call a ChainGuard, call a GuardProxy using methods like .on_fail"
        raise GuardedAccessError(msg)

    @override
    def __iter__(self) -> Iterator:
        return iter(getattr(self, TABLE_K).keys())

    @override
    def __contains__(self, _key: object) -> bool:
        match _key:
            case str():
                return _key in self.keys() or _key.replace("_","-") in self.keys()
            case x:
                return x in self.keys()


    @override
    def __setattr__(self, attr:str, value:Any) -> None:
        if not getattr(self, MUTABLE):
            raise TypeError()
        super_set(self, attr, value)

    def __getattr__(self, attr:str) -> Any:  # noqa: ANN401
        return self.__getitem__(attr)

    @override
    def __getitem__(self, keys:int|str|list[str]|tuple[int|str, ...]) -> Any:
        table    : dict
        curr     : dict
        ##--|
        match keys:
            case tuple():
                pass
            case int()|str():
                keys = (keys, )
            case x:
                raise TypeError(type(x))


        table  = self._table()
        curr   = table
        for k in keys:
            match k:
                case str() if k in curr:
                    pass
                case str() if (k:=k.replace(USCORE, DASH)) in curr:
                    pass
                case str():
                    index_s    = ".".join(map(str, self._index(k)))
                    available  = " ".join(table.keys())
                    msg        = f"{index_s} not found, available: [{available}]"
                    raise GuardedAccessError(msg)
                case int() if k < len(curr):
                    pass
                case int():
                    raise GuardedAcccessError("tried to access a list of wrong length")

            match curr.get(k, None):
                case dict() as result:
                    curr = result
                case result:
                    curr = result
        else:
            match curr:
                case dict():
                    return type(self)(curr, index=self._index(keys))
                case [*xs] if all(isinstance(x, dict) for x in xs):
                    index = self._index(keys)
                    return [type(self)(x, index=index) for x in xs]
                case [*xs]:
                    return xs
                case x:
                    return x

    @override
    def get(self, key:str, default:Maybe=None) -> Maybe:
        if key in self:
            return self.__getitem__(key)

        return default
    ##--|
    def _index(self, sub:Maybe[int|str|tuple[int|str, ...]]=None) -> tuple[int|str, ...]:
        match sub:
            case None:
                return super_get(self, INDEX_K)[:]
            case int()|str() as x:
                return (*super_get(self, INDEX_K), x)
            case [*xs]:
                return (*super_get(self, INDEX_K), *xs)
            case x:
                raise TypeError(type(x))

    def _table(self) -> dict:
        return super_get(self, TABLE_K)

    @override
    def keys(self) -> KeysView[str]: # type: ignore[override]
        table = super_get(self, TABLE_K)
        return table.keys()

    @override
    def items(self) -> ItemsView: # type: ignore[override]
        match super_get(self, TABLE_K):
            case dict() as val:
                return val.items()
            case list() as val:
                return {self._index()[-1]: val}.items()
            case GuardBase() as val:
                return val.items()
            case x:
                msg = "Unknown table type"
                raise TypeError(msg, x)

    @override
    def values(self) -> list|ValuesView: # type: ignore[override]
        match super_get(self, TABLE_K):
            case dict() as val:
                return val.values()
            case list() as val:
                return val
            case _:
                raise TypeError()

    @override
    def update(self, *args) -> Never: # type: ignore[override]  # noqa: ANN002
        msg = "ChainGuards are immutable"
        raise NotImplementedError(msg)
