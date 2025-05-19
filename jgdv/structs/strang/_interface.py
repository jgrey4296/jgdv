#!/usr/bin/env python3
"""
The Interface for Strang.

Strang Enums:
- StrangMarkAbstract_e

Describes the internal data structs:
- Sec_d : A Single section spec
- Sections_d : Collects the sec_d's. ClassVar
- Strang_d : Instance data of a strang beyond the normal str's

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
from types import UnionType

if TYPE_CHECKING:
    from jgdv import Maybe, Rx
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard, SupportsIndex
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    import string
    from enum import Enum

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Enums

class StrangMarkAbstract_e(enum.StrEnum):

    @classmethod
    def default(cls) -> Maybe:
        return None

    @classmethod
    def implicit(cls) -> set:
        return set()

    @classmethod
    def skip(cls) -> Maybe:
        return None

    @classmethod
    def idempotent(cls) -> set[str]:
        return set()

class DefaultHeadMarks_e(StrangMarkAbstract_e):
    """ Markers used in a Strang's head """
    basic = "$basic$"

class DefaultBodyMarks_e(StrangMarkAbstract_e):
    """ Markers Used in a base Strang's body """

    head    = "$head$"
    gen     = "$gen$"
    empty   = ""
    hide    = "_"
    extend  = "+"
    unique  = "<uuid>"

    @classmethod
    def default(cls) -> str:
        return cls.head

    @classmethod
    def implicit(cls) -> set[str]:
        return {cls.hide, cls.empty}

    @classmethod
    def skip(cls) -> Maybe[str]:
        return cls.empty

    @classmethod
    def idempotent(cls) -> set[str]:
        return {cls.head, cls.gen}

class CodeRefHeadMarks_e(StrangMarkAbstract_e):
    """ Available Group values of CodeRef strang's """
    module  = "module"
    cls     = "cls"
    value   = "value"
    fn      = "fn"

    val     = "value"

    @classmethod
    def default(cls) -> str:
        return cls.fn

##--| Vars
FMT_PATTERN   : Final[Rx]        = re.compile("^(h?)(t?)(p?)")
TYPE_RE       : Final[Rx]        = re.compile(r"<(.+?)(?::(.+?))?>")
TYPE_ITER_RE  : Final[Rx]        = re.compile(r"(<)(.+?)(?::(.+?))?(>)")
MARK_RE       : Final[Rx]        = re.compile(r"(\$.+?\$)")
MARK_ITER_RE  : Final[Rx]        = re.compile(r"(\$)(.+?)(\$)")
CASE_DEFAULT  : Final[str]       = "."
END_DEFAULT   : Final[str]       = "::"
INST_K        : Final[str]       = "instanced"
GEN_K         : Final[str]       = "gen_uuid"
STRGET        : Final[Callable]  = str.__getitem__
STRCON        : Final[Callable]  = str.__contains__
UUID_WORD     : Final[str]       = "<uuid>"

SEC_END_MSG   : Final[str]       = "Only the last section has no end marker"

##--|
type FullSlice     = slice[None, None, None]
type MSlice        = slice[Maybe[int], Maybe[int], Maybe[int]]
type HEAD_TYPES    = str
type BODY_TYPES    = str|UUID|DefaultBodyMarks_e
type SectionIndex  = str|int
type WordIndex     = tuple[SectionIndex, int]
type MarkIndex     = tuple[SectionIndex, StrangMarkAbstract_e]
type FindSlice     = str|StrangMarkAbstract_e|WordIndex|MarkIndex
type ItemIndex     = SectionIndex | FullSlice | MSlice | tuple[ItemIndex, ItemIndex]
type PushVal       = Maybe[str | StrangMarkAbstract_e | UUID]
##--| Section Specs
HEAD_SEC            : Final[tuple]  = ("head", CASE_DEFAULT, END_DEFAULT, BODY_TYPES, DefaultHeadMarks_e, True)
BODY_SEC            : Final[tuple]  = ("body", CASE_DEFAULT, None, HEAD_TYPES, DefaultBodyMarks_e, True)

CODEREF_HEAD_SEC    : Final[tuple]  = ("head",   CASE_DEFAULT, None, HEAD_TYPES, CodeRefHeadMarks_e, True)
CODEREF_MODULE_SEC  : Final[tuple]  = ("module", CASE_DEFAULT, None, HEAD_TYPES, DefaultBodyMarks_e, True)
CODEREF_VAL_SEC     : Final[tuple]  = ("value",  CASE_DEFAULT, None, HEAD_TYPES, CodeRefHeadMarks_e, True)
##--| Data

class Sec_d:
    """ Data of a named Strang section

    for an example section 'a.2.c.+::d'
    - case      : the word boundary.                              = '.'
    - end       : the rhs end str.                                = '::'
    - types     : allowed types.                                  = str|int
    - marks     : StrangMarkAbstract_e of words with a meta meaning.  = '+'
    - required  : a strang errors if a required section isnt found

    - idx       : the index of the section

    TODO Maybe 'type_re' and 'mark_re'

    """
    __slots__ = ("case", "end", "idx", "marks", "name", "required", "types")

    def __init__(self, name:str, case:str, end:str, types:type|UnionType, marks:type[StrangMarkAbstract_e], required:bool=True, *, idx:int=-1) -> None:  # noqa: FBT001, FBT002, PLR0913
        assert(0 <= idx)
        self.idx       : int                     = idx
        self.name      : str                     = name.lower()
        self.case      : str                     = case
        self.end       : Maybe[str]              = end
        self.types     : type|UnionType          = types
        self.marks     : type[StrangMarkAbstract_e]  = marks
        self.required  : bool                    = required

    def __contains__(self, other:type|StrangMarkAbstract_e) -> bool:
        match other:
            case type() as x:
                return issubclass(x, self.types)
            case UnionType() as xs:
                # Check its contained using its removal of duplicates
                return (xs | self.types) == self.types
            case StrangMarkAbstract_e() as x:
                return x in self.marks
            case _:
                return False

