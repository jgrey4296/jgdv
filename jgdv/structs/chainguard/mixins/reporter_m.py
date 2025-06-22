#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import atexit#  for @atexit.register
import collections
import contextlib
import datetime
import enum
import faulthandler
import functools as ftz
import hashlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types as types_
import weakref
from copy import deepcopy
from time import sleep
from uuid import UUID, uuid1
from weakref import ref

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

if TYPE_CHECKING:
    from .._interface import TomlTypes
    from jgdv import Maybe
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

class DefaultedReporter_m:
    """ A Mixin for reporting values that a failure proxy defaulted on. """

    _defaulted : ClassVar[set[str]] = set()

    @staticmethod
    def add_defaulted(index:str|list[str], val:Any, types:Maybe[str]=None) -> None:  # noqa: ANN401
        types = types or "Any"
        match index, val:
            case _, ():
                return
            case list(), _:
                msg = "Tried to Register a default value with a list index, use a str"
                raise TypeError(msg)
            case str(), bool():
                index_str = f"{index} = {str(val).lower()} # <{types}>"
            case str(), _:
                index_str = f"{index} = {val!r} # <{types}>"
            case [*xs], bool():
                index_path = ".".join(xs)
                index_str = f"{index_path} = {str(val).lower()} # <{types}>"
            case [*xs], _:
                index_path = ".".join(xs)
                index_str = f"{index_path} = {val} # <{types}>"
            case _, _:
                msg = "Unexpected Values found: "
                raise TypeError(msg, val, index)

        DefaultedReporter_m._defaulted.add(index_str)

    @staticmethod
    def report_defaulted() -> list[str]:
        """
        Report the index paths inject default values
        """
        return list(DefaultedReporter_m._defaulted)
