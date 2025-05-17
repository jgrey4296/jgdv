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
    _sections     : ClassVar          = API.StrangSections(API.HEAD_SEC, API.BODY_SEC)
    _typevar      : ClassVar          = None

    @classmethod
    def sections(cls) -> API.StrangSections:
        return cls._sections

    @classmethod
    def section(cls, arg:int|str) -> API.Sec_d:
        return cls._sections[arg]

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
        if self.is_uniq():
            return self[:,:]
        return str.__str__(self)

    def __repr__(self) -> str:
        body = str.__str__(self)
        cls  = self.__class__.__name__
        return f"<{cls}: {body}>"

    def __format__(self:API.Strang_i, spec:str) -> str:
        """ Basic formatting  """
        match spec:
            case "g":
                val = self[0,:]
                assert(isinstance(val, str))
                return val
            case "b":
                val = self[1,:]
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

        assert(isinstance(self, API.Strang_p))
        assert(isinstance(other, API.Strang_p))
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
        for s in range(len(self.sections())):
            for x in range(len(self.data.slices[s])):
                yield self.get(s, x)

    def __getitem__(self, args:Any) -> str: # type: ignore[override]  # noqa: ANN401, PLR0912, PLR0915, PLR0911
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
        """
        section_slice  : Maybe[int|slice] = None
        word_slice     : Maybe[int|slice] = None
        words          : list[str]
        idx            : int
        key            : str
        secs           : slice
        subs           : tuple[int|slice, ...]
        match args:
            case int() | slice() as x: # Normal str-like
                return API.STRGET(self, x)
            case str() as k: # whole section by name
                section_slice = self._sections.named[k]
            case [slice() as secs, slice(start=None, stop=None, step=None) as words]: # type: ignore[misc]
                # full expansion
                result = []
                sec_it = itz.islice(self.sections(), secs.start, secs.stop, secs.step)
                for s in sec_it:
                    for word in self.words(s.idx, case=True):
                        match word:
                            case UUID() as uid:
                                result.append(f"<uuid:{uid}>")
                            case x:
                                result.append(str(x))
                    else:
                        result.append(s.end or "")
                else:
                    return "".join(result)
            case [int() as idx, *_] if len(self._sections) < idx:
                msg = f"{self.__class__.__name__} has no section {idx}, only {len(self._sections)}"
                raise KeyError(msg)
            case [str() as key, *_] if key not in self._sections.named:
                msg = f"{self.__class__.__name__} has no section {key}"
                raise KeyError(msg)
            case [slice() as secs, *subs] if len(subs) != len(self.data.slices[secs]): # type: ignore[misc]
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
            case [str() as k]: # implicit SectionName-subslice
                section_slice = self._sections.named[k]
            case [int() as i, slice() as x]: # Section-subslice
                section_slice  = i
                word_slice     = x
            case [str() as k, slice() as x]: # SectionName-word
                section_slice  = self._sections.named[k]
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
                    result.append(API.STRGET(self, self.data.bounds[i]))
                    result.append(self._sections[i].end)
                else:
                    return "".join(result)
            case int() as sec, int() as w:
                return API.STRGET(self, self.data.slices[sec][w])
            case int() as sec, slice() as w:
                case   = self._sections[sec].case
                words  = []
                for x in self.data.slices[sec][w]:
                    words.append(API.STRGET(self, x))
                else:
                    return case.join(words)
            case None, slice() | int() as w:
                return API.STRGET(self, self.data.flat[w])
            case _:
                msg = "Slice Logic Failed"
                raise KeyError(msg, section_slice, word_slice)

    def __contains__(self:API.Strang_i, other:object) -> bool:
        """ test for conceptual containment of names
        other(a.b.c) ∈ self(a.b) ?
        ie: self < other
        """
        match other:
            case API.StrangMarkBase_e() as x:
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

    ##--| Access

    def get(self, *args:int) -> Any:  # noqa: ANN401
        match args:
            case int() as i:
                return self[i]
            case int() as i, int() as w:
                try:
                    val = self.data.meta[i][w] # type: ignore[index]
                except ValueError:
                    return self[i, w]
                else:
                    if val is None:
                        return self[i,w]
                    return val
            case int() as i, int() as w:
                return self[i, w]
            case x:
                raise TypeError(type(x))

    def words(self, idx:int|str, *, select:Maybe[slice]=None, case:bool=False) -> Iterator:
        """ Get the word values of a section.
        case=True adds the case in between values,
        select can be a slice that limits the returned values


        """
        count    : int
        gen      : Iterator
        section  : API.Sec_d
        section  = self.section(idx)
        count    = len(self.data.slices[section.idx])
        match select:
            case None:
                select = slice(None)
            case slice():
                pass

        gen       = itz.islice(range(count), select.start, select.stop, select.step)
        offbyone  = itz.tee(gen, 2)
        next(offbyone[1])

        for x,y in itz.zip_longest(*offbyone, fillvalue=None):
            yield self.get(section.idx, x)
            if case and y is not None:
                yield section.case


    ##--| UUIDs

    def uuid(self) -> Maybe[UUID]:
        match self.data.uuid:
            case None:
                return None
            case x,y:
                return self.get(x,y)

    def is_uniq(self) -> bool:
        """ utility method to test if this name refers to a name with a UUID """
        return self.data.uuid is not None

    def to_uniq(self, *, suffix:Maybe[str]=None) -> API.Strang_p:
        """ Generate a concrete instance of this name with a UUID appended,
        optionally can add a suffix

          ie: a.task.group::task.name..{prefix?}.$gen$.<UUID>
        """
        match suffix:
            case None:
                return self.push(uuid=True)
            case _:
                raise NotImplementedError()

    def de_uniq(self) -> API.Strang_i:
        """ return the strang up to, but not including, the uuid

        eg: 'group.a::q.w.e.<uuid>.t.y'.de_uniq() -> 'group.a::q.w.e'
        """
        assert(self.is_uniq()), "Can't de-uniq a non-uniq strang"
        raise NotImplementedError()

    ##--| Other

    def format(self, *args:Any, **kwargs:Any) -> str:  # noqa: ANN401
        """ Advanced formatting for strangs,
        using the cls._formatter
        """
        return self._formatter.format(self, *args, **kwargs)

    def canon(self) -> API.Strang_i:
        """ canonical name. no UUIDs
        eg: group::a.b.c.$gen$.<uuid>.c.d.e
        ->  group::a.b.c..c.d.e
        """
        raise NotImplementedError()

    def pop(self) -> API.Strang_i:
        """
        Strip off one marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c
        """
        raise NotImplementedError()

    def push(self, *args:Any, mark:Maybe[API.StrangMarkBase_e]=None, uuid:bool|UUID=False) -> API.Strang_i:
        """ create an extended strang with a mark or uuid appended

        eg: val = Strang('a.b.c::d.e.f')
        val.with(val.section(1).mark.head) -> 'a.b.c::d.e.f..$head$'
        val.with(uuid=True) -> 'a.b.c::d.e.f..<uuid>'
        val.with(uuid=uuid1()) -> 'a.b.c::d.e.f..<uuid:{val}>'
        """
        case   = self.section(-1).case
        dcase  = case * 2
        match mark, uuid:
            case None, None:
                raise NotImplementedError()
            case x, None:
                return Strang(f"{self}{dcase}${x}$")
                raise NotImplementedError()
            case None, x:
                raise NotImplementedError()
            case x, True:
                return cast("API.Strang_i", Strang(f"{self}{dcase}${x}${case}<uuid>"))
            case x, UUID() as y:
                return cast("API.Strang_i", Strang(f"{self}{dcase}${x}${case}<uuid:{y}>"))
            case x:
                raise TypeError(type(x))

    def root(self) -> API.Strang_i:
        """Pop off to the top marker """
        raise NotImplementedError()
