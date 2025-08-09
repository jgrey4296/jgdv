#!/usr/bin/env python3
"""

"""
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

from .param_spec import ParamSpec
from .core import AssignParam, ToggleParam, KeyParam, LiteralParam

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class RepeatToggleParam(ToggleParam):
    """ TODO A repeatable toggle
    eg: -verbose -verbose -verbose
    """
    desc : str = "A Repeat Toggle"
    pass

class WildcardParam(AssignParam):
    """ TODO a wildcard param that matches any --{key}={val} """

    desc : str = "A Wildcard"

    def __init__(self, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401, ARG002
        kwargs.setdefault("type", str)
        kwargs['name'] = "*"
        super().__init__(**kwargs)

    def matches_head(self, val:str) -> bool:
        assert(isinstance(self.separator, str))
        match self.prefix:
            case str() as p:
                return (val.startswith(p)
                        and self.separator in val)
            case _:
                return False

    def next_value(self, args:list) -> tuple[str, list, int]:
        logging.debug("Getting Wildcard Key Assingment: %s", args)
        assert(self.separator in args[0]), (self.separator, args[0])
        key,val = self._processor.split_assignment(self, args[0])
        match self.prefix:
            case str():
                return key.removeprefix(self.prefix), [val], 1
            case int():
                return key, [val], 1


class ImplicitParam(ParamSpec):
    """
    A Parameter that is implicit, so doesn't give a help description unless
    forced to
    """
    desc : str = "An Implicit Parameter"

    def help_str(self, *, force:bool=False) -> str:
        return ""

class RepeatableParam(KeyParam):
    """ TODO a repeatable key param
    -key val -key val2 -key val3
    """

    type_ : type
    desc  : str = "A Repeatable Key"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.type_ = list

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

class ChoiceParam(LiteralParam):
    """ TODO A param that must be from a choice of literals
    eg: ChoiceParam([blah, bloo, blee]) : blah | bloo | blee

    """

    desc : str = "A Choice"

    def __init__(self, name, choices:list[str], **kwargs) -> None:
        super().__init__(name=name, **kwargs)
        self._choices = choices

    def matches_head(self, val) -> bool:
        """ test to see if a cli argument matches this param

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

class ConstrainedParam(ParamSpec):
    """
    TODO a type of parameter which is constrained in the values it can take, beyond just type.

    eg: {name:amount, constraints={min=0, max=10}}
    """
    constraints  : list[Any]
    desc         : str  = "A Constrained Param"
