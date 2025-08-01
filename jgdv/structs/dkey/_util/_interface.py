#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN002, ANN003
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

from jgdv._abstract.protocols.general import SpecStruct_p
from jgdv.structs.strang import Strang, CodeReference
from .._interface import Key_p, NonKey_p, MultiKey_p, IndirectKey_p, LIFT_EXPANSION_PATTERN

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
from collections.abc import Sequence
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import MutableMapping, Hashable

    from jgdv import Maybe, Rx, Ident, RxStr, CtorFn, CHECKTYPE, FmtStr
    type LitFalse               = Literal[False]
    type InstructionAlts        = list[ExpInst_d]
    type InstructionList        = list[InstructionAlts]
    type InstructionExpansions  = list[ExpInst_d]
    type ExpOpts                = dict
    type SourceBases            = list|Mapping|SpecStruct_p

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
NO_EXPANSIONS_PERMITTED    : Final[int]                 = 0

EXPANSION_CONVERT_MAPPING  : Final[dict[str,Maybe[Callable]]]  = {
    "p"                    : lambda x: pl.Path(x).expanduser().resolve(),
    "s"                    : str,
    "S"                    : Strang,
    "c"                    : CodeReference,
    "i"                    : int,
    "f"                    : float,
    LIFT_EXPANSION_PATTERN : None,
}
##--| Data

class ExpInst_d:
    """ The lightweight holder of expansion instructions, passed through the
    expander mixin.
    Uses slots to make it as lightweight as possible

    - fallback : the value to use if expansion fails
    - convert  : controls type coercion of expansion result
    - lift     : says to lift expanded values into keys themselves (using !L in the key str)
    - literal  : signals the value needs no more expansion
    - rec      : the remaining recursive expansions available. -1 is unrestrained.
    - total_recs : tracks the number of expansions have occured

    """
    __slots__ = ("convert", "fallback", "lift", "literal", "rec", "total_recs", "value")
    value       : Any
    convert     : Maybe[str|bool]
    fallback    : Maybe[str]
    lift        : bool | tuple[bool, bool]
    literal     : bool
    rec         : Maybe[int]
    total_recs  : int

    def __init__(self, **kwargs) -> None:
        self.value       = kwargs.pop("value")
        self.convert     = kwargs.pop("convert", None)
        self.fallback    = kwargs.pop("fallback", None)
        self.lift        = kwargs.pop("lift", False)
        self.literal     = kwargs.pop("literal", False)
        self.rec         = kwargs.pop("rec", None)
        self.total_recs  = kwargs.pop("total_recs", 0)

        assert(self.rec is None or self.rec >= 0)
        if self.rec == 0:
            self.literal = True
        self.process_value()
        if bool(kwargs):
            raise ValueError(UnexpectedData, kwargs)

    @override
    def __repr__(self) -> str:
        lit  = "(Lit)" if self.literal else ""
        return f"<ExpInst_d:{lit} {self.value!r} / {self.fallback!r} (R:{self.rec},L:{self.lift},C:{self.convert})>"

    def process_value(self) -> None:
        match self.value:
            case ExpInst_d() as val:
                raise TypeError(NestedFailure, val)
            case Key_p() as k if k.data.convert is not None and LIFT_EXPANSION_PATTERN in k.data.convert:
                self.lift = True
            case Key_p() | None:
                pass

class ExpInstChain_d:
    __slots__ = ("chain", "merge", "root")

    root   : Key_p
    chain  : tuple[ExpInst_d, ...]
    merge  : Maybe[int]

    def __init__(self, *chain:ExpInst_d, root:Key_p, merge:Maybe[int]=None) -> None:
        self.root   = root
        self.chain  = tuple(chain)
        self.merge  = merge

    def __getitem__(self, i:int) -> ExpInst_d:
        return self.chain[i]

    def __iter__(self) -> Iterator[ExpInst_d]:
        return iter(self.chain)

    def __len__(self) -> int:
        return self.merge or len(self.chain)

    @override
    def __repr__(self) -> str:
        if self.merge:
            val = f"(M:{self.merge})"
        else:
            val = f"(C:{len(self.chain)})"
        return f"<ExpChain{val}: {self.root}>"

