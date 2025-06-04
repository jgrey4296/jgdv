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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv.mixins.annotate.annotate import SubAnnotate_m
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from jgdv import Proto
from jgdv.cli.errors import ArgParseError
from ._base import ParamSpecBase

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any
from collections.abc import Callable
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

from pydantic import Field, InstanceOf
if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Any, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
from .._interface import ParamStruct_p
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class ToggleParam(ParamSpecBase): #[bool]):
    """ A bool of -param or -not-param """

    desc : str = "A Toggle"

    def next_value(self, args:list) -> tuple[str, list, int]:
        head, *_ = args
        if self.inverse in head:
            value = self.default_value
        else:
            value = not self.default_value

        return self.name, [value], 1

class RepeatToggleParam(ToggleParam):
    """ TODO A repeatable toggle
    eg: -verbose -verbose -verbose
    """
    desc : str = "A Repeat Toggle"
    pass

class LiteralParam(ToggleParam):
    """
    Match on a Literal Parameter.
    For command/subcmd names etc
    """
    desc   : str = "A Literal"
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
    A Parameter that is implicit, so doesn't give a help description unless
    forced to
    """
    desc : str = "An Implicit Parameter"

    def help_str(self):
        return ""

class KeyParam(ParamSpecBase):
    """ TODO a param that is specified by a prefix key
    eg: -key val
    """
    type_ : InstanceOf[type] = Field(default=str, alias="type")
    desc  : str = "A Key"

    def matches_head(self, val) -> bool:
        return val in self.key_strs

    def next_value(self, args:list) -> tuple[str, list, int]:
        """ get the value for a -key val """
        logging.debug("Getting Key/Value: %s : %s", self.name, args)
        match args:
            case [x, y, *_] if self.matches_head(x):
                return self.name, [y], 2
            case _:
                raise ArgParseError("Failed to parse key")

class RepeatableParam(KeyParam):
    """ TODO a repeatable key param
    -key val -key val2 -key val3
    """

    type_ : InstanceOf[type] = Field(default=list, alias="type")
    desc  : str = "A Repeatable Key"

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

class ChoiceParam(LiteralParam): # [str]):
    """ TODO A param that must be from a choice of literals
    eg: ChoiceParam([blah, bloo, blee]) : blah | bloo | blee

    """

    desc : str = "A Choice"

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
    desc : str = "An expandable Param"
    pass

class ConstrainedParam(ParamSpecBase):
    """
    TODO a type of parameter which is constrained in the values it can take, beyond just type.

    eg: {name:amount, constraints={min=0, max=10}}
    """
    constraints : list[Any] = []
    desc : str = "A Constrained Param"
