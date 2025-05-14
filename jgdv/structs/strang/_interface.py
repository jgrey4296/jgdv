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

from jgdv._abstract.str_proto import String_p

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
from collections.abc import Sized
from collections import UserString

if TYPE_CHECKING:
    from jgdv import Maybe, Rx
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from types import UnionType

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Enums

class StrangMarker_e(enum.StrEnum):
    """ Markers Used in a base Strang """

    head     = "$head$"
    gen      = "$gen$"
    mark     = ""
    hide     = "_"
    extend   = "+"

class CodeRefMeta_e(enum.StrEnum):
    """ Available Group values of CodeRef strang's """
    module  = "module"
    cls     = "cls"
    value   = "value"
    fn      = "fn"

    val     = "value"
    default = fn

##--| Vars
FMT_PATTERN    : Final[Rx]                 = re.compile("^(h?)(t?)(p?)")
UUID_RE        : Final[Rx]                 = re.compile(r"<uuid(?::(.+?))?>")
MARK_RE        : Final[Rx]                 = re.compile(r"\$(.+?)\$")
SEP_DEFAULT    : Final[str]                = "::"
SUBSEP_DEFAULT : Final[str]                = "."
INST_K         : Final[str]                = "instanced"
GEN_K          : Final[str]                = "gen_uuid"
STRGET         : Final[Callable]           = str.__getitem__

##--|
type BODY_TYPES  = str|UUID|StrangMarker_e
type GROUP_TYPES = str
type BodyMark    = type[enum.StrEnum]
type GroupMark   = type[enum.StrEnum] | type[int]
# Body:

##--|

@runtime_checkable
class Importable_p(Protocol):
    """  """
    pass

class PreInitProcessed_p(Protocol):
    """ Protocol for things like Strang,
    whose metaclass preprocess the initialisation data before even __new__ is called.

    Is used in a metatype.__call__ as::

        cls._pre_process(...)
        obj = cls.__new__(...)
        obj.__init__(...)
        obj._process()
        obj._post_process()
        return obj

    """

    @classmethod
    def pre_process(cls, data:str, *, strict:bool=False) -> str: ...

    def _process(self) -> None: ...

    def _post_process(self) -> None: ...

class StrangInternal_p(Protocol):

    def _get_slices(self, start:int=0, max:Maybe[int]=None, *, add_offset:bool=False) -> list[slice]: ... # noqa: A002

class StrangTesting_p(Protocol):

    def is_uniq(self) -> bool: ...

    def is_head(self) -> bool: ...

class StrangMod_p(Protocol):

    def with_head(self) -> Self: ...

    def pop(self, *, top:bool=False) -> Self: ...

    def push(self, *vals:str) -> Self: ...

    def to_uniq(self, *, suffix:Maybe[str]=None) -> Self: ...

    def de_uniq(self) -> Self: ...

    def root(self) -> Self: ...

@runtime_checkable
class Strang_p(StrangTesting_p, StrangMod_p, StrangInternal_p, PreInitProcessed_p, String_p, Protocol):
    """  """

    @classmethod
    def _subjoin(cls, lst:list) -> str: ...

    @override
    def __getitem__(self, i:int|slice) -> BODY_TYPES: ... # type: ignore[override]

    @property
    def base(self) -> Self: ...

    @property
    def group(self) -> list[str]: ...

    @property
    def shape(self) -> tuple[int, int]: ...

    def body(self, *, reject:Maybe[Callable]=None, no_expansion:bool=False) -> list[str]: ...

    def uuid(self) -> Maybe[UUID]: ...

class Strang_i(Strang_p, Protocol):
    _separator        : ClassVar[str]
    _subseparator     : ClassVar[str]
    _body_types       : ClassVar[type|UnionType]
    _group_types      : ClassVar[type|UnionType]
    _typevar          : ClassVar[Maybe[type]]
    bmark_e           : ClassVar[type[enum.StrEnum]]
    gmark_e           : ClassVar[type[enum.Enum]|type[enum.StrEnum]|int]

    metadata          : dict
    _base_slices      : tuple[Maybe[slice], Maybe[slice]]
    _mark_idx         : tuple[Maybe[int], Maybe[int]]
    _group            : list[slice]
    _body             : list[slice]
    _body_meta        : list[Maybe[BODY_TYPES]]
    _group_meta       : set[GROUP_TYPES]
