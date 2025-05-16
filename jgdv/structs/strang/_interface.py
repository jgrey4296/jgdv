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
    import string
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
WORD_DEFAULT   : Final[str]                = "."
SEP_DEFAULT    : Final[str]                = "::"
INST_K         : Final[str]                = "instanced"
GEN_K          : Final[str]                = "gen_uuid"
STRGET         : Final[Callable]           = str.__getitem__
STRCON         : Final[Callable]           = str.__contains__

SEC_END_MSG    : Final[str]                = "Only the last section has no end marker"
##--|
type BODY_TYPES        = str|UUID|StrangMarker_e
type GROUP_TYPES       = str
type BodyMark          = type[enum.StrEnum]
type GroupMark         = type[enum.StrEnum] | type[int]
type SectionDescriptor = tuple[str, type|UnionType, enum.EnumMeta|type[int], bool]
type WordDescriptor    = tuple[str]
# Body:

##--| Data

class Sec_d:
    """ Data of a named Strang section

    for an example section 'a.2.c.+::d'
    - case     : the word boundary.                    = '.'
    - end      : the rhs end str.                      = '::'
    - types    : allowed types.                        = str|int
    - marks    : StrEnum of words with a meta meaning. = '+'
    - required : a strang errors if a required section isnt found

    """
    __slots__ = ("case", "end", "marks", "name", "required", "types")

    def __init__(self, name:str, case:str, end:str, types:type|UnionType, marks:enum.EnumMeta, required:bool=True) -> None:  # noqa: FBT001, FBT002, PLR0913
        self.name     = name.lower()
        self.case     = case
        self.end      = end
        self.types    = types
        self.marks    = marks
        self.required = required

class StrangSections:
    """
    An object to hold information about word separation and sections,
    a strang type is structured into these

    Each Section is a Sec_d
    """
    __slots__ = ("named", "order", "types")
    named  : dict[str, int]
    order  : list[Sec_d]
    types  : UnionType

    def __init__(self, *sections:tuple|Sec_d) -> None:
        self.order = []
        for sec in sections:
            match sec:
                case Sec_d() as s:
                    self.order.append(s)
                case xs:
                    obj = Sec_d(*xs)
                    self.order.append(obj)
        else:
            assert(all(x.end is not None for x in self.order[:-1])), SEC_END_MSG
            self.named = {x.name:i for i,x in  enumerate(self.order)}

    def __getitem__(self, val:int|str) -> Sec_d:
        match val:
            case int() as i:
                return self.order[i]
            case str() as k if k in self.named:
                return self.order[self.named[k]]
            case x:
                raise TypeError(type(x))

    def __iter__(self) -> Iterator[Sec_d]:
        return iter(self.order)

    def __len__(self) -> int:
        return len(self.order)

class Strang_d:
    """ Extra Data of a Strang.
    Sections are accessed by their index, so use cls._sections.named[name] to get the index

    - mark_idx  : tuple[int, int] - the root most body mark, and the leaf mark
    - bounds    : list[slice] - section slices
    - slices    : list[list[slice]] - word slices for each section
    - meta      : list[list] - word level meta data

    """
    __slots__ = ("bounds", "flat", "mark_idx", "meta", "slices")
    mark_idx  : tuple[int, int]
    slices    : tuple[tuple[slice], ...]
    flat      : tuple[slice, ...]
    bounds    : tuple[slice, ...]
    meta      : tuple[Maybe[list], ...]

    def __init__(self, *args) -> None:
        self.mark_idx  = {}
        self.slices    = ()
        self.flat      = ()
        self.meta      = ()
        self.bounds    = ()

##--| Protocols

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

    def pre_process[T:Strang_i](self, cls:type[Strang_i], data:str, *, strict:bool=False) -> str: ...

    def process(self, obj:Strang_i) -> Maybe[Strang_i]: ...

    def post_process(self, obj:Strang_i) -> Maybe[Strang_i]: ...

class ProcessorHooks(Protocol):

    @staticmethod
    def _pre_process_h[T:Strang_i](cls:type[Strang_i], data:str, *, strict:bool=False) -> str: ... # noqa: PLW0211

    def _process_h(self, obj:Strang_i) -> Maybe[Strang_i]: ...

    def _hpost_process_h(self, obj:Strang_i) -> Maybe[Strang_i]: ...

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

class StrangFormatter_p(Protocol):
    """ A string.Formatter with some Strang-specific methods """

    def format(self, format_string:str, /, *args:Any, **kwargs:Any) -> str: ... # noqa: ANN401

    def get_value(self, key:str, args, kwargs) -> str:  ...

    def convert_field(self, value, conversion) -> str: ...

    def expanded_str(self, data:Strang_i, *, stop:Maybe[int]=None) -> str: ...

@runtime_checkable
class Strang_p(StrangTesting_p, StrangMod_p, String_p, Protocol):
    """  """

    @override
    def __getitem__(self, i:int|slice) -> str|Strang_i: ... # type: ignore[override]

    @property
    def base(self) -> Self: ...

    @property
    def shape(self) -> tuple[int, ...]: ...

    def body(self, *, reject:Maybe[Callable]=None, no_expansion:bool=False) -> list[str]: ...

    def get(self, *args:int) -> Any: ...
    def uuid(self) -> Maybe[UUID]: ...

##--| Interfaces

class Strang_i(Strang_p, Protocol):
    _processor        : ClassVar[PreInitProcessed_p]
    _formatter        : ClassVar[string.Formatter]
    _sections         : ClassVar[StrangSections]
    _typevar          : ClassVar[Maybe[type]]
    data             : Strang_d
    meta              : dict
