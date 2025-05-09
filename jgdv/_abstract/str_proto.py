#!/usr/bin/env python3
"""
Adapated from typeshed

"""
# ruff: noqa
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
    from collections.abc import Mapping, MutableMapping, Hashable

##--|

type ReadableBuffer    = Any
type SupportsIndex     = Any
type _FormatMapMapping = Any
type _TranslateTable   = Any
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class String_p(Protocol):

    @staticmethod
    def maketrans[_T](x: dict[int, _T] | dict[str, _T] | dict[str | int, _T], /) -> dict[int, _T]: ...
    @staticmethod
    def maketrans(x: str, y: str, /) -> dict[int, int]: ...
    @staticmethod
    def maketrans(x: str, y: str, z: str, /) -> dict[int, int | None]: ...

    def __new__(cls, object: ReadableBuffer, encoding: str = ..., errors: str = ...) -> Self: ...
    def capitalize(self) -> str: ...
    def casefold(self) -> str: ...  # type: ignore[misc]
    def center(self, width: SupportsIndex, fillchar: str = " ", /) -> str: ...  # type: ignore[misc]
    def count(self, sub: str, start: SupportsIndex | None = ..., end: SupportsIndex | None = ..., /) -> int: ...
    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes: ...
    def endswith(self, suffix: str | tuple[str, ...], start: SupportsIndex | None = ..., end: SupportsIndex | None = ..., ) -> bool: ...
    def expandtabs(self, tabsize: SupportsIndex = 8) -> str: ...  # type: ignore[misc]
    def find(self, sub: str, start: SupportsIndex | None = ..., end: SupportsIndex | None = ..., /) -> int: ...
    def format(self, *args: object, **kwargs: object) -> str: ...
    def format_map(self, mapping: _FormatMapMapping, /) -> str: ...
    def index(self, sub: str, start: SupportsIndex | None = ..., end: SupportsIndex | None = ..., /) -> int: ...
    def isalnum(self) -> bool: ...
    def isalpha(self) -> bool: ...
    def isascii(self) -> bool: ...
    def isdecimal(self) -> bool: ...
    def isdigit(self) -> bool: ...
    def isidentifier(self) -> bool: ...
    def islower(self) -> bool: ...
    def isnumeric(self) -> bool: ...
    def isprintable(self) -> bool: ...
    def isspace(self) -> bool: ...
    def istitle(self) -> bool: ...
    def isupper(self) -> bool: ...
    def join(self, iterable: Iterable[str], /) -> str: ...  # type: ignore[misc]
    def ljust(self, width: SupportsIndex, fillchar: str = " ", /) -> str: ...  # type: ignore[misc]
    def lower(self) -> str: ...  # type: ignore[misc]
    def lstrip(self, chars: str | None = None, /) -> str: ...  # type: ignore[misc]
    def partition(self, sep: str, /) -> tuple[str, str, str]: ...  # type: ignore[misc]
    def replace(self: LiteralString, old: LiteralString, new: LiteralString, /, count: SupportsIndex = -1) -> LiteralString: ...
    def removeprefix(self, prefix: str, /) -> str: ...  # type: ignore[misc]
    def removesuffix(self, suffix: str, /) -> str: ...  # type: ignore[misc]
    def rfind(self, sub: str, start: SupportsIndex | None = ..., end: SupportsIndex | None = ..., /) -> int: ...
    def rindex(self, sub: str, start: SupportsIndex | None = ..., end: SupportsIndex | None = ..., /) -> int: ...
    def rjust(self, width: SupportsIndex, fillchar: str = " ", /) -> str: ...  # type: ignore[misc]
    def rpartition(self, sep: str, /) -> tuple[str, str, str]: ...  # type: ignore[misc]
    def rsplit(self, sep: str | None = None, maxsplit: SupportsIndex = -1) -> list[str]: ...  # type: ignore[misc]
    def rstrip(self, chars: str | None = None, /) -> str: ...  # type: ignore[misc]
    def split(self, sep: str | None = None, maxsplit: SupportsIndex = -1) -> list[str]: ...  # type: ignore[misc]
    def splitlines(self, keepends: bool = False) -> list[str]: ...  # type: ignore[misc]  # noqa: FBT001, FBT002
    def startswith(self, prefix: str | tuple[str, ...], start: SupportsIndex | None = ..., end: SupportsIndex | None = ..., /) -> bool: ...
    def strip(self, chars: str | None = None, /) -> str: ...  # type: ignore[misc]
    def swapcase(self) -> str: ...  # type: ignore[misc]
    def title(self) -> str: ...  # type: ignore[misc]
    def translate(self, table: _TranslateTable, /) -> str: ...
    def upper(self) -> str: ...  # type: ignore[misc]
    def zfill(self, width: SupportsIndex, /) -> str: ...  # type: ignore[misc]
    def __add__(self: LiteralString, value: LiteralString, /) -> LiteralString: ...
    def __add__(self, value: str, /) -> str: ...  # type: ignore[misc]
    # Incompatible with Sequence.__contains__
    def __contains__(self, key: str, /) -> bool: ...  # type: ignore[override]
    def __eq__(self, value: object, /) -> bool: ...
    def __ge__(self, value: str, /) -> bool: ...
    def __getitem__(self: LiteralString, key: SupportsIndex | slice, /) -> LiteralString: ...
    def __getitem__(self, key: SupportsIndex | slice, /) -> str: ...  # type: ignore[misc]
    def __gt__(self, value: str, /) -> bool: ...
    def __hash__(self) -> int: ...
    def __iter__(self) -> Iterator[str]: ...  # type: ignore[misc]
    def __le__(self, value: str, /) -> bool: ...
    def __len__(self) -> int: ...
    def __lt__(self, value: str, /) -> bool: ...
    def __mod__(self, value: Any, /) -> str: ...
    def __mul__(self, value: SupportsIndex, /) -> str: ...  # type: ignore[misc]
    def __ne__(self, value: object, /) -> bool: ...
    def __rmul__(self, value: SupportsIndex, /) -> str: ...  # type: ignore[misc]
    def __getnewargs__(self) -> tuple[str]: ...
