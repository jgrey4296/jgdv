#!/usr/bin/env python3
"""

"""
# ruff: noqa: N801

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

from jgdv.mixins.enum_builders import EnumBuilder_m

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
    from jgdv import Maybe, Rx, Ident, RxStr
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    from ._meta import DKey

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
DEFAULT_COUNT       : Final[int]       = 0
FMT_PATTERN         : Final[Rx]        = re.compile("[wdi]+")
INDIRECT_SUFFIX     : Final[Ident]     = "_"
KEY_PATTERN         : Final[RxStr]     = "{(.+?)}"
MAX_DEPTH           : Final[int]       = 10
MAX_KEY_EXPANSIONS  : Final[int]       = 200
PAUSE_COUNT         : Final[int]       = 0
RECURSION_GUARD     : Final[int]       = 5
PARAM_IGNORES       : Final[list[str]] = ["_", "_ex"]

RAWKEY_ID           : Final[str]       = "_rawkeys"
FORCE_ID            : Final[str]       = "force"
ARGS_K              : Final[Ident]     = "args"
KWARGS_K            : Final[Ident]     = "kwargs"

DEFAULT_DKEY_KWARGS : Final[list[str]] = [
    "ctor", "check", "mark", "fallback",
    "max_exp", "fmt", "help", "implicit", "conv",
    "named",
    RAWKEY_ID, FORCE_ID,
    ]
# Body:

class DKeyMark_e(EnumBuilder_m, enum.StrEnum):
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

    default  = FREE
##--|

@runtime_checkable
class Key_p(Protocol):
    """ The protocol for a Key, something that used in a template system"""

    @property
    def multi(self) -> bool: ...

    def keys(self) -> list[Key_p]: ...

    def redirect(self, spec=None) -> Key_p: ...

    def expand(self, spec=None, state=None, *, rec=False, insist=False, chain:Maybe[list[Key_p]]=None, on_fail=Any, locs:Maybe[Mapping]=None, **kwargs) -> str: ...  # noqa: ANN003

@runtime_checkable
class Expandable_p(Protocol):
    """ An expandable, like a DKey,
    uses these hooks to customise the expansion
    """
    type LookupList = list[list[ExpInst_d]]
    type LitFalse   = Literal[False]

    def expand(self, *args, **kwargs) -> Maybe:
        pass

    def exp_extra_sources_h(self) -> Maybe[list]:
        pass

    def exp_pre_lookup_h(self, sources, opts) -> Maybe[LookupList]:
        pass

    def exp_pre_recurse_h(self, vals:list[ExpInst_d], sources, opts) -> Maybe[list[ExpInst_d]]:
        pass

    def exp_flatten_h(self, vals:list[ExpInst_d], opts) -> Maybe[LitFalse|ExpInst_d]:
        pass

    def exp_coerce_h(self, val:ExpInst_d, opts) -> Maybe[ExpInst_d]:
        pass
    def exp_final_h(self, val:ExpInst_d, opts) -> Maybe[LitFalse|ExpInst_d]:
        pass

    def exp_check_result_h(self, val:ExpInst_d, opts) -> None:
        pass

##--|

class ExpInst_d:
    """ The lightweight holder of expansion instructions, passed through the
    expander mixin.
    Uses slots to make it as lightweight as possible

    """
    __slots__ = "convert", "fallback", "lift", "literal", "rec", "total_recs", "val"

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        match kwargs:
            case {"val": ExpInst_d() as val }:
                msg = "Nested ExpInst_d"
                raise TypeError(msg, val)
            case {"val": val}:
                self.val        = val
            case x:
                 msg = "ExpInst_d's must have a val"
                 raise ValueError(msg, x)

        if bool((extra:=kwargs.keys() - ExpInst_d.__slots__)):
            msg = "Unexpected kwargs given to ExpInst_d"
            raise ValueError(msg, extra)

        self.convert    = kwargs.get("convert", None)
        self.fallback   = kwargs.get("fallback", None)
        self.lift       = kwargs.get("lift", False)
        self.literal    = kwargs.get("literal", False)
        self.rec        = kwargs.get("rec", -1)
        self.total_recs = kwargs.get("total_recs", 1)

    def __repr__(self) -> str:
        lit = "(Lit)" if self.literal else ""
        return f"<ExpInst_d:{lit} {self.val!r} / {self.fallback!r} (R:{self.rec},L:{self.lift},C:{self.convert})>"
