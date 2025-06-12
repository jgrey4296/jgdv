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
from weakref import ref
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

EMPTY_CMD         : Final[str]  = "_cmd_"
EXTRA_KEY         : Final[str]  = "_extra_"
NON_DEFAULT_KEY   : Final[str]  = "_non_default_"

TYPE_CONV_MAPPING: Final[dict[str|type|types.GenericAlias, type|Callable]] = {
    "int"               : int,
    "float"             : float,
    "bool"              : bool,
    "str"               : str,
    "list"              : list,
}

# Body:

class ParseResult_d:
    __slots__ = ("args", "name", "non_default")
    name        : str
    args        : dict
    non_default : set[str]

    def __init__(self, name:str, args:Maybe[dict]=None, non_default:Maybe[set]=None) -> None:
        self.name         = name
        self.args         = args or {}
        self.non_default  = non_default or set()

    def __repr__(self) -> str:
        return f"<ParseResult: {self.name}, args:{self.args}>"

    def to_dict(self) -> dict:
        return {"name":self.name, "args":self.args, NON_DEFAULT_KEY:self.non_default}
##--|

@runtime_checkable
class ParamStruct_p(Protocol):
    """ Base class for CLI param specs, for type matching
    when 'consume' is given a list of strs,
    it can match on the args,
    and return an updated diction and a list of values it didn't consume

    """

    @staticmethod
    def key_func(x:ParamStruct_i) -> tuple: ...

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
    def positional(self) -> bool: ...

    @property
    def default_value(self) -> Any: ...  # noqa: ANN401

    @property
    def default_tuple(self) -> tuple[str, Any]: ...

class ParamStruct_i(ParamStruct_p, Protocol):
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

@runtime_checkable
class ArgParser_p(Protocol):
    """
    A Single standard process point for turning the list of passed in args,
    into a dict, into a chainguard,
    along the way it determines the cmds and tasks that have been chosne
    """

    def _parse_fail_cond(self) -> bool:
        raise NotImplementedError()

    def _has_no_more_args_cond(self) -> bool:
        raise NotImplementedError()

@runtime_checkable
class ParamSource_p(Protocol):

    @property
    def name(self) -> str:
        raise NotImplementedError()

    def param_specs(self) -> list[ParamStruct_p]:
        raise NotImplementedError()

@runtime_checkable
class CLIParamProvider_p(Protocol):
    """
      Things that can provide parameter specs for CLI parsing
    """

    @classmethod
    def param_specs(cls) -> list[ParamStruct_p]:
        """  make class parameter specs  """
        pass
