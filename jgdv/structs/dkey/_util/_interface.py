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
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Rx, Ident, RxStr, Ctor, CHECKTYPE, FmtStr
    type LookupList  = list[list[ExpInst_d]]
    type LitFalse    = Literal[False]

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

##--| Error Messages
NestedFailure           : Final[str]  = "Nested ExpInst_d"
NoValueFailure          : Final[str]  = "ExpInst_d's must have a val"
UnexpectedData          : Final[str]  = "Unexpected kwargs given to ExpInst_d"
##--| Data

class ExpInst_d:
    """ The lightweight holder of expansion instructions, passed through the
    expander mixin.
    Uses slots to make it as lightweight as possible

    - fallback : the value to use if expansion fails
    - convert  : controls type coercion of expansion result
    - lift     : says to lift expanded values into keys themselves
    - literal  : signals the value needs no more expansion
    - rec      : the remaining recursive expansions available. -1 is unrestrained.

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

##--| Protocols

class Expander_p[T](Protocol):

    def set_ctor(self, ctor:Ctor[T]) -> None: ...

    def redirect(self, source:T, *sources:dict, **kwargs:Any) -> list[Maybe[ExpInst_d]]:  ...  # noqa: ANN401

    def expand(self, source:T, *sources:dict, **kwargs:Any) -> Maybe[ExpInst_d]:  ...  # noqa: ANN401

    def extra_sources(self, source:T) -> list[Any]: ...

class ExpansionHooks_p(Protocol):

    def exp_extra_sources_h(self) -> Maybe[list]: ...

    def exp_pre_lookup_h(self, sources:list[dict], opts:dict) -> LookupList: ...

    def exp_pre_recurse_h(self, insts:list[ExpInst_d], sources:list[dict], opts:dict) -> Maybe[list[ExpInst_d]]: ...

    def exp_flatten_h(self, insts:list[ExpInst_d], opts:dict) -> Maybe[ExpInst_d]: ...

    def exp_coerce_h(self, inst:ExpInst_d, opts:dict) -> Maybe[ExpInst_d]: ...

    def exp_final_h(self, inst:ExpInst_d, opts:dict) -> Maybe[LitFalse|ExpInst_d]: ...

    def exp_check_result_h(self, inst:ExpInst_d, opts:dict) -> None: ...

class Expandable_p(Protocol):
    """ An expandable, like a DKey,
    uses these hooks to customise the expansion
    """

    def expand(self, *sources, **kwargs) -> Maybe: ...
