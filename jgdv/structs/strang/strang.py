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
from jgdv.mixins.annotate import SubAnnotate_m

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
from collections.abc import Iterator

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Callable, Generator
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
class Strang(SubAnnotate_m, str, metaclass=StrangMeta):
    """ A Structured String Baseclass.

    A Normal str, but is parsed on construction to extract and validate
    certain form and metadata.

    The Form of a Strang is::

        {group}{sep}{body}
        eg: group.val::body.val

    Body objs can be marks (Strang.bmark_e), and UUID's as well as str's

    strang[x] and strang[x:y] are changed to allow structured access::

        val         = Strang("a.b.c::d.e.f")
        val[0] # a.b.c
        val[1] # d.e.f

    """
    __slots__       = ("data", "meta")
    __match_args__  = ("head", "body")

    ##--|
    _processor  : ClassVar  = StrangBasicProcessor()
    _formatter  : ClassVar  = StrangFormatter()
    _sections   : ClassVar  = API.STRANG_ALT_SECS
    _typevar    : ClassVar  = None

    data        : API.Strang_d
    meta        : dict

    @classmethod
    def sections(cls) -> API.Sections_d:
        return cls._sections

    @classmethod
    def section(cls, arg:int|str) -> API.Sec_d:
        return cls._sections[arg]

    @classmethod
    def __init_subclass__[T:API.Strang_i](cls:type[T], *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        StrangMeta.register(cls)

    ##--|

    def __init__(self:API.Strang_i, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401, ARG002
        super().__init__()
        self.meta  = dict(kwargs)
        self.data  = API.Strang_d()

   ##--| dunders

    def __str__(self) -> str:
        """ Provides a fully expanded string

        eg: a.b.c::d.e.f..<uuid:{val}>
        """
        return format(self, "a+")

    def __repr__(self) -> str:
        body = self[:]
        cls  = self.__class__.__name__
        return f"<{cls}: {body}>"

    def __format__(self:API.Strang_i, spec:str) -> str:
        """ Basic formatting to get just a section """
        result : str
        match spec:
            case "a" | "a-" | "a+" if not self.data.args_start:
                result = self[:,:]
            case "a-": # No Args, No Expansion
                result = self[:self.data.args_start]
            case "a+" if self.data.args_start: # Full Args
                result = f"{self[:,:]}[<uuid:{self.uuid()}>]"
            case "a" if self.data.args_start: # Simple Args
                result = self[:]
            case "a=" if self.data.args_start: # only args
                result = self[self.data.args_start+1:-1]
            case "a=":
                result = ""
            case "u" if self.data.uuid:
                val = self.data.uuid
                result = f"<uuid:{val}>"
            case "u":
                raise ValueError()
            case _:
                result = super().__format__(spec)

        return result

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
        match other:
            case Strang() as x if self.uuid() and x.uuid():
                return hash(self) == hash(other)
            case UUID() as x:
                return self.uuid() == x
            case x if self.uuid():
                h_other = hash(x)
                return hash(self) == h_other or hash(self[:]) == h_other
            case x:
                return hash(self) == hash(x)

    def __ne__(self, other:object) -> bool:
        return not self == other

    def __iter__(self) -> Iterator:
        """ iterate over words """
        for sec in self.sections():
            yield from self.words(sec.idx)


    def __getitem__(self, args:API.ItemIndex) -> str: # type: ignore[override]  # noqa: PLR0912, PLR0911
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
        sec : API.Sec_d
        match self._discrim_getitem_args(args):
            case Iterator() as sec_iter: # full expansion
                result = []
                for sec in sec_iter:
                    for word in self.words(sec.idx, case=True):
                        match word:
                            case UUID() as x:
                                result.append(f"<uuid:{x}>")
                            case x:
                                result.append(str(x))
                    else:
                        result.append(sec.end or "")
                else:
                    return "".join(result)

            case int()|slice() as section, None:
                bounds = self.data.sections[section]
                return API.STRGET(self, bounds)
            case None, int() as flat:
                return API.STRGET(self, self.data.words[flat])
            case None, slice() as flat:
                selection = self.data.words[flat]
                return API.STRGET(self, slice(selection[0].start, selection[-1].stop, flat.step))
            case int() as section, int() as word:
                idx = self.data.sec_words[section][word]
                return API.STRGET(self, self.data.words[idx])
            case int() as section, slice() as word:
                case   = self.section(section).case or ""
                words  : list[str] = [API.STRGET(self, self.data.words[i]) for i in self.data.sec_words[section][word]]
                return case.join(words)
            case int()|slice() as basic:
                return API.STRGET(self, basic)
            case _:
                raise KeyError(errors.UnkownSlice, args)

    def _discrim_getitem_args(self, args:API.ItemIndex) -> Iterator[API.Sec_d]|tuple[Maybe[API.ItemIndex], ...]|API.ItemIndex:
        match args:
            case int() | slice() as x: # Normal str-like
                return x
            case str() as k: # whole section by name
                return self.section(k).idx, None
            case [slice() as secs, slice(start=None, stop=None, step=None)]: # type: ignore[misc]
                sec_it = itz.islice(self.sections(), secs.start, secs.stop, secs.step)
                return sec_it
            case [int() as idx, *_] if len(self.sections()) < idx:
                raise KeyError(errors.MissingSectionIndex.format(cls=self.__class__.__name__,
                                                            idx=idx,
                                                            sections=len(self.sections())))
            case [str() as key, *_] if key not in self._sections.named:
                raise KeyError(errors.MissingSectionName.format(cls=self.__class__.__name__,
                                                                key=key))
            case [slice() as secs, *subs] if len(subs) != len(self.data.sec_words[secs]): # type: ignore[misc]
                raise KeyError(errors.SliceMisMatch, len(subs), len(self.data.sec_words[secs]))
            case [str()|int() as i, slice()|int() as x]: # Section-word
                return self.section(i).idx, x
            case [None, slice()|int() as x]: # Flat slice
                return None, x
            case x:
                raise TypeError(type(x), x)

    def __getattr__(self, val:str) -> str:
        """ Enables using match statement for entire sections

        eg: case Strang(head=x, body=y):...

        """
        match val:
            case str() as x if x in self.sections():
                return self[val]
            case _:
                raise AttributeError(val)

    def __contains__(self:API.Strang_i, other:object) -> bool:
        """ test for conceptual containment of names
        other(a.b.c) ∈ self(a.b) ?
        ie: self < other
        """
        match other:
            case API.StrangMarkAbstract_e() as x:
                return x in self.data.meta
            case UUID() as x:
                return (x == self.uuid() or x in self.data.meta)
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
        return tuple(len(x) for x in self.data.sec_words)

    ##--| Access

    def index(self, *sub:API.FindSlice, start:Maybe[int]=None, end:Maybe[int]=None) -> int: # type: ignore[override]
        """ Extended str.index, to handle marks and word slices """
        needle  : str|API.StrangMarkAbstract_e
        word    : int
        match sub:
            case [API.StrangMarkAbstract_e() as mark]:
                idx = self.data.meta.index(mark)
                return self.data.words[idx].start
            case ["", *_]:
                raise ValueError(errors.IndexOfEmptyStr, sub)
            case [str() as needle]:
                pass
            case [str()|int() as sec, int() as word]:
                needle = self.get(sec, word)
            case _:
                raise TypeError(type(sub), sub)

        match needle:
            case API.StrangMarkAbstract_e():
                return self.index(needle, start=start, end=end)
            case _:
                return str.index(self, needle, start, end)

    def rindex(self, *sub:API.FindSlice, start:Maybe[int]=None, end:Maybe[int]=None) -> int: # type: ignore[override]
        """ Extended str.rindex, to handle marks and word slices """
        needle  : str
        word    : int
        match sub:
            case [API.StrangMarkAbstract_e() as mark]:
                word_idx  = max(-1, *(i for i,x in enumerate(self.data.meta) if x == mark))
                if word_idx == -1:
                    raise ValueError(mark)
                return self.data.words[word_idx].start
            case ["", *_]:
                raise ValueError(errors.IndexOfEmptyStr, sub)
            case [str() as needle]:
                pass
            case [int()|str() as sec, int() as word]:
                idx = self.section(sec).idx
                word_idx = self.data.sec_words[idx][word]
                return self.data.words[word_idx].start
            case x:
                raise ValueError(x)

        return str.rindex(self, needle, start, end)

    def get(self, *args:API.SectionIndex|API.WordIndex) -> Any:  # noqa: ANN401
        x     : Any
        sec   : int
        word  : int
        idx   : int
        match args:
            case [str() | int() as i]:
                return self[i]
            case [int() as sec, int() as word]:
                idx = self.data.sec_words[sec][word]
            case [str() as k, int() as word]:
                sec = self.section(k).idx
                idx = self.data.sec_words[sec][word]
            case x:
                raise KeyError(x)

        try:
            val = self.data.meta[idx] # type: ignore[index]
        except ValueError:
            return self[sec, word]
        else:
            match val:
                case None:
                    return self[sec,word]
                case _:
                    return val

    def words(self, idx:int|str, *, select:Maybe[slice]=None, case:bool=False) -> Iterator:
        """ Get the word values of a section.
        case=True adds the case in between values,
        select can be a slice that limits the returned values

        """
        count    : int
        gen      : Iterator
        section  : API.Sec_d
        section  = self.section(idx)
        count    = len(self.data.sec_words[section.idx])
        if count == 0:
            return

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

    ##--| Modify

    def push(self, *args:API.PushVal) -> Self:
        """ extend a strang with values

        Pushed onto the last section, with a section.marks.skip() mark first

        eg: val = Strang('a.b.c::d.e.f')
        val.push(val.section(1).mark.head) -> 'a.b.c::d.e.f..$head$'
        val.push(uuid=True) -> 'a.b.c::d.e.f..<uuid>'
        val.push(uuid=uuid1()) -> 'a.b.c::d.e.f..<uuid:{val}>'
        """
        word  : API.PushVal
        x     : API.PushVal
        words  = [format(self, "a-")]
        marks  = self.section(-1).marks or API.DefaultBodyMarks_e
        match marks.skip():
            case API.StrangMarkAbstract_e() as x:
                mark = x.value
                words.append(x.value)
            case _:
                raise ValueError(errors.NoSkipMark)

        for word in args:
            match word:
                case API.StrangMarkAbstract_e() as x if x in type(x).idempotent() and x in self:
                    pass
                case API.StrangMarkAbstract_e() as x if x in type(x).idempotent() and x in words:
                    pass
                case API.StrangMarkAbstract_e() as x if x in type(x).idempotent() and x in self:
                    words.append(x.value)
                case str() as x:
                    words.append(x)
                case UUID() as x:
                    words.append(f"<uuid:{x}>")
                case None:
                    words.append(mark)
                case x:
                    words.append(str(x))
        else:
            return self.__class__(*words)

    def pop(self, *, top:bool=True)-> API.Strang_i:
        """
        Strip off one marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c
        """
        mark = (self.section(-1).marks or API.DefaultBodyMarks_e).skip()
        assert(mark is not None)
        try:
            match top:
                case True:
                    next_mark = self.index(mark)
                case False:
                    next_mark = self.rindex(mark)
        except ValueError:
            return cast("API.Strang_i", self)
        else:
            return cast("API.Strang_i", Strang(self[:next_mark]))

    def mark(self, mark:str|API.StrangMarkAbstract_e) -> Self:
        """ Add a given mark if it is last section appropriate  """
        appropriate = self.section(-1).marks
        assert(appropriate is not None)
        match mark:
            case str() as x if x in appropriate:
                return self.push(appropriate(x))
            case API.StrangMarkAbstract_e() as x if x in appropriate:
                return self.push(x)
            case x:
                raise ValueError(x)

    ##--| UUIDs

    def uuid(self) -> Maybe[UUID]:
        return self.data.uuid

    def to_uniq(self, *args:str) -> Self:
        """ Generate a concrete instance of this name with a UUID prepended,

          ie: a.task.group::task.name..{prefix?}.$gen$.<UUID>
        """
        match args:
            case [] if self.uuid():
                return self
            case [] if bool(curr:=f"{self:a=}"):
                return self.__class__(f"{self:a-}[{curr},<uuid>]")
            case []:
                return self.__class__(f"{self:a-}[<uuid>]")
            case [*xs, x] if bool(curr:=f"{self:a=}"):
                return self.__class__(f"{self:a-}", *xs, f"{x}[<uuid>]")
            case [x]:
                return self.__class__(f"{self:a-}", f"{x}[<uuid>]")
            case x:
                raise TypeError(type(x))

    def de_uniq(self) -> Self:
        """ a.b.c::d.e.f[<uuid>] -> a.b.c::d.e.f

        """
        match self.uuid():
            case None:
                return self
            case _:
                return self.__class__(f"{self[:,:]}")

    ##--| Other

    def format(self, *args:Any, **kwargs:Any) -> str:  # noqa: ANN401
        """ Advanced formatting for strangs,
        using the cls._formatter
        """
        return self._formatter.format(self, *args, **kwargs)
