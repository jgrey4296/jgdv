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
from .. import _interface as API # noqa: N812
from .param_spec import ParamSpec

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

class ToggleParam(ParamSpec, annotation=bool, default=True):
    """ A bool of -param or -not-param """

    desc : str = "A Toggle"

    def __init__(self, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        if self.type_ is not bool:
            msg = "Toggle Params can only be boolean"
            raise TypeError(msg, self.name)

    def _toggle(self) -> Literal[True]:
        return True

    def next_value(self, args:list) -> tuple[str, list, int]:
        head, *_ = args
        if self.inverse in head:
            value = self.default_value
        else:
            value = not self.default_value

        return self.name, [value], 1

class KeyParam(ParamSpec[str]):
    """ a param that is specified by a prefix key

    eg: -key val
    """
    desc  : str = "A Key"

    def _keyval(self) -> Literal[True]:
        return True

    def matches_head(self, val:str) -> bool:
        return val in self.key_strs

    def next_value(self, args:list) -> tuple[str, list, int]:
        """ get the value for a -key val """
        logging.debug("Getting Key/Value: %s : %s", self.name, args)
        match args:
            case [x, y, *_] if self.matches_head(x):
                return self.name, [y], 2
            case _:
                msg = "Failed to parse key"
                raise ArgParseError(msg)

class AssignParam(ParamSpec):
    """ a joined --key=val param """

    desc : str = "An Assignment Param"

    def __init__(self, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        kwargs.setdefault("type", str)
        super().__init__(*args, **kwargs)
        if self.type_ is bool:
            msg = "A boolean assignment param is pointless, use a toggle"
            raise TypeError(msg, self.name)
        match self.prefix:
            case str() as x if bool(x):
                pass
            case x:
                msg = "Bad prefix value for an assignment param"
                raise ValueError(msg, x)
        match self.separator:
            case str() as x if bool(x):
                pass
            case x:
                msg = "Bad separator value for an assignment param"
                raise ValueError(msg, x)

    def _assignment(self) -> Literal[True]:
        return True

    def next_value(self, args:list) -> tuple[str, list, int]:
        """ get the value for a --key=val """
        logging.debug("Getting Key Assignment: %s : %s", self.name, args)
        if self.separator not in args[0]:
            msg = "Assignment param has no assignment"
            raise ArgParseError(msg, self.separator, args[0])
        key,val = self._processor.split_assignment(self, args[0])
        return self.name, [val], 1

class PositionalParam(ParamSpec):
    """ A param that is specified by its position in the arg list

    Positional Params are formatted as <int>name.
    eg: <2>blah

    The integer is the *relative* sort of the parameter.
    As the full parameter list can be accumulated at runtime,
    ParamSpec sorts them ready for use.
    See ParamSpec.key_func.

    Suffice to say, at specification time: <2>blah <50>aweg <-2>qqqq
    Results in a run time positional param list of: qqqq, blah, aweg

    """

    desc : str = "A Positional Param"

    def _positional(self) -> Literal[True]:
        return True

    @ftz.cached_property
    def key_str(self) -> str:
        return self.name

    def matches_head(self, val:str) -> bool:  # noqa: ARG002
        return True

    def next_value(self, args:list) -> tuple[str, list, int]:
        match self.count:
            case API.DEFAULT_COUNT:
                return self.name, [args[0]], 1
            case API.UNRESTRICTED_COUNT if self._processor.end_sep in args:
                idx     = args.index(self._processor.end_sep)
                claimed = args[max(idx, len(args))]
                return self.name, claimed, len(claimed)
            case API.UNRESTRICTED_COUNT:
                return self.name, args[:], len(args)
            case int() as x if x < len(args):
                return self.name, args[:x], x
            case x:
                msg = "Bad positional count"
                raise ArgParseError(msg, x)


class LiteralParam(ToggleParam):
    """
    Match on a Literal Parameter.
    For command/subcmd names etc
    """
    desc   : str = "A Literal"

    def matches_head(self, val:str) -> bool:
        """ test to see if a cli argument matches this param """
        match val:
            case x if x == self.key_str:
                return True
            case _:
                return False
