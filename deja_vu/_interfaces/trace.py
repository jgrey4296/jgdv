#/usr/bin/env python3
"""
How model results are represented and manipulated
"""
##-- imports
from __future__ import annotations

import abc
import logging as logmod
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from re import Pattern
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

from clingo import Symbol
from instal.defaults import STATE_HOLDSAT_GROUPS
from instal.interfaces.ast import TermAST
from instal.interfaces.solver import InstalModelResult

if TYPE_CHECKING:
    # tc only imports
    pass
##-- end imports


logging = logmod.getLogger(__name__)


@dataclass
class State_i:
    """
    Description of a single moment in a model's trace.
    Depending on implementation, could hold TermAST's
    or Clingo Symbols
    """

    timestep : int            = field(default=0)
    holdsat  : dict[str, Any] = field(default_factory=dict)
    occurred : list[Any]      = field(default_factory=list)
    observed : list[Any]      = field(default_factory=list)
    rest     : list[Any]      = field(default_factory=list)

    def __post_init__(self):
        for x in STATE_HOLDSAT_GROUPS:
            self.holdsat[x] = []

    def __iter__(self):
        for x in self.fluents:
            yield x

        for x in self.occurred:
            yield x

        for x in self.observed:
            yield x

        for x in self.rest:
            yield x

    @property
    def fluents(self) -> iter[Any]:
        """ Iterate through all the fluents as a list
        instead of as a dict of separate types of fluent
        """
        for items in self.holdsat.values():
            for entry in items:
                yield entry


    @abc.abstractmethod
    def __repr__(self): pass

    @abc.abstractmethod
    def to_json(self) -> dict: pass

    @abc.abstractmethod
    def check(self, conditions) -> bool: pass

    @abc.abstractmethod
    def insert(self, val:str|TermAST|Symbol): pass


    @abc.abstractmethod
    def filter(self, allow:list[Any], reject:list[Any]) -> State_i: pass


    # @abc.abstractmethod
    # def conflicts(self) -> list[tuple[int, Any, Any]]: pass

@dataclass
class Trace_i(Sequence):
    """
    The collected sequence of instance states which comprise
    a full model run
    """
    states   : InitVar[list[State_i]] = field()
    metadata : dict                   = field(default_factory=dict)

    _states  : dict[str, State_i]     = field(default_factory=dict)
    _ordered : list[int]              = field(init=False, default_factory=list)
    state_constructor : ClassVar[State_i] = None

    def __post_init__(self, states):
        self._states  = {x.timestep : x for x in states}
        self._ordered = sorted(x.timestep for x in states)


    @staticmethod
    @abc.abstractmethod
    def from_json(data): pass
    @staticmethod
    @abc.abstractmethod
    def from_model(model:InstalModelResult, steps:int=1): pass
    def __getitem__(self, index):
        return self._states[index]

    def __iter__(self):
        return iter(self._states.values())

    def contextual_iter(self) -> iter[tuple]:
        """
        provide an iterator of tuples
        [timestep, state, state-1, state+1]
        """
        states : list = list(self._states.values())
        return zip(range(len(self)),
                   states,
                   [None] + states,
                   states[1:] + [None])

    def __len__(self):
        return len(self._states)

    def last(self) -> State_i:
        return self._states[str(self._ordered[-1])]

    @property
    def timesteps(self) -> list[int]:
        return list(self._states.keys())

    @abc.abstractmethod
    def __repr__(self): pass

    @abc.abstractmethod
    def check(self, conditions:list) -> bool: pass
    @abc.abstractmethod
    def to_json_str(self, filename=None) -> str: pass

    @abc.abstractmethod
    def filter(self, allow:list[str], reject:list[str], start:None|int=None, end:None|int=None) -> Trace_i: pass

    @abc.abstractmethod
    def fluent_intervals(self) -> list[tuple[str, int, int]]: pass

    # @abc.abstractmethod
    # def conflicts(self) -> list[tuple[int, Any, Any]]: pass


@dataclass
class TraceTree_i:
    """
    Collections of traces which merge to form a tree, branching at diverging actions
    """

    # [state, [successors]]
    states : dict[str, tuple[State_i, list[str]]]
    start  : str

    def add_trace(self, trace):
        """ Add a trace into the tree
        comparing and discarding states until the divergent point is found.
        """
        pass
