#!/usr/bin/env python3
"""
An Adaptation of typeshed's protocol's of the stdlib.
"""
# mypy: disable-error-code="explicit-override"
# ruff: noqa: PLW1641, ANN401

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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

##--| General:

class Hashable_p(Protocol):

    def __hash__(self) -> int: ...

class Iterable_p[V](Protocol):

    def __iter__(self) -> Iterator_p[V]: ...

class Iterator_p[V](Iterable_p, Protocol):

    def __next__(self) -> V: ...

    def __iter__(self) -> Self: ...

class Reversible_p(Iterable_p, Protocol):

    def __reversed__(self) -> Self: ...

class Generator_p(Iterator_p, Protocol):

    def __next__(self) -> Any: ...

    def send(self, value:Any) -> Any: ...

    def throw(self, typ:Any, val:Maybe=None, tb:Maybe=None) -> Any: ...

    def close(self) -> None: ...

class Sized_p(Protocol):

    def __len__(self) -> int: ...

class Container_p[V](Protocol):

    def __contains__(self, x:V) -> bool: ...

class Collection_p(Sized_p, Iterable_p, Container_p, Protocol):
    pass

class Buffer_p(Protocol):

    def __buffer__(self, flags: int) -> memoryview: ...

class Callable_p[*A, K, R](Protocol):

    def __call__(self, *args:*A, **kwds:K) -> R: ...

##--| Sets

class Set_p[V](Collection_p, Protocol):
    """A set is a finite, iterable container.

    This class provides concrete generic implementations of all
    methods except for __contains__, __iter__ and __len__.

    To override the comparisons (presumably for speed, as the
    semantics are fixed), redefine __le__ and __ge__,
    then the other operations will automatically follow suit.
    """

    def __le__(self, other:Self) -> bool: ...

    def __lt__(self, other:Self) -> bool: ...

    def __gt__(self, other:Self) -> bool: ...

    def __ge__(self, other:Self) -> bool: ...

    def __eq__(self, other:object) -> bool: ...

    @classmethod
    def _from_iterable(cls:type[Set_p], it:Iterable_p[V]) -> Set_p[V]: ...

    def __and__(self, other:Self) -> Self: ...

    def __rand__(self, other:Self) -> Self: ...

    def isdisjoint(self, other:Self) -> bool: ...

    def __or__(self, other:Self) -> Self: ...

    def __ror__(self, other:Self) -> Self: ...

    def __sub__(self, other:Self) -> Self: ...

    def __rsub__(self, other:Self) -> Self: ...

    def __xor__(self, other:Self) -> Self: ...

    def __rxor__(self, other:Self) -> Self: ...

    def _hash(self) -> int: ...

class MutableSet_p[V](Set_p[V], Protocol):
    """A mutable set is a finite, iterable container.

    This class provides concrete generic implementations of all
    methods except for __contains__, __iter__, __len__,
    add(), and discard().

    To override the comparisons (presumably for speed, as the
    semantics are fixed), all you have to do is redefine __le__ and
    then the other operations will automatically follow suit.
    """

    def add(self, value:V) -> Self: ...

    def discard(self, value:V) -> None: ...

    def remove(self, value:V) -> None: ...

    def pop(self) -> V: ...

    def clear(self) -> None: ...

    def __ior__(self, it:Iterable_p) -> Self: ...

    def __iand__(self, it:Iterable_p) -> Self: ...

    def __ixor__(self, it:Iterable_p) -> Self: ...

    def __isub__(self, it:Iterable_p) -> Self: ...

##--| Mappings

class Mapping_p[K,V](Collection_p, Protocol):
    """A Mapping_p is a generic container for associating key/value
    pairs.

    This class provides concrete generic implementations of all
    methods except for __getitem__, __iter__, and __len__.
    """

    def __getitem__(self, key:K) -> V: ...

    def get[D:Maybe](self, key:K, default:Maybe[Any]=None) -> V|D: ...

    def __contains__(self, key:K) -> bool: ...

    def keys(self) -> KeysView_p: ...

    def items(self) -> ItemsView_p: ...

    def values(self) -> ValuesView_p: ...

    def __eq__(self, other:object) -> bool: ...

class MappingView_p(Sized_p, Protocol):

    def __init__(self, mapping:Mapping_p) -> None: ...

    def __len__(self) -> int: ...

    def __repr__(self) -> str: ...

class KeysView_p[K](MappingView_p, Set_p, Protocol):

    @classmethod
    def _from_iterable[V](cls:type[KeysView_p], it:Iterable_p[K]) -> KeysView_p[K]: ...

    def __contains__(self, key:K) -> bool: ...

    def __iter__(self) -> Iterator_p: ...

class ItemsView_p[K,V](MappingView_p, Set_p, Protocol):

    @classmethod
    def _from_iterable(cls:type[ItemsView_p], it:Iterable_p) -> ItemsView_p: ...

    def __contains__(self, item:tuple[K,V]) -> bool: ...

    def __iter__(self) -> Iterator_p[tuple[K,V]]: ...

class ValuesView_p[V](MappingView_p, Collection_p, Protocol):

    def __contains__(self, value:V) -> bool: ...

    def __iter__(self) -> Iterator_p: ...

class MutableMapping_p[K,V](Mapping_p[K,V], Protocol):
    """A MutableMapping is a generic container for associating
    key/value pairs.

    This class provides concrete generic implementations of all
    methods except for __getitem__, __setitem__, __delitem__,
    __iter__, and __len__.
    """

    def __setitem__(self, key:K, value:V) -> None: ...

    def __delitem__(self, key:K) -> None: ...

    def pop[D:V|Maybe[object]](self, key:K, default:Maybe[D]=None) -> D: ...

    def popitem(self) -> V: ...

    def clear(self) -> None: ...

    def update(self, other:Iterable_p=(), /, **kwds:Any) -> None: ...

    def setdefault[D:V|Maybe](self, key:K, default:Maybe[D]=None) -> V|D: ...

##--| Sequences

class Sequence_p[V](Reversible_p, Collection_p, Protocol):
    """All the operations on a read-only sequence.

    Concrete subclasses must override __new__ or __init__,
    __getitem__, and __len__.
    """

    # Tell ABCMeta.__new__ that this class should have TPFLAGS_SEQUENCE set.

    def __getitem__(self, index:int) -> V: ...

    def __iter__(self) -> Iterator_p: ...

    def __contains__(self, value:V) -> bool: ...

    def __reversed__(self) -> Self: ...

    def index(self, value:V, start:int=0, stop:Maybe[int]=None) -> int: ...

    def count(self, value:V) -> int: ...

class MutableSequence_p[V](Sequence_p, Protocol):
    """All the operations on a read-write sequence.

    Concrete subclasses must provide __new__ or __init__,
    __getitem__, __setitem__, __delitem__, __len__, and insert().
    """

    def __setitem__(self, index:int, value:V) -> None: ...

    def __delitem__(self, index:int) -> None: ...

    def insert(self, index:int, value:V) -> None: ...

    def append(self, value:V) -> None: ...

    def clear(self) -> None: ...

    def reverse(self) -> None: ...

    def extend(self, values:Iterable_p[V]) -> None: ...

    def pop(self, index:int=-1) -> V: ...

    def remove(self, value:V) -> None: ...

    def __iadd__(self, values:Iterable_p[V]) -> Self: ...
