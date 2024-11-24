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
import types
import weakref
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Self,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

from jgdv._abstract.protocols import Buildable_p
from jgdv.structs.dkey.key import DKey, REDIRECT_SUFFIX, CONV_SEP, DKeyMark_e
from jgdv.structs.dkey.dkey_formatter import DKeyFormatter

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


FMT_PATTERN     : Final[re.Pattern]         = re.compile("[wdi]+")


def identity(x):
    return x

class DKeyFormatting_m:

    """ General formatting for dkeys """

    def __format__(self, spec:str) -> str:
        """
          Extends standard string format spec language:
            [[fill]align][sign][z][#][0][width][grouping_option][. precision][type]
            (https://docs.python.org/3/library/string.html#format-specification-mini-language)

          Using the # alt form to declare keys are wrapped.
          eg: for key = DKey('test'), ikey = DKey('test_')
          f'{key}'   -> 'test'
          f'{key:w}' -> '{test}'
          f'{key:i}  ->  'test_'
          f'{key:wi} -> '{test_}'

          f'{ikey:d} -> 'test'

        """
        if not bool(spec):
            return str(self)
        rem, wrap, direct = self._consume_format_params(spec)

        # format
        result = str(self)
        if direct:
            result = result.removesuffix(REDIRECT_SUFFIX)
        elif not result.endswith(REDIRECT_SUFFIX):
            result = f"{result}{REDIRECT_SUFFIX}"

        if wrap:
            result = "".join(["{", result, "}"])

        return format(result, rem)

    def _consume_format_params(self, spec:str) -> tuple(str, bool, bool, bool):
        """
          return (consumed, wrap, direct)
        """
        wrap     = 'w' in spec
        indirect = 'i' in spec
        direct   = 'd' in spec
        remaining = FMT_PATTERN.sub("", spec)
        assert(not (direct and indirect))
        return remaining, wrap, (direct or (not indirect))

    def format(self, fmt, *, spec=None, state=None) -> str:
        return DKeyFormatter.fmt(self, fmt, **(state or {}))

    def set_fmt_params(self, params:str) -> Self:
        match params:
            case None:
                pass
            case str() if bool(params):
                self._fmt_params = params
        return self

class DKeyExpansion_m:
    """ general expansion for dkeys """

    def redirect(self, *sources, multi=False, re_mark=None, fallback=None, **kwargs) -> list[DKey]:
        """
          Always returns a list of keys, even if the key is itself
        """
        match DKeyFormatter.redirect(self, sources=sources, fallback=fallback):
            case []:
                return [DKey(f"{self:d}", mark=re_mark)]
            case [*xs] if multi:
                return [DKey(x, mark=re_mark, implicit=True) for x in xs]
            case [x] if x is self:
                return [DKey(f"{self:d}", implicit=True)]
            case [x]:
                return [DKey(x, mark=re_mark, implicit=True)]
            case x:
                raise TypeError("bad redirection type", x, self)

    def expand(self, *sources, fallback=None, max=None, check=None, **kwargs) -> None|Any:
        logging.debug("DKey expansion for: %s", self)
        match DKeyFormatter.expand(self, sources=sources, fallback=fallback or self._fallback, max=max or self._max_expansions):
            case None:
                return None
            case DKey() as x if self._expansion_type is str:
                return f"{x:w}"
            case x:
                return x

    def _check_expansion(self, value, override=None):
        """ typecheck an expansion result """
        match override or self._typecheck:
            case x if x == Any:
                pass
            case types.GenericAlias() as x:
                if not isinstance(value, x.__origin__):
                    raise TypeError("Expansion value is not the correct container", x, value, self)
                if len((args:=x.__args__)) == 1 and not all(isinstance(y, args[0]) for y in value):
                    raise TypeError("Expansion value does not contain the correct value types", x, value, self)
            case types.UnionType() as x if not isinstance(value, x):
                raise TypeError("Expansion value does not match required type", x, value, self)
            case type() as x if not isinstance(value, x):
                raise TypeError("Expansion value does not match required type", x, value, self)
            case _:
                pass

    def _expansion_hook(self, value) -> Any:
        return value

    def _update_expansion_params(self, mark:DKeyMark_e) -> Self:
        """ pre-register expansion parameters """
        match self._mark:
            case None:
                pass
            case _ if self._expansion_type is not identity:
                pass
            case DKeyMark_e.PATH:
                self._expansion_type  = pl.Path
                self._typecheck = pl.Path
            case DKeyMark_e.STR:
                self._expansion_type  = str
                self._typecheck = str

        match self._expansion_type:
            case type() as x if issubclass(x, Buildable_p):
                self._typecheck = x
                self._expansion_type  = x.build

        return self
