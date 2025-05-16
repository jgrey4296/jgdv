 #!/usr/bin/env python3
"""

"""
# ruff: noqa: B019, PLR2004
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import functools as ftz
import importlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from uuid import uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Mixin, Proto

# ##-- end 1st party imports

from .processor import StrangBasicProcessor
from .formatter import StrangFormatter
from . import errors
from . import _interface as API # noqa: N812
from ._meta import StrangMeta

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
import enum
from uuid import UUID

if TYPE_CHECKING:
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
logging.disabled = False
##-- end logging

type BodyMark  = type[enum.StrEnum]
type GroupMark = type[enum.StrEnum] | type[int]

##--|

@Proto(API.Strang_i, mod_mro=False)
class Strang(str, metaclass=StrangMeta):
    """ A Structured String Baseclass.

    A Normal str, but is parsed on construction to extract and validate
    certain form and metadata.

    The Form of a Strang is::

        {group}{sep}{body}
        eg: group.val::body.val

    Body objs can be marks (Strang.bmark_e), and UUID's as well as str's

    strang[x] and strang[x:y] are changed to allow structured access::

        val = Strang("a.b.c::d.e.f")
        val[0] # a.b.c
        val[1] # d.e.f

    """
    __slots__ = ("data", "meta")
    ##--|
    _processor    : ClassVar          = StrangBasicProcessor()
    _formatter    : ClassVar          = StrangFormatter()
    _sections     : ClassVar          = API.StrangSections(
        ("head", API.WORD_DEFAULT, API.SEP_DEFAULT, API.BODY_TYPES | API.Strang_p, API.StrangMarker_e, True),
        ("body", API.WORD_DEFAULT, None, API.GROUP_TYPES, API.StrangMarker_e, True),
    )
    _typevar      : ClassVar          = None


    @classmethod
    def section(cls, arg:Maybe[int|str]=None) -> API.StrangSection:
        if arg:
            return cls._sections[arg]
        return cls._sections

    @classmethod
    def __init_subclass__[T:API.Strang_i](cls:type[T], *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        StrangMeta.register(cls)

    ##--|

    def __init__(self:API.Strang_i, *_:Any, **kwargs:Any) -> None:  # noqa: ANN401
        super().__init__()
        self.meta          = dict(kwargs)
        self.data         = API.Strang_d()

    ##--| dunders

    def __str__(self) -> str:
        if API.INST_K in self.meta:
            raise TypeError("Building a string of a strang with a UUID")
        return str.__str__(self)

    def __repr__(self) -> str:
        body = str(self)
        cls  = self.__class__.__name__
        return f"<{cls}: {body}>"

    def __format__(self:API.Strang_i, spec:str) -> str:
        """ Basic formatting  """
        match spec:
            case "g":
                val = self[0:]
                assert(isinstance(val, str))
                return val
            case "b":
                val = self[1:]
                assert(isinstance(val, str))
                return val
            case _:
                return super().__format__(spec)

    def __hash__(self) -> int:
        return str.__hash__(str(self))

    def __lt__(self:API.Strang_i, other:object) -> bool:
        match other:
            case API.Strang_p() | str() as x if not len(self) < len(x):
                logging.debug("Length mismatch")
                return False
            case API.Strang_p():
                pass
            case x:
                logging.debug("Type failure")
                return False

        if not self[0,:] == other[0,:]:
            logging.debug("head mismatch")
            return False

        for x,y in zip(self.words(1), other.words(1), strict=False):
            if x != y:
                logging.debug("Faileid on: %s : %s", x, y)
                return False

        return True

    def __le__(self:API.Strang_i, other:object) -> bool:
        match other:
            case API.Strang_p() as x:
                return hash(self) == hash(other) or (self < x) # type: ignore
            case str():
                return hash(self) == hash(other)
            case x:
                raise TypeError(type(x))

    def __eq__(self, other:object) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other:object) -> bool:
        return not self == other

    def __iter__[T:API.Strang_i](self:T) -> Iterator:
        """ iterate over words """
        for s in range(len(self.section())):
            for x in range(len(self.data.slices[s])):
                yield self.get(s, x)

    def __getitem__(self, args:int|slice) -> str|API.Strang_i: # type: ignore[override]  # noqa: PLR0912
        """
        Access sections and words of a Strang,
        by name or index.

        val = Strang('a.b.c::d.e.f')
        val[:]          -> (val2:=a.b.c::d.e.f) is not val
        val[0,:]        -> a.b.c
        val[0]          -> a.b.c
        val[0,0]        -> a
        val[0,:-1]      -> a.b
        val['head']     -> a.b.c
        val['head', -1] -> c

        val[1,:]        -> d.e.f
        val[1]          -> d.e.f
        val[1,1:]       -> e.f
        val['body']     -> d.e.f
        """
        section_slice  : Maybe[int|slice] = None
        word_slice     : Maybe[int|slice] = None
        idx            : int
        key            : str
        secs           : slice
        subs           : tuple[int|slice, ...]
        match args:
            case int() | slice() as x: # Normal str-like
                return API.STRGET(self, x)
            case [int() as idx, *_] if len(self._sections) < idx:
                msg = f"{self.__class__.__name__} has no section {idx}, only {len(self._sections)}"
                raise KeyError(msg)
            case [str() as key, *_] if key not in self._sections.named:
                msg = f"{self.__class__.__name__} has no section {key}"
                raise KeyError(msg)
            case [slice() as secs, *subs] if len(subs) != len(self.data.slices[secs]):
                msg = "Mismatch between section slices and word slices"
                raise KeyError(msg)
            case [int() as i]:
                section_slice = i
            case [str() as k]:
                section_slice = self._sections.named[k]
            case [int() as i, int() as x]: # Section-word
                section_slice  = i
                word_slice     = x
            case [str() as k, int() as x]: # SectionName-word
                section_slice  = self._sections.named[k]
                word_slice     = x
            case [int() as i]: # implicit Section-subslice
                section_slice = i
            case [str() as k]: # implicit Section-subslice
                section_slice = self._sections.named[k]
            case [int() as i, slice() as x]: # Section-subslice
                section_slice  = i
                word_slice     = x
            case [str() as k, slice() as x]: # SectionName-word
                section_slice = self._sections.named[k]
                word_slice     = x
            case x:
                raise TypeError(type(x), x)

        match section_slice, word_slice:
            case int() as sec, None:
                return API.STRGET(self, self.data.bounds[sec])
            case slice() as sec, None:
                idxs = range(len(self._sections))
                result = []
                for i in itz.islice(idxs, sec.start, sec.stop, sec.step):
                    result.append(self.data.bounds[i])
                    result.append(self._sections[i].end)
                else:
                    return "".join()
            case int() as sec, int() as w:
                return API.STRGET(self, self.data.slices[sec][w])
            case int() as sec, slice() as w:
                case   = self._sections[sec].case
                words  = [API.STRGET(self, x) for x in self.data.slices[sec][w]]
                return case.join(words)
            case None, slice() | int() as w:
                return API.STRGET(self, self.data.flat[w])
            case _:
                msg = "Slice Logic Failed"
                raise ValueError(msg, section_slice, word_slice)

    def __contains__(self:API.Strang_i, other:object) -> bool:
        """ test for conceptual containment of names
        other(a.b.c) ∈ self(a.b) ?
        ie: self < other
        """
        match other:
            case enum.EnumMeta() as x:
                return any(x in y for y in self.data.meta if y is not None)
            case UUID() as uid if self.data.meta is None:
                return False
            case UUID() as uid:
                body_meta = self.data.meta[1]
                assert(body_meta is not None)
                return uid in body_meta
            case str() as needle:
                return API.STRCON(self, needle)
            case _:
                return False

    ##--| Properties

    @property
    def base(self) -> Self:
        return self

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(len(x) for x in self.data.slices)

    ##--| Rest

    def get(self, *args:int) -> Any:
        match args:
            case int() as i:
                return self[i]
            case int() as i, int() as w if bool(sm:=self.data.meta[i]) and sm[w] is not None:
                return self.data.meta[i][w]
            case int() as i, int() as w:
                return self[i, w]
            case x:
                raise TypeError(type(x))

    def words(self, group:int|str) -> list:
        match group:
            case int():
                pass
            case str() as k:
                group = self.sections().named[k]

        return [self.get(group, x) for x in range(len(self.data.slices[group]))]

    def body(self, *, reject:Maybe[Callable]=None, no_expansion:bool=False) -> list[str]:
        """ Get the body, as a list of str's,
        with values filtered out if a rejection fn is used
        """

        return [str.__getitem__(self, x) for x in self.data.slices[1]]

    def uuid(self) -> Maybe[UUID]:
        raise NotImplementedError()

    def is_uniq(self:API.Strang_i) -> bool:
        """ utility method to test if this name refers to a name with a UUID """
        raise NotImplementedError()

    def is_head(self:API.Strang_i) -> bool:
        # TODO shift to doot
        raise NotImplementedError()

    def format(self, *args:Any, **kwargs:Any) -> str:  # noqa: ANN401
        """ Advanced formatting for strangs,
        using the cls._formatter
        """
        return self._formatter.format(self, *args, **kwargs)

    def canon(self:API.Strang_i) -> API.Strang_i:
        """ canonical name. no UUIDs
        eg: group::a.b.c.$gen$.<uuid>.c.d.e
        ->  group::a.b.c..c.d.e
        """
        raise NotImplementedError()

    def pop(self:API.Strang_i, *, top:bool=False) -> API.Strang_p:
        """
        Strip off one marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c
        """
        raise NotImplementedError()

    def push(self:API.Strang_i, *vals:str) -> API.Strang_i:
        """ Add a root marker if the last element isn't already a root marker
        eg: group::a.b.c => group.a.b.c.
        (note the trailing '.')
        """
        raise NotImplementedError()

    def to_uniq(self:API.Strang_i, *, suffix:Maybe[str]=None) -> API.Strang_i:
        """ Generate a concrete instance of this name with a UUID appended,
        optionally can add a suffix

          ie: a.task.group::task.name..{prefix?}.$gen$.<UUID>
        """
        raise NotImplementedError()

    def de_uniq(self:API.Strang_i) -> API.Strang_i:
        """ return the strang up to, but not including, the first instance mark.

        eg: 'group.a::q.w.e.<uuid>.t.<uuid>.y'.de_uniq() -> 'group.a::q.w.e'
        """
        raise NotImplementedError()

    def with_head(self:API.Strang_i) -> API.Strang_i:
        """ generate a canonical group/completion task name for this name
        eg: (concrete) group::simple.task..$gen$.<UUID> ->  group::simple.task..$gen$.<UUID>..$group$
        eg: (abstract) group::simple.task. -> group::simple.task..$head$

        """
        raise NotImplementedError()

    def root(self:API.Strang_i) -> API.Strang_i:
        """Pop off to the top marker """
        raise NotImplementedError()
