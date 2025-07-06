#!/usr/bin/env python3
"""

"""
# ruff: noqa:

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
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

from dataclasses import dataclass, field, InitVar
from typing import Any

if TYPE_CHECKING:
    import types
    from jgdv import Maybe, Rx
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
DEFAULT_PREFIX  : Final[str]  = "-"
END_SEP         : Final[str]  = "--"
FULLNAME_RE     : Final[Rx]   = re.compile(r"(?:<(?P<pos>\d*)>|(?P<prefix>\W+))?(?P<name>.+?)(?P<assign>=)?$")
DEFAULT_DOC     : Final[str]  = "A Base Parameter"
""" The Regexp for parsing string descriptions of parameters """

##--|
EMPTY_CMD           : Final[str]  = "_cmd_"
EXTRA_KEY           : Final[str]  = "_extra_"
NON_DEFAULT_KEY     : Final[str]  = "_non_default_"
DEFAULT_COUNT       : Final[int]  = 1
UNRESTRICTED_COUNT  : Final[int]  = -1
##--|
TYPE_CONV_MAPPING: Final[dict[str|type|types.GenericAlias, type|Callable]] = {
    "int"               : int,
    "float"             : float,
    "bool"              : bool,
    "str"               : str,
    "list"              : list,
}

# Body:

class SectionType_e(enum.Enum):
    """ The different types of section a parse machine can process """
    prog = enum.auto()
    cmd  = enum.auto()
    sub  = enum.auto()

class ParseResult_d:
    """ Simple container for parsed cli information

    Name : the name of the spec that parsed this data
    args : mapping of {arg -> data}, including default values it nothing parsing for it
    non_default : set[arg, ...] that actually parsed
    ref : the name of a linked parse result this object extends

    """
    __slots__ = ("args", "name", "non_default", "ref")
    name         : str
    args         : dict
    non_default  : set[str]
    ref          : Maybe[str]

    def __init__(self, name:str, args:Maybe[dict]=None, ref:Maybe[str]=None) -> None:
        self.name         = name
        self.args         = args or {}
        self.non_default  = set()
        self.ref          = ref

    @override
    def __repr__(self) -> str:
        return f"<ParseResult: {self.name}, args:{self.args}>"

    def to_dict(self) -> dict:
        return {"name":self.name, "args":self.args, NON_DEFAULT_KEY:self.non_default}

class ParseReport_d:
    """ The returned data of parsing cli args

    Contains:
    - raw : the raw args that were used. ieg: sys.argv[:]
    - remaining : anything not parsed
    - prog : ParseResult_d of base program arguments
    - cmds : mapping(cmdName -> [ParseResult_d])
    - subs : mapping(subName -> [ParseResult_d])
    - help : bool

    """
    type CmdName = str
    type SubName = str
    __slots__ = ("cmds", "help", "prog", "raw", "remaining", "subs")
    raw        : tuple[str, ...]
    remaining  : tuple[str, ...]
    prog       : ParseResult_d
    cmds       : dict[CmdName, tuple[ParseResult_d]]
    subs       : dict[SubName, tuple[ParseResult_d]]
    help       : bool

    def __init__(self, *, raw:Iterable[str], remaining:Iterable[str], prog:ParseResult_d, help:bool) -> None:  # noqa: A002
        self.raw        = tuple(raw)
        self.remaining  = tuple(remaining)
        self.help       = help
        self.prog       = prog
        self.cmds       = {}
        self.subs       = {}

    def to_dict(self) -> dict:
        return {
            "prog" : self.prog.to_dict(),
            "cmds" : {x: [y.to_dict() for y in ys] for x,ys in self.cmds.items()},
            "subs" : {x: [y.to_dict() for y in ys] for x,ys in self.subs.items()},
            "help" : help,
        }

##--| Params

@runtime_checkable
class ParamSpec_p(Protocol):
    """ Base class for CLI param specs, for type matching
    when 'consume' is given a list of strs,
    it can match on the args,
    and return an updated diction and a list of values it didn't consume

    """

    @classmethod
    def key_func(cls, x:ParamSpec_i) -> tuple: ...

    def consume(self, args:list[str], *, offset:int=0) -> Maybe[tuple[dict, int]]:
        pass

    ##--| properties

    @property
    def short(self) -> str: ...

    @property
    def inverse(self) -> str: ...

    @property
    def repeatable(self) -> bool: ...

    @property
    def key_str(self) -> str: ...

    @property
    def short_key_str(self) -> Maybe[str]: ...

    @property
    def key_strs(self) -> list[str]: ...

    @property
    def default_value(self) -> Any: ...  # noqa: ANN401

    @property
    def default_tuple(self) -> tuple[str, Any]: ...

    def help_str(self, *, force:bool=False) -> str: ...

class ParamSpec_i(ParamSpec_p, Protocol):
    _processor : ClassVar

    name       : str
    type_      : Maybe[type]
    insist     : bool
    default    : Any|Callable
    desc       : str
    count      : int
    prefix     : int|str
    separator  : str|Literal[False]
    implicit   : bool

##--| Param Subtypes

@runtime_checkable
class PositionalParam_p(Protocol):

    def _positional(self) -> Literal[True]: ...

@runtime_checkable
class AssignmentParam_p(Protocol):

    def _assignment(self) -> Literal[True]: ...

@runtime_checkable
class KeyParam_p(Protocol):

    def _keyval(self) -> Literal[True]: ...

@runtime_checkable
class ToggleParam_p(Protocol):

    def _toggle(self) -> Literal[True]: ...
##--| Parsing

@runtime_checkable
class ArgParserModel_p(Protocol):
    """ The Model used in a jgdv.cli.arg_parser:ParseMachine to implement specific parsing logic """

    def prepare_for_parse(self, *, prog:ParamSource_p, cmds:list[ParamSource_p], subs:list[tuple[tuple[str, ...], ParamSource_p]], raw_args:list[str]) -> None: ...

@runtime_checkable
class ParamSource_p(Protocol):
    """ Param Sources are anything that can provide a name and a set of parameters """

    @property
    def name(self) -> str:
        raise NotImplementedError()

    def param_specs(self) -> list[ParamSpec_i]:
        raise NotImplementedError()

@runtime_checkable
class CLIParamProvider_p(Protocol):
    """
      Things that can provide parameter specs for CLI parsing
    """

    @classmethod
    def param_specs(cls) -> list[ParamSpec_i]:
        """  make class parameter specs  """
        pass
