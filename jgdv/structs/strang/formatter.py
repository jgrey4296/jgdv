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
import string
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import sh

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Mixin
from jgdv._abstract.protocols import SpecStruct_p
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from . import _interface as API  # noqa: N812

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
    from jgdv import Maybe
    from jgdv import Ident, FmtStr, Rx, RxStr, Func
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from ._interface import Strang_i

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__file__)
##-- end logging

class StrangFormatter(string.Formatter):
    """
      An Expander/Formatter to extend string formatting with options useful for dkey's
      and doot specs/state.

    """

    def format(self, key:str, /, *args:Any, **kwargs:Any) -> str: # noqa: ANN401
        """ format keys as strings """
        match key:
            case str():
                fmt = key
            case pl.Path():
                raise NotImplementedError()
            case _:
                msg = "Unrecognized expansion type"
                raise TypeError(msg, key)

        result = self.vformat(fmt, args, kwargs)
        return result

    def get_value(self, key:int|str, args:Sequence[Any], kwargs:Any) -> str: # noqa: ANN401
        """ lowest level handling of keys being expanded """
        # This handles when the key is something like '1968'
        if isinstance(key, int) and 0 <= key <= len(args):
            return args[key]

        return kwargs.get(key, key)

    def convert_field(self, value:str, conversion:Maybe[str]) -> str:
        # do any conversion on the resulting object
        match conversion:
            case None:
                return value
            case "s" | "p" | "R" | "c" | "t":
                return str(value)
            case "r":
                return repr(value)
            case "a":
                return ascii(value)
            case _:
                msg = f"Unknown conversion specifier {conversion!s}"
                raise ValueError(msg)

    def expanded_str(self, value:Strang_i, *, stop:Maybe[int]=None) -> str:
        """ Create a str with generative marks replaced with generated values

        eg: a.b.c.<gen-uuid> -> a.b.c.<UUID:......>
        """
        return self.join_sections(value)

    def format_subval(self, value:Strang_i, val:str, *, no_expansion:bool=False) -> str:
        match val:
            case str():
                return val
            case UUID() if no_expansion:
                return "<uuid>"
            case UUID():
                return f"<uuid:{val}>"
            case _:
                msg = "Unknown body type"
                raise TypeError(msg, val)

    def join_sections(self, obj:Strang_i) -> str:
        flat = []
        for i, sec in enumerate(obj._sections.sections):
            flat.append(obj[i,:])
            flat.append(sec.end)
        else:
            return "".join(flat)


    def canon(self, obj:Strang_i) -> Strang_i:
        """ canonical name. no UUIDs
        eg: group::a.b.c.$gen$.<uuid>.c.d.e
        ->  group::a.b.c..c.d.e
        """

        def _filter_fn(x:API.BODY_TYPES) -> bool:
            return (isinstance(x, UUID)
                    or x == self.bmark_e.gen # type: ignore
                    )

        group      = cast("str", obj[0:])
        canon_body = self._subjoin(self.body(reject=_filter_fn))

        return self.__class__(f"{group}{self._separator}{canon_body}") # type: ignore

    def pop(self:Strang_i, *, top:bool=False) -> Strang_i:
        """
        Strip off one marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c
        """
        end_id = self._mark_idx[0 if top else 1]
        return cast("Strang_i", self[2:end_id])

    def push(self:Strang_i, *vals:str) -> Strang_i:
        """ Add a root marker if the last element isn't already a root marker
        eg: group::a.b.c => group.a.b.c.
        (note the trailing '.')
        """
        return self.__class__(self._subjoin(str(x) for x in [self[2:], # type: ignore
                                                             self.bmark_e.mark, # type: ignore
                                                             *vals,
                                                             ] if x is not None))

    def to_uniq(self:Strang_i, *, suffix:Maybe[str]=None) -> Strang_i:
        """ Generate a concrete instance of this name with a UUID appended,
        optionally can add a suffix

          ie: a.task.group::task.name..{prefix?}.$gen$.<UUID>
        """
        match self[1:-1]:
            case UUID():
                return self
            case _:
                return self.push(self.bmark_e.gen, "<uuid>", suffix) # type: ignore

    def de_uniq(self:Strang_i) -> Strang_i:
        """ return the strang up to, but not including, the first instance mark.

        eg: 'group.a::q.w.e.<uuid>.t.<uuid>.y'.de_uniq() -> 'group.a::q.w.e'
        """
        if API.GEN_K not in self.metadata:
            return self
        return cast("Strang_i", self[2:self.metadata.get(API.INST_K, None)]).pop()

    def with_head(self:Strang_i) -> Strang_i:
        """ generate a canonical group/completion task name for this name
        eg: (concrete) group::simple.task..$gen$.<UUID> ->  group::simple.task..$gen$.<UUID>..$group$
        eg: (abstract) group::simple.task. -> group::simple.task..$head$

        """
        if self.is_head():
            return self

        return self.push(self.bmark_e.head) # type: ignore

    def root(self:Strang_i) -> Strang_i:
        """Pop off to the top marker """
        return self.pop(top=True)
