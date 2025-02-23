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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

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
FMT_PATTERN    : Final[Rx]                 = re.compile("^(h?)(t?)(p?)")
UUID_RE        : Final[Rx]                 = re.compile(r"<uuid(?::(.+?))?>")
MARK_RE        : Final[Rx]                 = re.compile(r"\$(.+?)\$")
SEP_DEFAULT    : Final[str]                = "::"
SUBSEP_DEFAULT : Final[str]                = "."
INST_K         : Final[str]                = "instanced"
GEN_K          : Final[str]                = "gen_uuid"
STRGET                                     = str.__getitem__
# Body:

class StrangMarker_e(enum.StrEnum):
    """ Markers Used in a Strang """

    head     = "$head$"
    gen      = "$gen$"
    mark     = ""
    hide     = "_"
    extend   = "+"

class CodeRefMeta_e(enum.StrEnum):
    module  = "module"
    cls     = "cls"
    value   = "value"
    fn      = "fn"

    val     = "value"
    default = fn

##--|
@runtime_checkable
class Strang_p(Protocol):
    pass

@runtime_checkable
class Importable_p(Protocol):
    pass

@runtime_checkable
class PreInitProcessed_p(Protocol):
    """ Protocol for things like Strang,
    whose metaclass preprocess the initialisation data before even __new__ is called.

    Is used in a metatype.__call__ as:
    cls._pre_process(...)
    obj = cls.__new__(...)
    obj.__init__(...)
    obj._process()
    obj._post_process()
    return obj

    """

    @classmethod
    def _pre_process(cls, data:Any, *, strict=False) -> Any:
        pass

    def _process(self) -> None:
        pass

    def _post_process(self) -> None:
        pass
