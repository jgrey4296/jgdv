"""
How an external solver (eg: Clingo, but could be Z3 etc) integrates into Instal
"""
##-- imports
from __future__ import annotations

import abc
import logging as logmod
import time
import warnings
from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from typing import (IO, TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, List, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)

from clingo import parse_term

if TYPE_CHECKING:
    # tc only imports
    from pathlib import Path
    from instal.interfaces.ast import TermAST

##-- end imports

logging = logmod.getLogger(__name__)

@dataclass
class InstalModelResult:
    """
    The immediate results data structure returned by a solver.
    Does no translation from the data structures the solver uses.

    ie: for Clingo, it is lists of clingo.Symbol's
    """
    atoms   : list[Any]
    shown   : list[Any]
    cost    : float
    number  : int
    optimal : bool
    type    : Any


@dataclass
class SolverWrapper_i:
    """
    An wrapper around a solver (ie: clingo) to interface with the rest of instal
    """

    program        : None|str                = field(default=None)
    input_files    : list[Path]              = field(default_factory=list, kw_only=True)

    timestamp      : float                   = field(init=False, default_factory=time.time)
    results        : list[InstalModelResult] = field(init=False, default_factory=list)
    current_answer : int                     = field(init=False, default=0)
    cycle          : int                     = field(init=False, default=0)
    observations   : list[TermAST]           = field(default_factory=list)


    def __post_init__(self): pass


    @abc.abstractmethod
    def solve(self, assertions:None|list[Any]=None, fresh=False) -> int: pass

    @property
    @abc.abstractmethod
    def metadata(self): pass
