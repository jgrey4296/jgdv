#/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import warnings
import abc
import logging as logmod
from collections import defaultdict
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from re import Pattern
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

from instal.interfaces.ast import InstalAST

if TYPE_CHECKING:
    # tc only imports
    pass
##-- end imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging



class InstalASTVisitor_i(metaclass=abc.ABCMeta):
    """
    Interface for the AST Visitor,
    the stub of whic which can be generated
    with instal.cli.generate_vistor
    """

    @abc.abstractmethod
    def visit(self, node:InstalAST, *, skip_actions=False): pass

    @abc.abstractmethod
    def visit_all(self, nodes:list[InstalAST]): pass

    @abc.abstractmethod
    def generic_visit(self, node): pass

    @abc.abstractmethod
    def flatten_for_classes(self, *classes): pass

    @abc.abstractmethod
    def add_actions(self, actions_obj): pass
