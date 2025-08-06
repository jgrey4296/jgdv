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
from jgdv.mixins.annotate import SubAlias_m

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

# ##-- Generated Exports
__all__ = ( # noqa: RUF022

# -- Classes
"Strang",
)
# ##-- end Generated Exports

##-- logging
logging = logmod.getLogger(__name__)
logging.disabled = False
##-- end logging

##--|

class _StrangSlicer:
    """
        Access sections and words of a Strang,
        by name or index.

        val = Strang('a.b.c::d.e.f')
        val[:]          -> str(a.b.c::d.e.f)
        val[0,:]        -> a.b.c
        val[0]          -> a.b.c
        val[0,0]        -> a
        val[0,:-1]      -> a.b
        val['head']     -> a.b.c
        val['head', -1] -> c
        val[:,:,:-1]    -> a.b.c::d.e
    """
    __slots__ = ()

    def getitem(self, obj:API.Strang_p, args:API.ItemIndex) -> str: # type: ignore[override]
        words   : list[str]
        gotten  : str
        match self.discrim_getitem_args(obj, args):
            case Iterator() as sec_iter: # full expansion
                gotten = self.run_iterator(obj, sec_iter)
            case int()|slice() as section, None:
                bounds = obj.data.sections[section]
                gotten = API.STRGET(obj, bounds)
            case None, int() as flat:
                gotten = API.STRGET(obj, obj.data.words[flat])
            case None, slice() as flat:
                selection = obj.data.words[flat]
                gotten = API.STRGET(obj, slice(selection[0].start, selection[-1].stop, flat.step))
            case int() as section, int() as word:
                idx = obj.data.sec_words[section][word]
                gotten = API.STRGET(obj, obj.data.words[idx])
            case int() as section, slice() as word:
                case   = obj.section(section).case or ""
                words  = [API.STRGET(obj, obj.data.words[i]) for i in obj.data.sec_words[section][word]]
                gotten = case.join(words)
            case int()|slice() as basic:
                gotten = API.STRGET(obj, basic)
            case True, [*xs]:
                gotten = self.multi_slice(obj, xs)
            case _:
                raise KeyError(errors.UnkownSlice, args)
        ##--|
        return gotten

    def discrim_getitem_args(self, obj:API.Strang_p, args:API.ItemIndex) -> Iterator[API.Sec_d]|tuple[Maybe[API.ItemIndex], ...]|API.ItemIndex:
        result : Iterator|tuple|API.ItemIndex
        match args:
            case int() | slice() as x: # Normal str-like
                result = x
            case str() as k: # whole section by name
                result = obj.section(k).idx, None
            case [slice(), slice()] if not bool(obj.data.words):
                result = obj.data.sections[0]
            case [slice() as secs, slice(start=None, stop=None, step=None)]: # type: ignore[misc]
                sec_it = itz.islice(obj.sections(), secs.start, secs.stop, secs.step)
                result = sec_it
            case [int() as idx, *_] if len(obj.sections()) < idx:
                raise KeyError(errors.MissingSectionIndex.format(cls=obj.__class__.__name__,
                                                            idx=idx,
                                                            sections=len(obj.sections())))
            case [str() as key, *_] if key not in obj._sections.named:
                raise KeyError(errors.MissingSectionName.format(cls=obj.__class__.__name__,
                                                                key=key))
            case [slice() as secs, *subs] if secs.start is None and secs.stop is None:
                if len(subs) != len(obj.data.sec_words[secs]): # type: ignore[misc]
                    raise KeyError(errors.SliceMisMatch, len(subs), len(obj.data.sec_words[secs]))
                result = True, tuple(subs)
            case [str()|int() as i, slice()|int() as x]: # Section-word
                result = obj.section(i).idx, x
            case [None, slice()|int() as x]: # Flat slice
                result = None, x
            case x:
                raise TypeError(type(x), x)
        ##--|
        return result

    def run_iterator(self, obj:API.Strang_p, sec_iter:Iterator) -> str:
        sec : API.Sec_d
        result = []
        for sec in sec_iter:
            for word in obj.words(sec.idx, case=True):
                match word:
                    case UUID() as x:
                        result.append(f"<uuid:{x}>")
                    case x:
                        result.append(str(x))
            else:
                result.append(sec.end or "")
        else:
            return "".join(result)

    def multi_slice(self, obj:API.Strang_p, slices:Iterable) -> str:
        result = []
        for i,x in enumerate(slices):
            if x is None:
                continue
            result.append(obj[i,x])
            if (end:=obj.section(i).end) is not None:
                result.append(end)
        else:
            return "".join(result)
##--|

