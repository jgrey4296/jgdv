#!/usr/bin/env python3
"""
Types that help add clarity


"""

# Imports:
from __future__ import annotations

from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match, NewType,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload, Optional,
                    runtime_checkable)
from uuid import UUID, uuid1

__all__                       = ["Stack", "Queue", "Vector", "Ident", "Depth", "Seconds", "Maybe", "Result", "Either"]

type _T                       = Any

type Stack[T]                 = list[T]
type Queue[T]                 = list[T]
type Vector[T]                = list[T]
type Ident                    = str

type Maybe[_T]                = _T | None
type Result[_T, E:Exception]  = _T | E
type Either[L, R]             = L | R

# TODO : Make These subtypes of int that are 0<=x
type Depth              = int
type Seconds            = int
