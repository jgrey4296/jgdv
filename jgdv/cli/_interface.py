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
import types
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

if TYPE_CHECKING:
    from jgdv import Maybe, Rx
    from typing import Final
    from typing import ClassVar, Any, LiteralString
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
DEFAULT_PREFIX    : Final[str]  = "-"
END_SEP           : Final[str]  = "--"
FULLNAME_RE       : Final[Rx]   = re.compile(r"(?:<(?P<pos>\d*)>|(?P<prefix>\W+))?(?P<name>.+?)(?P<assign>=)?$")

EMPTY_CMD         : Final[str]  = "_cmd_"
EXTRA_KEY         : Final[str]  = "_extra_"
NON_DEFAULT_KEY   : Final[str]  = "_non_default_"
# Body:

@dataclass
class ParseResult_d:
    name        : str
    args        : dict     = field(default_factory=dict)
    non_default : set[str] = field(default_factory=set)

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

    def consume(self, args:list[str], *, offset:int=0) -> Maybe[tuple[dict, int]]:
        pass


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

    @property
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
