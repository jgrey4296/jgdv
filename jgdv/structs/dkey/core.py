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
    Self,
    Sequence,
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

# ##-- 1st party imports
from jgdv._abstract.protocols import Buildable_p, Key_p, SpecStruct_p
from jgdv.structs.code_ref import CodeReference
from jgdv.structs.dkey.base import DKeyBase
from jgdv.structs.dkey.dkey import CONV_SEP, REDIRECT_SUFFIX, DKey, DKeyMark_e
from jgdv.structs.dkey.formatter import DKeyFormatter
from jgdv.structs.dkey.mixins import DKeyExpansion_m, DKeyFormatting_m, identity

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class SingleDKey(DKeyBase, mark=DKeyMark_e.FREE):
    """
      A Single key with no extras.
      ie: {x}. not {x}{y}, or {x}.blah.
    """

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

class MultiDKey(DKeyBase, mark=DKeyMark_e.MULTI, multi=True):
    """
      Multi keys allow contain 1+ explicit subkeys
    """

    def __init__(self, data:str|pl.Path, *, mark:DKeyMark_e=None, **kwargs):
        super().__init__(data, mark=mark, **kwargs)
        has_text, s_keys = DKeyFormatter.Parse(data)
        self._has_text   = has_text
        self._subkeys    = s_keys
        self._anon    = self.format("", state={key.key : "{}" for key in s_keys})

    def __format__(self, spec:str):
        """
          Multi keys have no special formatting

          ... except stripping dkey particular format specs out of the result?
        """
        rem, wrap, direct = self._consume_format_params(spec)
        return format(str(self), rem)

    def keys(self) -> list[Key_p]:
        return [DKey(key.key, fmt=key.format, conv=key.conv, implicit=True) for key in self._subkeys]

    def expand(self, *sources, **kwargs) -> Any:
        logging.debug("MultiDKey Expand")
        match self.keys():
            case [x] if not self._has_text:
                return self._expansion_hook(x.expand(*sources, **kwargs))
            case _:
                return super().expand(*sources, **kwargs)

    @property
    def multi(self) -> bool:
        return True

    def __contains__(self, other):
         return other in self._subkeys

class NonDKey(DKeyBase, mark=DKeyMark_e.NULL):
    """
      Just a string, not a key. But this lets you call no-ops for key specific methods
    """

    def __init__(self, data, **kwargs):
        """
          ignores all kwargs
        """
        super().__init__(data)
        if (fb:=kwargs.get('fallback', None)) is not None and fb != self:
            raise ValueError("NonKeys can't have a fallback, did you mean to use an explicit key?", self)

    def __format__(self, spec) -> str:
        rem, _, _ = self._consume_format_params(spec)
        return format(str(self), rem)

    def format(self, fmt) -> str:
        return format(self, fmt)

    def expand(self, *args, **kwargs) -> str:
        if (fb:=kwargs.get('fallback', None)) is not None and fb != self:
            raise ValueError("NonKeys can't have a fallback, did you mean to use an explicit key?", self)
        return str(self)

    def _update_expansion_params(self, *args) -> Self:
        self._expansion_type  = str
        self._typecheck       = str
        return self
