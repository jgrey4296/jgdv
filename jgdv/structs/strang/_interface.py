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
    from jgdv._abstract.pre_processable import PreProcessor_p
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

##--| Vars
FMT_PATTERN   : Final[Rx]                    = re.compile("^(h?)(t?)(p?)")
TYPE_RE       : Final[Rx]                    = re.compile(r"<(.+?)(?::(.+?))?>") # TODO name the groups
TYPE_ITER_RE  : Final[Rx]                    = re.compile(r"(<)(.+?)(?::(.+?))?(>)")
MARK_RE       : Final[Rx]                    = re.compile(r"(\$.+?\$)")
MARK_ITER_RE  : Final[Rx]                    = re.compile(r"(\$)(.+?)(\$)")
ARGS_RE       : Final[Rx]                    = re.compile(r"\[(.+?)\]$")
ARGS_CHARS    : Final[tuple[str, str, str]]  = "[", ",", "]"
CASE_DEFAULT  : Final[str]                   = "."
END_DEFAULT   : Final[str]                   = "::"
INST_K        : Final[str]                   = "instanced"
GEN_K         : Final[str]                   = "gen_uuid"
STRGET        : Final[Callable]              = str.__getitem__
STRCON        : Final[Callable]              = str.__contains__
UUID_WORD     : Final[str]                   = "<uuid>"

SEC_END_MSG   : Final[str]                   = "Only the last section has no end marker"

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

    @classmethod
    def idempotent(cls) -> set[str]:
        return {cls.module, cls.cls, cls.value, cls.fn}


##--|
type FullSlice     = slice[None, None, None]
type MSlice        = slice[Maybe[int], Maybe[int], Maybe[int]]
type SectionIndex  = str|int
type WordIndex     = tuple[SectionIndex, int]
type MarkIndex     = tuple[SectionIndex, StrangMarkAbstract_e]
type FindSlice     = str|StrangMarkAbstract_e|WordIndex|MarkIndex
type ItemIndex     = SectionIndex | FullSlice | MSlice | tuple[ItemIndex, ...]
type PushVal       = Maybe[str | StrangMarkAbstract_e | UUID]

