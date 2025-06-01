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
from jgdv.mixins.enum_builders import EnumBuilder_m
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

if TYPE_CHECKING:
    from jgdv import Maybe, Rx, Ident, RxStr, Ctor, CHECKTYPE, FmtStr
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    from ._facade import DKey

    type KeyMark     = DKeyMarkAbstract_e|str|type
    type LookupList  = list[list[ExpInst_d]]
    type LitFalse    = Literal[False]
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
DEFAULT_COUNT        : Final[int]              = 0
FMT_PATTERN          : Final[Rx]               = re.compile("[wdi]+")
INDIRECT_SUFFIX      : Final[Ident]            = "_"
KEY_PATTERN          : Final[RxStr]            = "{(.+?)}"
OBRACE               : Final[str]              = "{"
MAX_DEPTH            : Final[int]              = 10
MAX_KEY_EXPANSIONS   : Final[int]              = 200
PAUSE_COUNT          : Final[int]              = 0
RECURSION_GUARD      : Final[int]              = 5
PARAM_IGNORES        : Final[tuple[str, str]]  = ("_", "_ex")

RAWKEY_ID            : Final[str]              = "_rawkeys"
FORCE_ID             : Final[str]              = "force"
ARGS_K               : Final[Ident]            = "args"
KWARGS_K             : Final[Ident]            = "kwargs"

DEFAULT_DKEY_KWARGS  : Final[list[str]]        = [
    "ctor", "check", "mark", "fallback",
    "max_exp", "fmt", "help", "implicit", "conv",
    "named",
    RAWKEY_ID, FORCE_ID,
    ]

##--| Error Messages
NestedFailure           : Final[str]  = "Nested ExpInst_d"
NoValueFailure          : Final[str]  = "ExpInst_d's must have a val"
UnexpectedData          : Final[str]  = "Unexpected kwargs given to ExpInst_d"
UnknownDKeyCtorType     : Final[str]  = "Unknown type passed to construct dkey"
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

class DKeyMark_e(EnumBuilder_m, DKeyMarkAbstract_e):
    """
      Enums for how to use/build a dkey

    """
    FREE     = "free"
    PATH     = enum.auto() # -> pl.Path
    INDIRECT = "indirect"
    STR      = enum.auto() # -> str
    CODE     = enum.auto() # -> coderef
    IDENT    = enum.auto() # -> taskname
    ARGS     = enum.auto() # -> list
    KWARGS   = enum.auto() # -> dict
    POSTBOX  = enum.auto() # -> list
    NULL     = enum.auto() # -> None
    MULTI    = enum.auto()

    @classmethod
    def default(cls) -> str:
        return cls.FREE

    @classmethod
    def null(cls) -> str:
        return cls.NULL

    @classmethod
    def multi(cls) -> str:
        return cls.MULTI

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

class ExpInst_d:
    """ The lightweight holder of expansion instructions, passed through the
    expander mixin.
    Uses slots to make it as lightweight as possible

    """
    __slots__ = ("convert", "fallback", "lift", "literal", "rec", "total_recs", "value")
    value       : Any
    convert     : Maybe[str|bool]
    fallback    : Maybe[str]
    lift        : bool
    literal     : bool
    rec         : int
    total_recs  : int

    def __init__(self, **kwargs) -> None:
        self.value       = kwargs.pop("value")
        self.convert     = kwargs.pop("convert", None)
        self.fallback    = kwargs.pop("fallback", None)
        self.lift        = kwargs.pop("lift", False)
        self.literal     = kwargs.pop("literal", False)
        self.rec         = kwargs.pop("rec", -1)
        self.total_recs  = kwargs.pop("total_recs", 1)

        match self.value:
            case ExpInst_d() as val:
                raise TypeError(NestedFailure, val)
            case None:
                 raise ValueError(NoValueFailure)
        if bool(kwargs):
            raise ValueError(UnexpectedData, kwargs)

    def __repr__(self) -> str:
        lit  = "(Lit)" if self.literal else ""
        return f"<ExpInst_d:{lit} {self.value!r} / {self.fallback!r} (R:{self.rec},L:{self.lift},C:{self.convert})>"

class DKey_d(StrangAPI.Strang_d):
    """ Data of a DKey """
    __slots__ = ("convert", "expansion_type", "fallback", "format", "help", "mark", "max_expansions", "multi", "name", "raw", "typecheck")
    name            : Maybe[str]
    raw             : tuple[RawKey_d, ...]
    mark            : KeyMark
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
        self.mark            = kwargs.pop("mark", DKeyMark_e.default())
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

class Expander_p(Protocol):

    def set_ctor(self, ctor:Ctor[Key_p]) -> None: ...

    def redirect(self, source:Key_p, *sources:dict, **kwargs:Any) -> list[Maybe[ExpInst_d]]:  ...  # noqa: ANN401

    def expand(self, source:Key_p, *sources:dict, **kwargs:Any) -> Maybe[ExpInst_d]:  ...  # noqa: ANN401

    def extra_sources(self, source:Key_p) -> list[Any]: ...

class ExpansionHooks_p(Protocol):

    def exp_extra_sources_h(self) -> Maybe[list]: ...

    def exp_pre_lookup_h(self, sources:list[dict], opts:dict) -> Maybe[LookupList]: ...

    def exp_pre_recurse_h(self, insts:list[ExpInst_d], sources:list[dict], opts:dict) -> Maybe[list[ExpInst_d]]: ...

    def exp_flatten_h(self, insts:list[ExpInst_d], opts:dict) -> Maybe[LitFalse|ExpInst_d]: ...

    def exp_coerce_h(self, inst:ExpInst_d, opts:dict) -> Maybe[ExpInst_d]: ...

    def exp_final_h(self, inst:ExpInst_d, opts:dict) -> Maybe[LitFalse|ExpInst_d]: ...

    def exp_check_result_h(self, inst:ExpInst_d, opts:dict) -> None: ...

class Expandable_p(Protocol):
    """ An expandable, like a DKey,
    uses these hooks to customise the expansion
    """

    def expand(self, *sources, **kwargs) -> Maybe: ...

@runtime_checkable
class Key_p(ExpansionHooks_p, StrangAPI.Strang_p, Protocol):
    """ The protocol for a Key, something that used in a template system"""
    _extra_kwargs  : ClassVar[set[str]]
    _processor     : ClassVar
    _expander      : ClassVar[Expander_p]
    # data           : DKey_d

    @staticmethod
    def MarkOf[T:Key_p](cls:type[T]|T) -> KeyMark|tuple[KeyMark, ...]: ...  # noqa: N802

    def keys(self) -> list[Key_p]: ...

    def redirect(self, spec=None) -> Key_p: ...

    def expand(self, *sources, rec=False, insist=False, chain:Maybe[list[Key_p]]=None, on_fail=Any, locs:Maybe[Mapping]=None, **kwargs) -> str: ...

    def var_name(self) -> str: ...

@runtime_checkable
class MultiKey_p(Protocol):

    def _multi(self) -> Literal[True]: ...


@runtime_checkable
class IndirectKey_p(Protocol):

    def _indirect(self) -> Literal[True]: ...
##--| Combined Interfaces
