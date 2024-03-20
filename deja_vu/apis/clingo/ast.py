#/usr/bin/env python3
"""
AST representations bridging parsed DSL -> compiled clingo
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

logging = logmod.getLogger(__name__)

VAR_SIG_REG = re.compile(r"\d+$")

##-- util context manager

class ASTContextManager:
    """ For ensuring all ASTs are built with the correct source """

    def __init__(self, parse_source):
        self.parse_source = parse_source

    def __enter__(self):
        SolverAST.current_parse_source = self.parse_source

    def __exit__(self, exc_type, exc_value, exc_traceback):
        SolverAST.current_parse_source = None

##-- end util context manager

@dataclass(frozen=True)
class SolverAST:
    parse_source : list[str|pl.Path]    = field(default_factory=list, kw_only=True, repr=False)
    parse_loc    : None|tuple[int, int] = field(default=None, kw_only=True)

    current_parse_source : ClassVar[None|str] = None

    def __post_init__(self):
        if SolverAST.current_parse_source is not None:
            self.parse_source.append(SolverAST.current_parse_source)

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
class TermAST(SolverAST):
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