class SourceChain_d:
    """ The core logic to lookup a key from a sequence of sources

    | Doesn't perform repeated expansions.
    | Tries sources in order.
    | A Source that is a list is copied and each retrieval pops a value off it

    TODO replace this with collections.ChainMap ?
    """
    __slots__ = ("sources",)
    sources  : list[Mapping|list]

    def __init__(self, *args:Maybe[SourceBases|SourceChain_d]) -> None:
        self.sources = []
        for base in args:
            match base:
                case None:
                    pass
                case SourceChain_d():
                    self.sources += base.sources
                case list():
                    self.sources.append(base[:])
                case dict() | collections.ChainMap():
                    self.sources.append(base)
                case Mapping():
                    self.sources.append(base)
                case SpecStruct_p():
                    self.sources.append(base.params)
                case x:
                    raise TypeError(type(x))

    @override
    def __repr__(self) -> str:
        source_types = ", ".join([type(x).__name__ for x in self.sources])
        return f"<{type(self).__name__}: {source_types}>"

    def extend(self, *args:SourceBases) -> SourceChain_d:
        extension = SourceChain_d(*self.sources, *args)
        return extension

    def lookup(self, target:ExpInstChain_d) -> Maybe[ExpInst_d|tuple]:
        """ Look up alternatives

        | pass through DKeys and (DKey, ..) for recursion
        | lift (str(), True, fallback)
        | don't lift (str(), False, fallback)

        """
        x            : Any
        for inst in target:
            match inst:
                case ExpInst_d(value=NonKey_p()) | ExpInst_d(literal=True):
                    return inst
                case ExpInst_d() as curr:
                    match self.get(str(curr.value)):
                        case None:
                            pass
                        case x:
                            return x, curr
                case x:
                    msg = "Unrecognized lookup spec"
                    raise TypeError(msg, x)
            ##--|
        else:
            return None

    def get(self, key:str, fallback:Maybe=None) -> Maybe:
        """ Get a key's value from an ordered sequence of potential sources.

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

##--| Protocols

@runtime_checkable
class InstructionFactory_p(Protocol):

    def build_chains(self, val:ExpInst_d, opts:ExpOpts) -> list[ExpInstChain_d|ExpInst_d]: ...

    def build_inst(self, val:Maybe, root:Maybe[ExpInst_d], opts:ExpOpts, *, decrement:bool=True) -> Maybe[ExpInst_d]: ...

    def null_inst(self) -> ExpInst_d: ...

    def literal_inst(self, val:Any) -> ExpInst_d: ...  # noqa: ANN401

class Expander_p[T](Protocol):

    def set_ctor(self, ctor:CtorFn[..., T]) -> None: ...

    def redirect(self, source:T, *sources:dict, **kwargs:Any) -> list[Maybe[ExpInst_d]]:  ...  # noqa: ANN401

    def expand(self, source:T, *sources:dict, **kwargs:Any) -> Maybe[ExpInst_d]:  ...  # noqa: ANN401

    def extra_sources(self, source:T) -> SourceChain_d: ...

    def coerce_result(self, inst:ExpInst_d, opts:ExpOpts, *, source:Key_p) -> Maybe[ExpInst_d]: ...

class ExpansionHooks_p(Protocol):

    def exp_to_inst_h(self, root:ExpInst_d, factory:InstructionFactory_p,  **kwargs) -> Maybe[ExpInst_d]: ...  # noqa: ANN401

    def exp_generate_chains_h(self, root:ExpInst_d, factory:InstructionFactory_p, opts:ExpOpts) -> list[ExpInstChain_d|ExpInst_d]: ...  # noqa: ANN401

    def exp_extra_sources_h(self, current:SourceChain_d) -> SourceChain_d: ...

    def exp_flatten_h(self, values:list[Maybe[ExpInst_d]], factory:InstructionFactory_p, opts:dict) -> Maybe[ExpInst_d]: ...

    def exp_coerce_h(self, inst:ExpInst_d, factory:InstructionFactory_p, opts:dict) -> Maybe[ExpInst_d]: ...

    def exp_final_h(self, inst:ExpInst_d, root:Maybe[ExpInst_d], factory:InstructionFactory_p, opts:dict) -> Maybe[ExpInst_d]: ...

    def exp_check_result_h(self, inst:Maybe[ExpInst_d], opts:dict) -> None: ...

class Expandable_p(Protocol):
    """ An expandable, like a DKey,
    uses these hooks to customise the expansion
    """

    def expand(self, *sources, **kwargs) -> Maybe: ...
