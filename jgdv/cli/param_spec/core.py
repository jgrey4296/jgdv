#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import builtins
import datetime
import enum
import functools as ftz
import importlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import typing
import weakref
from dataclasses import InitVar, dataclass, field
from types import GenericAlias
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Self,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from pydantic import BaseModel, Field, InstanceOf, field_validator, model_validator

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv._abstract.protocols import Buildable_p, ParamStruct_p, ProtocolModelMeta
from jgdv.mixins.annotate import SubAnnotate_m
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from jgdv.cli.errors import ArgParseError
from ._base import ParamSpecBase

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

NON_ASSIGN_PREFIX : Final[str] = "-"
ASSIGN_PREFIX     : Final[str] = "--"
END_SEP           : Final[str] = "--"

class ToggleParam(ParamSpecBase[bool]):

    def next_value(self, args:list) -> tuple[str, list, int]:
        head, *_ = args
        if self.inverse in head:
            value = self.default_value
        else:
            value = not self.default_value

        return self.name, [value], 1

class LiteralParam(ToggleParam):
    """
    Match on a Literal Parameter.
    For command/subcmd names etc
    """
    prefix : str = ""

    def matches_head(self, val) -> bool:
        """ test to see if a cli argument matches this param

        Will match anything if self.positional
        Matchs {self.prefix}{self.name} if not an assignment
        Matches {self.prefix}{self.name}{separator} if an assignment
        """
        match val:
            case x if x == self.name:
                return True
            case _:
                return False

class ImplicitParam(ParamSpecBase):
    """
    A Parameter that is implicit, so doesn't give a help description unless forced to
    """

    def help_str(self):
        return ""

class KeyParam(ParamSpecBase):
    """ TODO a param that is specified by a prefix key """

    def matches_head(self, val) -> bool:
        return val in self.key_strs

    def get_next_value(self, args:list) -> tuple[list, int]:
        """ get the value for a -key val """
        logging.debug("Getting Key/Value: %s : %s", self.name, args)
        match args:
            case [x, y, *_] if self.matches_head(x):
                return str, [y], 2
            case _:
                raise ArgParseError("Failed to parse key")

class RepeatableParam(KeyParam):
    """ TODO a repeatable key param """

    type_ : InstanceOf[type] = Field(default=list, alias="type")

    def next_value(self, args:list) -> tuple[str, list, int]:
        """ Get as many values as match
        eg: args[-test, 2, -test, 3, -test, 5, -nottest, 6]
        ->  [2,3,5], [-nottest, 6]
        """
        logging.debug("Getting until no more matches: %s : %s", self.name, args)
        assert(self.repeatable)
        result, consumed, remaining  = [], 0, args[:]
        while bool(remaining):
            head, val, *rest = remaining
            if not self.matches_head(head):
                break
            else:
                result.append(val)
                remaining = rest
                consumed += 2

        return self.name, result, consumed

class ChoiceParam(LiteralParam[str]):
    """ TODO A param that must be from a choice of literals """

    def __init__(self, name, choices:list[str], **kwargs):
        super().__init__(name=name, **kwargs)
        self._choices = choices

    def matches_head(self, val) -> bool:
        """ test to see if a cli argument matches this param

        Will match anything if self.positional
        Matchs {self.prefix}{self.name} if not an assignment
        Matches {self.prefix}{self.name}{separator} if an assignment
        """
        return val in self._choices

class EntryParam(LiteralParam):
    """ TODO a parameter that if it matches,
    returns list of more params to parse
    """
    pass

class ConstrainedParam(ParamSpecBase):
    """
    TODO a type of parameter which is constrained in the values it can take, beyond just type.

    eg: {name:amount, constraints={min=0, max=10}}
    """
    constraints : list[Any] = []

