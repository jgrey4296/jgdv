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

# ##-- end 1st party imports

from . import _interface as API  # noqa: N812
from . import errors

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
                raise TypeError(errors.FormatterExpansionTypeFail, key)

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
                raise ValueError(errors.FormatterConversionUnknownSpec.format(spec=conversion))

    def expanded_str(self, value:Strang_i, *, stop:Maybe[int]=None) -> str:
        """ Create a str with generative marks replaced with generated values

        eg: a.b.c.<gen-uuid> -> a.b.c.<UUID:......>
        """
        raise NotImplementedError()

    def format_subval(self, value:Strang_i, val:str, *, no_expansion:bool=False) -> str:
        match val:
            case str():
                return val
            case UUID() if no_expansion:
                return "<uuid>"
            case UUID():
                return f"<uuid:{val}>"
            case _:
                raise TypeError(errors.FormatterUnkownBodyType, val)

    def canon(self, obj:Strang_i) -> Strang_i:
        """ canonical name. no UUIDs
        eg: group::a.b.c.$gen$.<uuid>.c.d.e
        ->  group::a.b.c..c.d.e
        """

        def filter_fn(x:Any) -> bool:  # noqa: ANN401
            return isinstance(x, UUID)

        result : list[str] = []
        for sec in obj.sections():
            for i, word in enumerate(obj.words(sec.idx)):
                if filter_fn(word):
                    result.append(word)
                else:
                    result.append(obj[sec.idx, i])

        else:
            return obj.__class__("".join(result))

    def pop(self:Strang_i, *, top:bool=False) -> Strang_i:
        """
        Strip off one marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c
        """
        raise NotImplementedError()

    def de_uniq(self:Strang_i) -> Strang_i:
        """ return the strang up to, but not including, the first instance mark.

        eg: 'group.a::q.w.e.<uuid>.t.<uuid>.y'.de_uniq() -> 'group.a::q.w.e'
        """
        raise NotImplementedError()

    def root(self:Strang_i) -> Strang_i:
        """Pop off to the top marker """
        return self.pop(top=True)