class Sections_d:
    """
    An object to hold information about word separation and sections,
    a strang type is structured into these

    Each Section is a Sec_d
    TODO add format conversion specs
    """
    __slots__ = ("named", "order", "types")
    named  : dict[str, int]
    order  : list[Sec_d]
    types  : type|UnionType

    def __init__(self, *sections:tuple|Sec_d) -> None:
        self.order = []
        self.named = {}
        for i, sec in enumerate(sections):
            match sec:
                case Sec_d() as obj:
                    obj.idx = i
                    self.order.append(obj)
                    self.named[obj.name] = i
                case xs:
                    obj = Sec_d(*xs, idx=i)
                    self.order.append(obj)
                    self.named[obj.name] = i
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
                raise KeyError(x)

    def __iter__(self) -> Iterator[Sec_d]:
        return iter(self.order)

    def __len__(self) -> int:
        return len(self.order)

class Strang_d:
    """ Extra Data of a Strang.
    Sections are accessed by their index, so use cls._sections.named[name] to get the index

    - bounds    : list[slice] - section slices
    - slices    : list[list[slice]] - word slices for each section
    - meta      : list[list] - word level meta data

    """
    __slots__ = ("bounds", "flat", "meta", "slices", "uuid")
    slices    : tuple[tuple[slice, ...], ...]
    flat      : tuple[slice, ...]
    bounds    : tuple[slice, ...]
    meta      : tuple[Maybe[tuple[Maybe[StrangMarkAbstract_e]]], ...]
    uuid      : Maybe[UUID]

    def __init__(self, uuid:Maybe[UUID]=None) -> None:
        self.slices  = ()
        self.flat    = ()
        self.meta    = ()
        self.bounds  = ()
        self.uuid    = uuid

##--| Protocols

@runtime_checkable
class Importable_p(Protocol):
    """  """
    pass

class PreProcessor_p(Protocol):
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

    def pre_process[T:Strang_i](self, cls:type[Strang_i], data:str, *, strict:bool=False) -> tuple[str, dict]: ...

    def process(self, obj:Strang_i) -> Maybe[Strang_i]: ...

    def post_process(self, obj:Strang_i) -> Maybe[Strang_i]: ...

class ProcessorHooks(Protocol):

    @classmethod
    def _pre_process_h[T:Strang_i](cls:type[T], data:str, *, strict:bool=False) -> tuple[str, dict]: ...

    def _process_h(self, obj:Strang_i) -> Maybe[Strang_i]: ...

    def _post_process_h(self, obj:Strang_i) -> Maybe[Strang_i]: ...

class StrangUUIDs_p(Protocol):

    def to_uniq(self, *, suffix:Maybe[str]=None) -> Self: ...

    def de_uniq(self) -> Self: ...

    def diff_uuids(self, other:UUID) -> str: ...

class StrangMod_p(Protocol):

    def pop(self, *, top:bool=False) -> Strang_i: ...

    def push(self, *vals:PushVal) -> Strang_i: ...

    def root(self) -> Strang_i: ...

class StrangFormatter_p(Protocol):
    """ A string.Formatter with some Strang-specific methods """

    def format(self, format_string:str, /, *args:Any, **kwargs:Any) -> str: ... # noqa: ANN401

    def get_value(self, key:str, args:Any, kwargs:Any) -> str:  ...

    def convert_field(self, value:Any, conversion:Any) -> str: ...

    def expanded_str(self, data:Strang_i, *, stop:Maybe[int]=None) -> str: ...

@runtime_checkable
class Strang_p(StrangUUIDs_p, StrangMod_p, String_p, Protocol):
    """  """

    @classmethod
    def sections(cls) -> Sections_d: ...

    @classmethod
    def section(cls, arg:int|str) -> Sec_d: ...

    @override
    def __getitem__(self, i:ItemIndex) -> str: ... # type: ignore[override]

    @property
    def base(self) -> Self: ...

    @property
    def shape(self) -> tuple[int, ...]: ...

    @override
    def index(self, *sub:FindSlice, start:Maybe[int]=None, end:Maybe[int]=None) -> int: ... # type: ignore[override]

    @override
    def rindex(self, *sub:FindSlice, start:Maybe[int]=None, end:Maybe[int]=None) -> int: ... # type: ignore[override]

    def words(self, idx:SectionIndex, *, case:bool=False) -> list: ...

    def get(self, *args:SectionIndex|WordIndex) -> Any: ...  # noqa: ANN401

    def uuid(self) -> Maybe[UUID]: ...

##--| Interfaces

class Strang_i(Strang_p, Protocol):
    _processor  : ClassVar[PreProcessor_p]
    _formatter  : ClassVar[string.Formatter]
    _sections   : ClassVar[Sections_d]
    _typevar    : ClassVar[Maybe[type]]
    data        : Strang_d
    meta        : dict
