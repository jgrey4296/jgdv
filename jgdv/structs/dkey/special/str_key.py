#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN002, ANN003
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
import string
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv._abstract.protocols.general import Buildable_p, SpecStruct_p
from jgdv.structs.strang import CodeReference

# ##-- end 1st party imports

from .._interface import DKeyMark_e
from ..dkey import DKey
from ..keys import MultiDKey, NonDKey, SingleDKey

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Ident, RxStr, Rx
    from .._interface import KeyMark

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class StrDKey(DKey, mark=str, convert="s"):
    """
    A Simple key that always expands to a string
    """
    __slots__ = ()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.data.expansion_type  = str
        self.data.typecheck       = str