@Proto(API.Strang_p, mod_mro=False)
class Strang[*K](SubAlias_m, str, metaclass=StrangMeta, fresh_registry=True):
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
    _processor  : ClassVar                 = StrangBasicProcessor()
    _formatter  : ClassVar                 = StrangFormatter()
    _slicer     : ClassVar[_StrangSlicer]  = _StrangSlicer()
    _sections   : ClassVar                 = API.STRANG_ALT_SECS

    data        : API.Strang_d
    meta        : dict

    @classmethod
    def sections(cls) -> API.Sections_d:
        return cls._sections

    @classmethod
    def section(cls, arg:int|str) -> API.Sec_d:
        return cls._sections[arg]

    ##--|

    def __init__(self, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401, ARG002
        super().__init__()
        self.data  = API.Strang_d(kwargs.pop("uuid",None))

    ##--| dunders

    @override
    def __str__(self) -> str:
        """ Provides a fully expanded string

        eg: a.b.c::d.e.f..<uuid:{val}>
        """
        return format(self, "a+")

    @override
    def __repr__(self) -> str:
        body = self[:]
        cls  = self.__class__.__name__
        return f"<{cls}: {body}>"

    @override
    def __format__(self, spec:str) -> str:
        """ Basic formatting to get just a section

        additional format specs:
        a   : body, args, no expansion
        a-  : body, no args, no expansion
        a+  : body, args, expand
        a=  : no body, args
        u   : uuid

        """
        result : str
        match spec:
            case "a" | "a-" | "a+" if not self.data.args_start:
                result = self[:,:]
            case "a-":
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
                msg = "'u' format param"
                raise NotImplementedError(msg)
            case _:
                result = super().__format__(spec)

        return result

    @override
    def __hash__(self) -> int:
        return str.__hash__(str(self))

    @override
    def __lt__(self:API.Strang_p, other:object) -> bool:
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
                logging.debug("Failed on: %s : %s", x, y)
                return False

        return True

    @override
    def __le__(self:API.Strang_p, other:object) -> bool:
        match other:
            case API.Strang_p() as x:
                return hash(self) == hash(other) or (self < x)
            case str():
                return hash(self) == hash(other)
            case x:
                raise TypeError(type(x))

    @override
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

    @override
    def __ne__(self, other:object) -> bool:
        return not self == other

    @override
    def __iter__(self) -> Iterator:
        """ iterate over words """
        for sec in self.sections():
            yield from self.words(sec.idx)

    @override
    def __getitem__(self, args:API.ItemIndex) -> str: # type: ignore[override]
        """
        Access sections and words of a Strang,
        by name or index.

        val = Strang('a.b.c::d.e.f')
        val[:]          -> str(a.b.c::d.e.f)
        val[0,:]        -> a.b.c
        val[0]          -> a.b.c
        val[0,0]        -> a
        val[0,:-1]      -> a.b
        val['head']     -> a.b.c
        val['head', -1] -> c
        val[:,:,:-1]    -> a.b.c::d.e
        """
        return self._slicer.getitem(cast("API.Strang_p", self), args)

    def __getattr__(self, val:str) -> str:
        """ Enables using match statement for entire sections

        eg: case Strang(head=x, body=y):...

        """
        match val:
            case str() as x if x in self.sections():
                return self[val]
            case _:
                raise AttributeError(val)

    @override
    def __contains__(self:API.Strang_p, other:object) -> bool:
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

    def otherfunc(self):
        return 2

    @override
    def index(self, *sub:API.FindSlice, start:Maybe[int]=None, end:Maybe[int]=None) -> int: # type: ignore[override]
        """Extended str.index, to handle marks and word slices.

        :param sub: (:type:`~jgdv.structs.strang._interface.FindSlice`).
            The indices to slice.
        :param start: (:type:`~jgdv._abstract.types.Maybe[int]`) The start of the slice to cover.
        :param end:   (:type:`Maybe[int]`) The end of the slice to cover.

        :returns: The index of the char
        """
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

    @override
    def rindex(self, *sub:API.FindSlice, start:Maybe[int]=None, end:Maybe[int]=None) -> int: # type: ignore[override]
        """ Extended str.rindex, to handle marks and word slices """
        needle  : str
        word    : int
        match sub:
            case [API.StrangMarkAbstract_e() as mark]:
                word_idx  = max(-1, *(i for i,x in enumerate(self.data.meta) if x == mark), -1)
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
        """ Accessor to get internal data """
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
        except (ValueError, IndexError):
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
        sec_case : str
        section  = self.section(idx)
        sec_case = section.case or ""
        count    = len(self.data.sec_words[section.idx])
        if not bool(self.data.words):
            return
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
                yield sec_case

    def args(self) -> Maybe[tuple]:
        return self.data.args
    ##--| Modify

    def push(self, *new_words:API.PushVal, new_args:Maybe[list]=None, uuid:Maybe[UUID]=None) -> Self:
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

        for word in new_words:
            match word:
                case API.StrangMarkAbstract_e() as x if x in type(x).idempotent() and x in self:
                    pass
                case API.StrangMarkAbstract_e() as x if x in type(x).idempotent() and x in words:
                    pass
                case _:
                    words.append(self._processor.prep_word(word, fallback=mark))
        else:
            match new_args:
                case [] | None if uuid:
                    return self.__class__(*words, "[<uuid>]", uuid=uuid)
                case [] | None:
                    return self.__class__(*words)
                case [*xs]:
                    joined_args = ",".join(self._processor.prep_word(x) for x in xs)
                    return self.__class__(*words, f"[{joined_args}]", uuid=uuid)
                case y:
                    raise TypeError(type(y))

    def pop(self, *, top:bool=True)-> Self:
        """
        Strip off one marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c
        """
        next_mark  : int
        mark       : Maybe[API.StrangMarkAbstract_e]
        ##--|
        mark  = (self.section(-1).marks or API.DefaultBodyMarks_e).skip()
        assert(mark is not None)
        try:
            match top:
                case True:
                    next_mark = self.index(mark)
                case False:
                    next_mark = self.rindex(mark)
        except ValueError:
            return self
        else:
            return type(self)(self[:next_mark])

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
            case [*xs] if bool(self.args()):
                return self.__class__(f"{self:a-}", *xs, f"[{self:a=},<uuid>]")
            case [*xs]:
                return self.__class__(f"{self:a-}", *xs, "[<uuid>]")
            case x:
                raise TypeError(type(x), x)

    def de_uniq(self) -> Self:
        """ a.b.c::d.e.f[<uuid>] -> a.b.c::d.e.f

        """
        match self.uuid():
            case None:
                return self
            case _:
                return self.__class__(f"{self[:,:]}")

    ##--| Other

    @override
    def format(self, *args:Any, **kwargs:Any) -> str:
        """ Advanced formatting for strangs,
        using the cls._formatter
        """
        return self._formatter.format(self, *args, **kwargs)
