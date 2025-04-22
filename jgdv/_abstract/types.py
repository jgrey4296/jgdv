#!/usr/bin/env python3
"""
Types that help add clarity

Provides a number of type aliases and shorthands.
Such as `Weak[T]` for a weakref, `Stack[T]`, `Queue[T]` etc for lists,
and `Maybe[T]`, `Result[T, E]`, `Either[L, R]`.

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import pathlib as pl
import types
from collections import deque
from collections.abc import (
    Callable,
    Generator,
    Hashable,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    ValuesView,
)
from re import Match, Pattern
from typing import Annotated, Any, Never, Self, TypeGuard, final
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 3rd party imports
from packaging.specifiers import SpecifierSet
from packaging.version import Version

# ##-- end 3rd party imports

# ##-- Generated Exports
__all__ = ( # noqa: RUF022
# -- Types
"AbsPath", "CHECKTYPE", "Char", "Ctor", "DateTime", "Decorator", "Depth", "DictItems",
"DictKeys", "DictVals", "E_", "Either", "Fifo", "FmtKey", "FmtSpec", "FmtStr", "Frame",
"Func", "Ident", "Lambda", "Lifo", "M_", "Maybe", "Method", "Module", "Mut", "NoMut", "Queue",
"R_", "RelPath", "Result", "Rx", "RxMatch", "RxStr", "Seconds", "Stack", "SubOf", "TimeDelta",
"Traceback", "Url", "VList", "Vector", "VerSpecStr", "VerStr", "Weak",

)
# ##-- end Generated Exports

##-- strings
type VerStr                   = Annotated[str, Version] # A Version String
type VerSpecStr               = Annotated[str, SpecifierSet]
type Ident                    = Annotated[str, UUID] # Unique Identifier Strings
type FmtStr                   = Annotated[str, None] # Format Strings like 'blah {val} bloo'
type FmtSpec                  = Annotated[str, None] # Format and conversion parameters. eg: 'blah {val:<9!r}' would be ':<10!r'
type FmtKey                   = str # Names of Keys in a FmtStr
type RxStr                    = Annotated[str, Pattern]
type Char                     = Annotated[str, lambda x: len(x) == 1]
type Url                      = Annotated[str, "url"]

##-- end strings

##-- paths
type RelPath = Annotated[pl.Path, lambda x: not x.is_absolute()]
type AbsPath = Annotated[pl.Path, lambda x: x.is_absolute()]

##-- end paths

##-- regex
type Rx                       = Pattern
type RxMatch                  = Match

##-- end regex

##-- callables
type Ctor[T]                   = type[T] | Callable[[*Any], T]
type Func[**I, O]              = Callable[I, O]
type Method[**I, O]            = types.MethodType[I, O]
type Decorator[F:Func]         = Callable[[F], F]
type Lambda[**I, O]            = types.LambdaType[I, O]

##-- end callables

##-- containers
type Weak[T]                  = ref[T]
type Stack[T]                 = list[T]
type Fifo[T]                  = list[T]
type Queue[T]                 = deque[T]
type Lifo[T]                  = list[T]
type Vector[T]                = list[T]

##-- end containers

##-- utils
type VList[T]                 = T | list[T]
type Mut[T]                   = Annotated[T, "Mutable"]
type NoMut[T]                 = Annotated[T, "Immutable"]

type Maybe[T]                 = T | None
type Result[T, E:Exception]   = T | E
type Either[L, R]             = L | R
type SubOf[T]                 = TypeGuard[T]

##-- end utils

##-- shorthands
type M_[T]                    = Maybe[T]
type R_[T, E:Exception]       = Result[T,E]
type E_[L, R]                 = Either[L,R]

##-- end shorthands

##-- numbers
type Depth              = Annotated[int, lambda x: 0 <= x]
type Seconds            = Annotated[int, lambda x: 0 <= x]
type DateTime           = datetime.datetime
type TimeDelta          = datetime.timedelta

##-- end numbers

##-- dicts
type DictKeys           = KeysView
type DictItems          = ItemsView
type DictVals           = ValuesView

##-- end dicts

##-- tracebacks and frames
type Traceback = types.TracebackType
type Frame     = types.FrameType

##-- end tracebacks and frames

##-- misc
type Module    = types.ModuleType
type CHECKTYPE = Maybe[type|types.GenericAlias|types.UnionType]

##-- end misc
