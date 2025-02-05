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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv._abstract.protocols import Buildable_p, Key_p, SpecStruct_p
from jgdv.structs.dkey._meta import DKey, DKeyMark_e, DKeyMeta
from jgdv.structs.dkey._base import DKeyBase
from ._parser import REDIRECT_SUFFIX

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class SingleDKey(DKeyBase, mark=DKeyMark_e.FREE):
    """
      A Single key with no extras.
      ie: {x}. not {x}{y}, or {x}.blah.
    """

    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)
        match kwargs.get(DKeyMeta._rawkey_id, None):
            case [x]:
                self._set_params(fmt=kwargs.get("fmt", None) or x.format,
                                 conv=kwargs.get("conv", None) or x.conv)
            case None | []:
                raise ValueError("A Single Key no raw key data")
            case [*xs]:
                raise ValueError("A Single Key got multiple raw key data", xs)


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
      Multi keys allow 1+ explicit subkeys.

    The have additional fields:
    _has_text : whether the multikey has non-key based text pre/suffixes
    _subkeys  : parsed information about explicit subkeys

    """

    def __init__(self, data:str|pl.Path, **kwargs):
        super().__init__(data, **kwargs)
        match kwargs.get(DKeyMeta._rawkey_id, None):
            case [*xs]:
                self._subkeys = xs
            case None | []:
                raise ValueError("Tried to build a multi key with no subkeys", data)

        # remove the names for the keys, to allow expanding positionally
        self._anon       = self.format("", state={key.key : "{}" for key in self._subkeys})

    def __format__(self, spec:str) -> str:
        """
          Multi keys have no special formatting

          ... except stripping dkey particular format specs out of the result?
        """
        rem, wrap, direct = self._consume_format_params(spec)
        return format(str(self), rem)

    def keys(self) -> list[Key_p]:
        return [DKey(key.key, fmt=key.format, conv=key.conv, implicit=True)
                for key in self._subkeys
                if bool(key)
                ]

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
         return other in self.keys()

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

    def local_expand(self, *args, **kwrags) -> str:
        return str(self)

class IndirectDKey(SingleDKey, mark=DKeyMark_e.INDIRECT, conv="I"):
    """
      A Key for getting a redirected key.
      eg: RedirectionDKey(key_) -> SingleDKey(value)

      re_mark :
    """

    def __init__(self, data, multi=False, re_mark=None, **kwargs):
        kwargs.setdefault("fallback", Self)
        super().__init__(data, **kwargs)
        self.multi_redir      = multi
        self.re_mark          = re_mark
        self._expansion_type  = DKey
        self._typecheck       = DKey | list[DKey]
        self._fallback         = f"{self:wi}"

    def expand(self, *sources, max=None, full:bool=False, **kwargs) -> Maybe[DKey]:
        match super().redirect(*sources, multi=self.multi_redir, re_mark=self.re_mark, **kwargs):
            case list() as xs if self.multi_redir and full:
                return [x.expand(*sources) for x in xs]
            case list() as xs if self.multi_redir:
                return xs
            case [x, *xs] if full:
                return x.expand(*sources)
            case [x, *xs] if self._fallback == self and x < self:
                return x
            case [x, *xs] if self._fallback is None:
                return None
            case [x, *xs]:
                return x
            case []:
                return self._fallback

    def exp_pre_lookup_hook(self, sources, opts) -> list:
        return [
            (f"{self:i}", True, None),
            (f"{self:d}", False, None)
        ]
