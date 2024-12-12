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

type Stack[T]                = NewType("Stack", list[T])
type Queue[T]                = NewType("Queue", list[T])
type Vector[T]               = NewType("Vector", list[float])

type Ident                   = NewType("Identifier", str)

type Depth                   = NewType("Depth", int)
type Seconds                 = NewType("Seconds", int)

type Maybe[T]                = T | None
type Result[T, E:Exception]  = T | E
type Either[L, R]            = L | R
