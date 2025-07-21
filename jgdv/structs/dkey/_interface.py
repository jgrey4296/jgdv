#!/usr/bin/env python3
"""

"""
# ruff: noqa: N801, ANN001, ANN002, ANN003
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

from jgdv import identity_fn
from jgdv.structs.strang import _interface as StrangAPI # noqa: N812

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from collections.abc import Mapping

if TYPE_CHECKING:
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, MutableMapping, Hashable

    from jgdv import Maybe, Rx, Ident, RxStr, Ctor, CHECKTYPE, FmtStr
    from ._util._interface import Expander_p, ExpInst_d

    type LitFalse    = Literal[False]
    type KeyMark     = DKeyMarkAbstract_e|LitFalse|str|type|tuple[KeyMark, ...]
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
DEFAULT_COUNT            : Final[int]              = 0
LIFT_EXPANSION_PATTERN   : Final[str]              = "L"
FMT_PATTERN              : Final[Rx]               = re.compile(r"[wdi]+")
EXPANSION_LIMIT_PATTERN  : Final[Rx]               = re.compile(r"e(\d+)")
INDIRECT_SUFFIX          : Final[Ident]            = "_"
KEY_PATTERN              : Final[RxStr]            = "{(.+?)}"
OBRACE                   : Final[str]              = "{"
MAX_DEPTH                : Final[int]              = 10
MAX_KEY_EXPANSIONS       : Final[int]              = 200
PAUSE_COUNT              : Final[int]              = 0
RECURSION_GUARD          : Final[int]              = 10
PARAM_IGNORES            : Final[tuple[str, str]]  = ("_", "_ex")

RAWKEY_ID                : Final[str]              = "_rawkeys"
FORCE_ID                 : Final[str]              = "force"
ARGS_K                   : Final[Ident]            = "args"
KWARGS_K                 : Final[Ident]            = "kwargs"

DEFAULT_DKEY_KWARGS      : Final[list[str]]        = [
    "ctor", "check", "mark", "fallback",
    "max_exp", "fmt", "help", "implicit", "conv",
    "named",
    RAWKEY_ID, FORCE_ID,
    ]

##--| Error Messages
UnknownDKeyCtorType      : Final[str]              = "Unknown type passed to construct dkey"
InsistentKeyFailure     : Final[str]  = "An insistent key was not built"
KeyBuildFailure         : Final[str]  = "No key was built"
NoMark                  : Final[str]  = "Mark has to be a value"
MarkConflictsWithMulti  : Final[str]  = "Mark is MULTI but multi=False"
MarkLacksACtor          : Final[str]  = "Couldn't find a ctor for mark"
MarkConversionConflict  : Final[str]  = "Kwd Mark/Conversion Conflict"
UnexpectedKwargs        : Final[str]  = "Key got unexpected kwargs"
RegistryLacksMark       : Final[str]  = "Can't register when the mark is None"
RegistryConflict        : Final[str]  = "API.Key_p Registry conflict"
ConvParamTooLong        : Final[str]  = "Conversion Parameters For Dkey's Can't Be More Than A Single Char"
ConvParamConflict       : Final[str]  = "Conversion Param Conflict"
# Enums:

class DKeyMarkAbstract_e(StrangAPI.StrangMarkAbstract_e):

    @classmethod
    def default(cls) -> Maybe: ...

    @classmethod
    def null(cls) -> Maybe: ...

    @classmethod
    def multi(cls) -> Maybe: ...

class DKeyMark_e(DKeyMarkAbstract_e):
    """
      Enums for how to use/build a dkey

    """
    ARGS     = enum.auto() # -> list
    KWARGS   = enum.auto() # -> dict
    POSTBOX  = enum.auto() # -> list

    @classmethod
    def default(cls) -> Any:  # noqa: ANN401
        return Any

    @classmethod
    def null(cls) -> Maybe:
        return False

    @classmethod
    def indirect(cls) -> type:
        return Mapping

    @classmethod
    def multi(cls) -> type:
        return list

##--| Data

