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

from jgdv._abstract.protocols import SpecStruct_p
from jgdv.structs.strang import Strang, CodeReference
from .._interface import Key_p, NonKey_p

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
from collections.abc import Mapping
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, MutableMapping, Hashable

    from jgdv import Maybe, Rx, Ident, RxStr, Ctor, CHECKTYPE, FmtStr
    type LitFalse    = Literal[False]
    type InstructionList  = list[ExpInst_d]
    type InstructionAlts  = list[InstructionList]
    type ExpOpts          = dict
    type SourceBases      = list|Mapping

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

##--| Values
UNRESTRICTED_EXPANSION     : Final[int]                 = -1
NO_EXPANSIONS_PERMITTED    : Final[int]                 = 0

EXPANSION_CONVERT_MAPPING  : Final[dict[str,Callable]]  = {
    "p"                    : lambda x: pl.Path(x).expanduser().resolve(),
    "s"                    : str,
    "S"                    : Strang,
    "c"                    : CodeReference,
    "i"                    : int,
    "f"                    : float,
}
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
    - total_recs : tracks the number of expansions have occured

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
        self.rec         = kwargs.pop("rec", None) or UNRESTRICTED_EXPANSION
        self.total_recs  = kwargs.pop("total_recs", 0)

        self.process_value()
        if bool(kwargs):
            raise ValueError(UnexpectedData, kwargs)

    def __repr__(self) -> str:
        lit  = "(Lit)" if self.literal else ""
        return f"<ExpInst_d:{lit} {self.value!r} / {self.fallback!r} (R:{self.rec},L:{self.lift},C:{self.convert})>"

    def process_value(self) -> None:
        match self.value:
            case ExpInst_d() as val:
                raise TypeError(NestedFailure, val)
            case None:
                 raise ValueError(NoValueFailure)
            case Key_p():
                pass

class SourceChain_d:
    """ The core logic to lookup a key from a sequence of sources

    | Doesn't perform repeated expansions.
    | Tries sources in order.

    TODO replace this with collections.ChainMap ?
    """
    __slots__ = ("lifter", "sources")
    sources  : list[Mapping]
    lifter   : type[Key_p]

    def __init__(self, *args:Maybe[SourceBases|SourceChain_d], lifter=type[Key_p]) -> None:
        self.sources = []
        for base in args:
            match base:
                case None:
                    pass
                case SourceChain_d():
                    self.sources += base.sources
                case dict() | collections.ChainMap():
                    self.sources.append(base)
                case Mapping():
                    self.sources.append(base)
                case x:
                    raise TypeError(type(x))
        self.lifter   = lifter

    def extend(self, *args:Mapping) -> Self:
        self.sources += [x for x in args if x not in self.sources]
        return self

    def get(self, key:str, fallback:Maybe=None) -> Maybe:
        """ Get a key's value from an ordered sequence of potential sources.

        | Try to get {key} then {key\\_} in order of sources passed in.
        """
        replacement  : Maybe  = fallback
        for lookup in self.sources:
            match lookup:
                case None | []:
                    continue
                case list():
                    replacement = lookup.pop()
                case _ if hasattr(lookup, "get"):
                    if key not in lookup:
                        continue
                    replacement = lookup.get(key, fallback)
                case SpecStruct_p():
                    params      = lookup.params
                    replacement = params.get(key, fallback)
                case _:
                    msg = "Unknown Type in get"
                    raise TypeError(msg, key, lookup)

            if replacement is not fallback:
                return replacement
        else:
            return fallback



    def lookup(self, target:list[ExpInst_d]) -> Maybe[ExpInst_d]:
        """ Look up alternatives

        | pass through DKeys and (DKey, ..) for recursion
        | lift (str(), True, fallback)
        | don't lift (str(), False, fallback)

        """
        x : Any
        for spec in target:
            match spec:
                case ExpInst_d(value=Key_p()):
                    return spec
                case ExpInst_d(literal=True):
                    return spec
                case ExpInst_d(value=str() as key, lift=lift, fallback=fallback):
                    pass
                case x:
                    msg = "Unrecognized lookup spec"
                    raise TypeError(msg, x)

            match self.get(key):
                case None:
                    pass
                case x if lift:
                    logging.debug("Lifting Result to Key: %r", x)
                    match self.lifter(x, implicit=True, fallback=fallback): # type: ignore[call-arg]
                        case NonKey_p() as y:
                            return ExpInst_d(value=y, rec=0, litreal=True)
                        case Key_p() as y:
                            return ExpInst_d(value=y, fallback=fallback, lift=False)
                        case x:
                            raise TypeError(type(x))
                case x:
                    return ExpInst_d(value=x, fallback=fallback)
        else:
            return None
##--| Protocols

class Expander_p[T](Protocol):

    def set_ctor(self, ctor:Ctor[T]) -> None: ...

    def redirect(self, source:T, *sources:dict, **kwargs:Any) -> list[Maybe[ExpInst_d]]:  ...  # noqa: ANN401

    def expand(self, source:T, *sources:dict, **kwargs:Any) -> Maybe[ExpInst_d]:  ...  # noqa: ANN401

    def extra_sources(self, source:T) -> SourceChain_d: ...

class ExpansionHooks_p(Protocol):

    def exp_extra_sources_h(self, current:SourceChain_d) -> SourceChain_d: ...

    def exp_generate_alternatives_h(self, sources:SourceChain_d, opts:ExpOpts) -> InstructionAlts: ...

    def exp_configure_recursion_h(self, insts:InstructionAlts, sources:SourceChain_d, opts:ExpOpts) -> Maybe[InstructionList]: ...

    def exp_flatten_h(self, insts:InstructionList, opts:dict) -> Maybe[ExpInst_d]: ...

    def exp_coerce_h(self, inst:ExpInst_d, opts:dict) -> Maybe[ExpInst_d]: ...

    def exp_final_h(self, inst:ExpInst_d, opts:dict) -> Maybe[LitFalse|ExpInst_d]: ...

    def exp_check_result_h(self, inst:ExpInst_d, opts:dict) -> None: ...

class Expandable_p(Protocol):
    """ An expandable, like a DKey,
    uses these hooks to customise the expansion
    """

    def expand(self, *sources, **kwargs) -> Maybe: ...
