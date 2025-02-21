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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv.mixins.annotate import SubAnnotate_m
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from jgdv.cli.errors import ArgParseError
from ._base import ParamSpecBase
from .._interface import END_SEP

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any, Callable
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
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

class PositionalParam(ParamSpecBase):
    """ TODO a param that is specified by its position in the arg list """

    @ftz.cached_property
    def key_str(self) -> str:
        return self.name

    def matches_head(self, val) -> bool:
        return True

    def next_value(self, args:list) -> tuple[str, list, int]:
        match self.count:
            case 1:
                return self.name, [args[0]], 1
            case -1:
                idx     = args.index(END_SEP)
                claimed = args[max(idx, len(args))]
                return self.name, claimed, len(claimed)
            case int() as x if x < len(args):
                return self.name, args[:x], x
            case _:
                raise ArgParseError()