class RawKey_d:
    """ Utility class for parsed {}-format string parameters.

    ::

        see: https://peps.python.org/pep-3101/
        and: https://docs.python.org/3/library/string.html#format-string-syntax

    Provides the data from string.Formatter.parse, but in a structure
    instead of a tuple.
    """
    __slots__ = ("convert", "format", "key", "prefix")
    prefix  : str
    key     : Maybe[str]
    format  : Maybe[str]
    convert : Maybe[str]

    def __init__(self, **kwargs) -> None:
        self.prefix       = kwargs.pop("prefix")
        self.key          = kwargs.pop("key", None)
        self.format       = kwargs.pop("format", None)
        self.convert      = kwargs.pop("convert", None)
        assert(not bool(kwargs)), kwargs

    def __getitem__(self, i) -> Maybe[str]:
        match i:
            case 0:
                return self.prefix
            case 1:
                return self.key
            case 2:
                return self.format
            case 3:
                return self.convert
            case _:
                msg = "Tried to access a bad element of DKeyParams"
                raise ValueError(msg, i)

    def __bool__(self) -> bool:
        return bool(self.key)

    def __repr__(self) -> str:
        return f"<RawkKey: {self.joined()}>"

    def joined(self) -> str:
        """ Returns the key and params as one string

        eg: blah, fmt=5, conv=p -> blah:5!p
        """
        args : list[str]
        if not bool(self.key):
            return ""

        assert(self.key is not None)
        args = [self.key]
        if bool(self.format):
            assert(self.format is not None)
            args += [":", self.format]
        if bool(self.convert):
            assert(self.convert is not None)
            args += ["!", self.convert]

        return "".join(args)

    def wrapped(self) -> str:
        """ Returns this key in simple wrapped form

        (it ignores format, conv params and prefix)

        eg: blah -> {blah}
        """
        return "{%s}" % self.key  # noqa: UP031

    def anon(self) -> str:
        """ Make a format str of this key, with anon variables.

        eg: blah {key:f!p} -> blah {}
        """
        if bool(self.key):
            return "%s{}" % self.prefix  # noqa: UP031

        return self.prefix or ""

    def direct(self) -> str:
        """ Returns this key in direct form

        ::

            eg: blah -> blah
                blah_ -> blah
        """
        return (self.key or "").removesuffix(INDIRECT_SUFFIX)

    def indirect(self) -> str:
        """ Returns this key in indirect form

        ::

            eg: blah -> blah_
                blah_ -> blah_
        """
        match self.key:
            case str() as k if k.endswith(INDIRECT_SUFFIX):
                return k
            case str() as k:
                return f"{k}{INDIRECT_SUFFIX}"
            case _:
                return ""

    def is_indirect(self) -> bool:
        match self.key:
            case str() as k if k.endswith(INDIRECT_SUFFIX):
                return True
            case _:
                return False

class DKey_d(StrangAPI.Strang_d):
    """ Data of a DKey """
    __slots__ = ("convert", "expansion_type", "fallback", "format", "help", "max_expansions", "multi", "name", "raw", "typecheck")
    name            : Maybe[str]
    raw             : tuple[RawKey_d, ...]
    expansion_type  : Ctor
    typecheck       : CHECKTYPE
    fallback        : Maybe[Any]
    format          : Maybe[FmtStr]
    convert         : Maybe[FmtStr]
    help            : Maybe[str]
    max_expansions  : Maybe[int]
    multi           : bool

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.name            = kwargs.pop("name", None)
        self.raw             = tuple(kwargs.pop(RAWKEY_ID, ()))
        self.expansion_type  = kwargs.pop("ctor", identity_fn)
        self.typecheck       = kwargs.pop("check", Any)
        self.fallback        = kwargs.pop("fallback", None)
        self.format          = kwargs.pop("format", None)
        self.convert         = kwargs.pop("convert", None)
        self.help            = kwargs.pop("help", None)
        self.max_expansions  = kwargs.pop("max_exp", None)
        self.multi           = kwargs.pop("multi", False)

##--| Section Specs
DKEY_SECTIONS : Final[StrangAPI.Sections_d] = StrangAPI.Sections_d(
    StrangAPI.Sec_d("body", None, None, str, None, True),  # noqa: FBT003
)
##--| Protocols

@runtime_checkable
class Key_p(StrangAPI.Strang_p, Protocol):
    """ The protocol for a Key, something that used in a template system"""
    _extra_kwargs  : ClassVar[set[str]]
    _processor     : ClassVar
    _expander      : ClassVar[Expander_p]
    data           : DKey_d

    @staticmethod
    def MarkOf[T:Key_p](cls:type[T]|T) -> KeyMark: ...  # noqa: N802, PLW0211

    def redirect(self, spec=None) -> Key_p: ...

    def expand(self, *sources, rec=False, insist=False, chain:Maybe[list[Key_p]]=None, on_fail=Any, locs:Maybe[Mapping]=None, **kwargs) -> str: ...

    def var_name(self) -> str: ...

@runtime_checkable
class MultiKey_p(Protocol):

    def keys(self) -> list[Key_p]: ...

    def _multi(self) -> Literal[True]: ...

@runtime_checkable
class IndirectKey_p(Protocol):

    def _indirect(self) -> Literal[True]: ...
##--| Combined Interfaces

@runtime_checkable
class NonKey_p(Protocol):

    def _nonkey(self) -> Literal[True]: ...