HEAD_TYPES    = str|UUID|DefaultBodyMarks_e
BODY_TYPES    = str|UUID|DefaultBodyMarks_e
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
    idx       : int
    name      : Final[str]
    case      : Final[Maybe[str]]
    end       : Final[Maybe[str]]
    types     : Final[type|UnionType]
    marks     : Final[Maybe[type[StrangMarkAbstract_e]]]
    required  : Final[bool]

    def __init__(self, name:str, case:Maybe[str], end:Maybe[str], types:type|UnionType, marks:Maybe[type[StrangMarkAbstract_e]], required:bool=True, *, idx:int=-1) -> None:  # noqa: FBT001, FBT002, PLR0913
        assert(case is None or bool(case))
        assert(end is None or bool(end))
        self.idx       = idx
        self.name      = name.lower()
        self.case      = case
        self.end       = end
        self.types     = types
        self.marks     = marks
        self.required  = required

    def __contains__(self, other:type|StrangMarkAbstract_e) -> bool:
        match other:
            case type() as x:
                return issubclass(x, self.types)
            case UnionType() as xs:
                # Check its contained using its removal of duplicates
                return (xs | self.types) == self.types
            case StrangMarkAbstract_e() as x if self.marks:
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
    named  : Final[dict[str, int]]
    order  : Final[tuple[Sec_d, ...]]
    types  : type|UnionType

    def __init__(self, *sections:tuple|Sec_d) -> None:
        order : list[Sec_d] = []
        for i, sec in enumerate(sections):
            match sec:
                case Sec_d() as obj:
                    obj.idx = i
                    order.append(obj)
                case xs:
                    obj = Sec_d(*xs, idx=i)
                    order.append(obj)
        else:
            assert(all(x.end is not None for x in order[:-1])), SEC_END_MSG
            self.order = tuple(order)
            self.named = {x.name:i for i,x in  enumerate(self.order)}

    def __contains__(self, val:str) -> bool:
        return val in self.named

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

    - sections  : tuple[slice, ...]      - Section boundaries
    - sec_words : tuple[tuple[int, ...]] - lookup of (sec, word) -> WordIndex
    - words     : tuple[slice, ...]      - Word Slices
    - meta      : tuple[Maybe, ...]      - Flat word level meta data

    """
    __slots__ = ("args", "args_start", "flat_idx", "meta", "sec_words", "sections", "uuid", "words")
    args_start  : Maybe[int]
    args        : Maybe[tuple]
    sections    : tuple[slice, ...]
    sec_words   : tuple[tuple[int, ...], ...]
    flat_idx    : tuple[tuple[int, int], ...]
    words       : tuple[slice, ...]
    meta        : tuple[Maybe, ...]
    uuid        : Maybe[UUID]

    def __init__(self, uuid:Maybe[UUID]=None) -> None:
        self.args_start  = None
        self.args        = None
        self.sections    = ()
        self.sec_words   = ()
        self.words       = ()
        self.meta        = ()
        self.uuid        = uuid


##--| Default Section Specs
HEAD_SEC             : Final[Sec_d]       = Sec_d("head", CASE_DEFAULT, END_DEFAULT, BODY_TYPES, DefaultHeadMarks_e, True)  # noqa: FBT003
BODY_SEC             : Final[Sec_d]       = Sec_d("body", CASE_DEFAULT, None, HEAD_TYPES, DefaultBodyMarks_e, True)  # noqa: FBT003

CODEREF_HEAD_SEC     : Final[Sec_d]       = Sec_d("head",   CASE_DEFAULT, END_DEFAULT, HEAD_TYPES, CodeRefHeadMarks_e, False)  # noqa: FBT003
CODEREF_MODULE_SEC   : Final[Sec_d]       = Sec_d("module", CASE_DEFAULT, ":", HEAD_TYPES, DefaultBodyMarks_e, True)  # noqa: FBT003
CODEREF_VAL_SEC      : Final[Sec_d]       = Sec_d("value",  CASE_DEFAULT, None, HEAD_TYPES, CodeRefHeadMarks_e, True)  # noqa: FBT003

STRANG_DEFAULT_SECS  : Final[Sections_d]  = Sections_d(HEAD_SEC, BODY_SEC)
STRANG_ALT_SECS      : Final[Sections_d]  = Sections_d(
    Sec_d("head", CASE_DEFAULT, END_DEFAULT, HEAD_TYPES, DefaultHeadMarks_e, True),  # noqa: FBT003
    Sec_d("body", CASE_DEFAULT, None, BODY_TYPES, DefaultBodyMarks_e, True),  # noqa: FBT003
)
CODEREF_DEFAULT_SECS : Final[Sections_d] = Sections_d(CODEREF_HEAD_SEC, CODEREF_MODULE_SEC, CODEREF_VAL_SEC)
##--| Protocols

@runtime_checkable
class Importable_p(Protocol):
    """  """
    pass

class StrangUUIDs_p(Protocol):

    def to_uniq(self, *args:str) -> Self: ...

    def de_uniq(self) -> Self: ...

class StrangMod_p(Protocol):

    def pop(self, *, top:bool=False) -> Strang_p: ...

    def push(self, *vals:PushVal) -> Strang_p: ...

class StrangFormatter_p(Protocol):
    """ A string.Formatter with some Strang-specific methods """

    def format(self, format_string:str, /, *args:Any, **kwargs:Any) -> str: ... # noqa: ANN401

    def get_value(self, key:str, args:Any, kwargs:Any) -> str:  ...  # noqa: ANN401

    def convert_field(self, value:Any, conversion:Any) -> str: ...  # noqa: ANN401

    def expanded_str(self, data:Strang_p, *, stop:Maybe[int]=None) -> str: ...

@runtime_checkable
class Strang_p(StrangUUIDs_p, StrangMod_p, String_p, Protocol):
    """  """
    _processor  : ClassVar[PreProcessor_p]
    _formatter  : ClassVar[string.Formatter]
    _sections   : ClassVar[Sections_d]
    data        : Strang_d

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
