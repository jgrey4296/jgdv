#/usr/bin/env python3
"""
AST representations bridging parsed instal -> compiled clingo
"""
##-- imports
from __future__ import annotations

import logging as logmod
import pathlib as pl
from os import getcwd
from enum import Enum, auto
from dataclasses import InitVar, dataclass, field
import re
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref
##-- end imports

__all__ = [
    "EventEnum", "FluentEnum", "RuleEnum", "InstalAST",
    "TermAST", "InstitutionDefAST",
    "BridgeDefAST", "DomainSpecAST", "QueryAST", "InitiallyAST",
    "EventAST", "FluentAST", "ConditionAST",
    "RuleAST", "GenerationRuleAST", "InertialRuleAST",
    "TransientRuleAST", "BridgeLinkAST"
]
logging = logmod.getLogger(__name__)


VAR_SIG_REG = re.compile(r"\d+$")

##-- enums
class EventEnum(Enum):
    exogenous     = auto()
    institutional = auto()
    violation     = auto()

class FluentEnum(Enum):
    inertial               = auto()
    transient              = auto()
    cross                  = auto()
    obligation             = auto()
    achievement_obligation = auto()
    maintenance_obligation = auto()

class RuleEnum(Enum):
    # Event:
    generates   = auto()
    xgenerates  = auto()
    # Inertial:
    initiates   = auto()
    terminates  = auto()
    xinitiates  = auto()
    xterminates = auto()
    # Transient:
    transient   = auto()

class BridgeLinkEnum(Enum):
    source = auto()
    sink   = auto()

##-- end enums

##-- util context manager
class ASTContextManager:
    """ For ensuring all ASTs are built with the correct source """

    def __init__(self, parse_source):
        self.parse_source = parse_source

    def __enter__(self):
        InstalAST.current_parse_source = self.parse_source

    def __exit__(self, exc_type, exc_value, exc_traceback):
        InstalAST.current_parse_source = None


##-- end util context manager

##-- core base asts
@dataclass(frozen=True)
class InstalAST:
    parse_source : list[str|pl.Path]    = field(default_factory=list, kw_only=True, repr=False)
    parse_loc    : None|tuple[int, int] = field(default=None, kw_only=True)

    current_parse_source : ClassVar[None|str] = None

    def __post_init__(self):
        if InstalAST.current_parse_source is not None:
            self.parse_source.append(InstalAST.current_parse_source)

    @property
    def sources_str(self):
        if not bool(self.parse_source):
            return "n/a"

        full_path = self.parse_source[0]
        cwd       = getcwd()
        match full_path:
            case pl.Path():
                return str(full_path.relative_to(cwd))
            case str():
                return full_path
            case _:
                raise TypeError("An AST has an unexpected pasrse source", full_path)


    @staticmethod
    def manage_source(parse_source):
        return ASTContextManager(parse_source)


@dataclass(frozen=True)
class TermAST(InstalAST):
    value  : str             = field()
    params : list[TermAST]   = field(default_factory=list)
    is_var : bool            = field(default=False)

    def __post_init__(self):
        assert(not (self.is_var and bool(self.params)))
        super().__post_init__()

    def __str__(self):
        if bool(self.params):
            param_str = ",".join(str(x) for x in self.params)
            return self.value + "(" + param_str + ")"

        return str(self.value)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, TermAST):
            return False

        if not self.value == other.value:
            return False

        return all(x == y for x,y in zip(self.params, other.params))



    @property
    def signature(self):
        if not self.is_var:
            return f"{self.value}/{len(self.params)}"

        chopped = VAR_SIG_REG.sub("", self.value)
        return f"{chopped}/{len(self.params)}"

    @property
    def has_var(self) -> bool:
        return self.is_var or any(x.has_var for x in self.params)

##-- end core base asts

##-- institutions and bridges
@dataclass(frozen=True)
class InstitutionDefAST(InstalAST):
    head            : TermAST                = field()
    fluents         : list[FluentAST]        = field(default_factory=list)
    events          : list[EventAST]         = field(default_factory=list)
    types           : list[DomainSpecAST]    = field(default_factory=list)
    rules           : list[RuleAST]          = field(default_factory=list)
    initial         : list[InitiallyAST]     = field(default_factory=list)

@dataclass(frozen=True)
class BridgeDefAST(InstitutionDefAST):
    links : list[BridgeLinkAST] = field(default_factory=list)

##-- end institutions and bridges

##-- components
@dataclass(frozen=True)
class DomainSpecAST(InstalAST):
    """
    Type : instance, instance, instance;
    """
    head  : TermAST       = field()
    body  : list[TermAST] = field(default_factory=list)

@dataclass(frozen=True)
class QueryAST(InstalAST):
    head       : TermAST            = field()
    time       : None|int           = field(default=None)
    negated    : bool               = field(default=False)
    conditions : list[ConditionAST] = field(default_factory=list)

@dataclass(frozen=True)
class InitiallyAST(InstalAST):
    body       : list[TermAST]      = field(default_factory=list)
    conditions : list[ConditionAST] = field(default_factory=list)
    inst       : None|TermAST       = field(default=None)
    negated    : bool               = field(default=False)

@dataclass(frozen=True)
class EventAST(InstalAST):
    head       : TermAST   = field()
    annotation : EventEnum = field()

@dataclass(frozen=True)
class FluentAST(InstalAST):
    head       : TermAST    = field()
    annotation : FluentEnum = field(default=FluentEnum.inertial)

@dataclass(frozen=True)
class BridgeLinkAST(InstalAST):
    head     : TermAST        = field()
    link_type : BridgeLinkEnum = field()

##-- end components

##-- Rules
@dataclass(frozen=True)
class RuleAST(InstalAST):
    """
    rule of the form:
    if [head] and [conditions] then [body]
    or in datalog style:
    body <- head, conditions.
    """
    head       : None| TermAST      = field()
    body       : list[TermAST]      = field(default_factory=list)
    conditions : list[ConditionAST] = field(default_factory=list)
    delay      : int                = field(default=0)
    annotation : RuleEnum           = field(kw_only=True)

@dataclass(frozen=True)
class GenerationRuleAST(RuleAST):
    """
    event generation rule
    {head} generates {body} if {conditions}
    """
    pass

@dataclass(frozen=True)
class InertialRuleAST(RuleAST):
    """
    inertial fluent change rules
    {head} initiates/terminates {body} if {conditions}
    """
    pass

@dataclass(frozen=True)
class TransientRuleAST(RuleAST):
    """
    transient fluent consequence rules
    of the form:
    [transientFluent] when [conditions]
    """
    pass

@dataclass(frozen=True)
class ConditionAST(InstalAST):
    """
    Conditional expressions for rules
    """
    head     : TermAST      = field()
    negated  : bool         = field(default=False)
    operator : None|str     = field(default=None)
    rhs      : None|TermAST = field(default=None)
##-- end Rules
