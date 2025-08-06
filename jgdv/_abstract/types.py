#!/usr/bin/env python3
"""
Types that help add clarity

Provides a number of type aliases and shorthands.
Such as ``Weak[T]`` for a weakref, ``Stack[T]``, ``Queue[T]`` etc for lists,
and ``Maybe[T]``, ``Result[T, E]``, ``Either[L, R]``.

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import pathlib as pl
import types
from collections import deque
from collections.abc import (Callable, Generator, Hashable, ItemsView,
                             Iterable, Iterator, KeysView, ValuesView)
from re import Match, Pattern
from typing import (Annotated, Any, Final, Literal, Never, Self, TypeGuard,
                    Union, final, Concatenate)
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
"AbsPath", "Builder", "CHECKTYPE", "Char", "CtorFn", "DateTime", "Decorator", "Depth",
"DictItems", "DictKeys", "DictVals", "E_", "Either", "Fifo", "FmtKey", "FmtSpec", "FmtStr",
"Frame", "Func", "Ident", "Lambda", "Lifo", "M_", "Maybe", "MaybeT", "Method", "Module", "Mut",
"NoMut", "Queue", "R_", "RelPath", "Result", "Rx", "RxMatch", "RxStr", "Seconds", "Stack",
"SubOf", "TimeDelta", "Traceback", "Url", "VList", "Vector", "VerSpecStr", "VerStr",
"Weak",

)
# ##-- end Generated Exports

##-- strings
type VerStr                   = Annotated[str, Version] # A Version String
""" A String representing a Version. """
type VerSpecStr               = Annotated[str, SpecifierSet]
""" A String that describes a version set to match. """
type Ident                    = Annotated[str, UUID]
""" A UUID equivalent str. """
type FmtStr                   = Annotated[str, None]
""" Format Strings like 'blah {val} bloo'. """
type FmtSpec                  = Annotated[str, None]
""" Format and conversion parameters. eg: 'blah {val:<9!r}' would be ':<10!r' """
type FmtKey                   = str
""" Names of Keys in a FmtStr or FmtSpec """
type RxStr                    = Annotated[str, Pattern]
""" A String intented to be compiled as a re.Pattern """
type Char                     = Annotated[str, lambda x: len(x) == 1]
""" A String of length 1. A Single character. """
type Url                      = Annotated[str, "url"]
""" A String that is a url. """

##-- end strings

##-- paths
type RelPath = Annotated[pl.Path, lambda x: not x.is_absolute()]
""" A Relative Path. """
type AbsPath = Annotated[pl.Path, lambda x: x.is_absolute()]
""" A Path that is absolute. """

##-- end paths

##-- regex
type Rx       = Pattern
""" A re.Pattern. """
type RxMatch  = Match
""" A re.Match """

##-- end regex

##-- callables
type CtorFn[**I, O]          = Callable[I, O] | type[O]
""" A Callable that constructs a type. """
type Builder[**I, T]         = Callable[I, T]
type Func[**I, O]            = Callable[I, O]
""" A Callable. """
type Method[X:type, **I, O]  = Callable[Concatenate[X, I], O]
""" A Callable that is attached to an object. """
type Decorator[**I1, O1, **I2, O2]       = Func[[Func[I1, O1]], Func[I2, O2]]
""" A Function that decorates a callable. """
type Lambda[**I, O]          = Callable[I, O]
""" A lambda function. """

##-- end callables

##-- containers
type Weak[T]    = ref[T]
""" A Weak reference to a type. """
type Stack[T]   = list[T]
""" A Stack/FIFO. """
type Fifo[T]    = list[T]
""" A Stack/FIFO """
type Queue[T]   = deque[T]
""" A Queue/LIFO """
type Lifo[T]    = list[T]
""" A Queue/LIFO """
type Vector[T,S:int]  = Annotated[list[T], S]
""" A Sized collection of numbers? """

##-- end containers

##-- utils
type VList[T]                = T | list[T]
""" A Value, or a list of values """
type Mut[T]                  = Annotated[T, "Mutable"]
""" A Mutable Value """
type NoMut[T]                = Annotated[T, "Immutable"]
""" A Non-mutable value """

type Maybe[T]                = T | None
""" A Value or None. """
type MaybeT[*I]              = tuple[*I] | None
""" A Tuple of values or None. """
type Result[T, E:Exception]  = T | E
""" A Value, or an exception. """
type Either[L, R]            = L | R
""" One of two different values. """
type SubOf[T]                = TypeGuard[T]
""" A Typeguard for checking for a subtype of T. """

##-- end utils

##-- shorthands
type M_[T]                   = Maybe[T]
""" A Shorthand for Maybe[T] """
type R_[T, E:Exception]      = Result[T,E]
""" A Shorthand for Result[T, E] """
type E_[L, R]            = Either[L,R]
""" A Shorthand for Either[L, R] """

##-- end shorthands

##-- numbers
type Depth      = Annotated[int, lambda x: 0 <= x]
""" A Non-negative int for representing Depth """
type Seconds    = Annotated[int, lambda x: 0 <= x]
""" A Non-negative int for representing Seconds """
type DateTime   = datetime.datetime
""" An alias for datetime.datetime """
type TimeDelta  = datetime.timedelta
""" An alias for datetime.timedelta """

##-- end numbers

##-- dicts
type DictKeys   = KeysView
""" An Alias for the keys of a dict. """
type DictItems  = ItemsView
""" An Alias for the items of a dict. """
type DictVals   = ValuesView
""" An Alias for the values of a dict. """

##-- end dicts

##-- tracebacks and frames
type Traceback = types.TracebackType
""" An Error Traceback """
type Frame     = types.FrameType
""" A Runtime Frame """

##-- end tracebacks and frames

##-- misc
# the stdlib types.UnionType (int | float) is not typing.Union[int, float]
UnionTypes  : Final[types.UnionType]  = types.UnionType | type(Union[int,None])  # noqa: UP007
""" """
type Module                           = types.ModuleType
""" The type of a python module. """

type CHECKTYPE                        = Maybe[type|types.GenericAlias|types.UnionType]
""" """

##-- end misc
