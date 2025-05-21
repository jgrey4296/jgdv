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
import re
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from . import _interface as API # noqa: N812
from .dkey import DKey
from ._util.expander import Expander
from ._interface import INDIRECT_SUFFIX, DKeyMark_e, RAWKEY_ID, ExpInst_d
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, Self
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
   import pathlib as pl
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   from jgdv._abstract.protocols import SpecStruct_p
   from ._interface import Key_i

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class SingleDKey(DKey, mark=DKeyMark_e.FREE, core=True):
    """
      A Single key with no extras.
      ie: {x}. not {x}{y}, or {x}.blah.
    """
    __slots__ = ()

    def __init__(self, data, **kwargs) -> None:
        super().__init__(data, **kwargs)
        match kwargs.get(RAWKEY_ID, None):
            case [x]:
                self._set_params(fmt=kwargs.get("fmt", None) or x.format,
                                 conv=kwargs.get("conv", None) or x.conv)
            case None | []:
                msg = "A Single Key has no raw key data"
                raise ValueError(msg)
            case [*xs]:
                msg = "A Single Key got multiple raw key data"
                raise ValueError(msg, xs)

    def _set_params(self, *, fmt:Maybe[str]=None, conv:Maybe[str]=None) -> None:
        """ str formatting and conversion parameters.
        These only make sense for single keys, as they need to be wrapped.
        see: https://docs.python.org/3/library/string.html#format-string-syntax
        """
        match fmt:
            case None:
                pass
            case str() if bool(fmt):
                self._fmt_params = fmt

        match conv:
            case None:
                pass
            case str() if bool(conv):
                self._conv_params = conv

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
        rem, wrap, direct = self._consume_format_params(spec) # type: ignore

        # format
        result = str(self)
        if direct:
            result = result.removesuffix(INDIRECT_SUFFIX)
        elif not result.endswith(INDIRECT_SUFFIX):
            result = f"{result}{INDIRECT_SUFFIX}"

        if wrap:
            result = "".join(["{", result, "}"])  # noqa: FLY002

        return format(result, rem)

class MultiDKey[X](DKey, mark=DKeyMark_e.MULTI, multi=True, core=True):
    """ Multi keys allow 1+ explicit subkeys.

    They have additional fields:

    _subkeys  : parsed information about explicit subkeys

    """
    __slots__ = ("_anon")
    anon : str

    def __init__(self, data:str|pl.Path, **kwargs) -> None:
        super().__init__(str(data), **kwargs)
        if not bool(self.data.raw):
            msg = "Tried to build a multi key with no subkeys"
            raise ValueError(msg, data, kwargs)

        # remove the names for the keys, to allow expanding positionally
        self._anon       = "".join(x.anon() for x in self.data.raw)

    def __format__(self, spec:str) -> str:
        """
          Multi keys have no special formatting

          ... except stripping dkey particular format specs out of the result?
        """
        rem, wrap, direct = self._consume_format_params(spec) # type: ignore
        return format(str(self), rem)

    def keys(self) -> list[Key_i]:
        return [DKey(key.joined(), implicit=True)
                for key in self.data.raw
                if bool(key)
                ]

    @property
    def multi(self) -> bool:
        return True

    def __contains__(self, other) -> bool:
         return other in self.keys()

    def exp_pre_lookup_h(self, sources, opts) -> list[list[ExpInst_d]]:
        """ Lift subkeys to expansion instructions """
        targets = []
        for key in self.keys():
            targets.append([ExpInst_d(val=key, fallback=None)])
        else:
            return targets

    def exp_flatten_h(self, vals:list[ExpInst_d], opts) -> Maybe[ExpInst_d]:
        """ Flatten the multi-key expansion into a single string,
        by using the anon-format str
        """
        flat : list[str] = []
        for x in vals:
            match x:
                case ExpInst_d(val=IndirectDKey() as k):
                    flat.append(f"{k:wi}")
                case ExpInst_d(val=x):
                    flat.append(str(x))
        else:
            return ExpInst_d(val=self._anon.format(*flat), literal=True)

class NonDKey(DKey, mark=DKeyMark_e.NULL, core=True):
    """ Just a string, not a key.

    ::

        But this lets you call no-ops for key specific methods.
        It can coerce itself though
    """
    __slots__ = ()

    def __init__(self, data, **kwargs) -> None:
        super().__init__(data, **kwargs)
        if (fb:=kwargs.get('fallback', None)) is not None and fb != self:
            msg = "NonKeys can't have a fallback, did you mean to use an explicit key?"
            raise ValueError(msg, self)

    def __format__(self, spec) -> str:
        rem, _, _ = self._consume_format_params(spec)
        return format(str(self), rem)

    def format(self, fmt) -> str:
        """ Just does normal str formatting """
        return format(self, fmt)

    def expand(self, *args, **kwargs) -> Maybe:
        """ A Non-key just needs to be coerced into the correct str format """
        val = ExpInst_d(val=str(self))
        match self._expander  .coerce_result(val, kwargs, source=self):
            case None if (fallback:=kwargs.get("fallback")) is not None:
                return ExpInst_d(val=fallback, literal=True)
            case None:
                return self._fallback
            case ExpInst_d() as x:
                return x.val
            case x:
                msg = "Nonkey coercion didn't return an ExpInst_d"
                raise TypeError(msg, x)

class IndirectDKey(DKey, mark=DKeyMark_e.INDIRECT, conv="I", core=True):
    """
      A Key for getting a redirected key.
      eg: RedirectionDKey(key) -> SingleDKey(value)

      re_mark :
    """
    __slots__  = ("multi_redir", "re_mark")
    __hash__   = str.__hash__

    def __init__(self, data, multi=False, re_mark=None, **kwargs) -> None:
        kwargs.setdefault("fallback", Self)
        super().__init__(data, **kwargs)
        self.multi_redir      = multi
        self.re_mark          = re_mark

    def __eq__(self, other) -> bool:
        match other:
            case str() if other.endswith(INDIRECT_SUFFIX):
                return f"{self:i}" == other
            case _:
                return super().__eq__(other)

    def exp_pre_lookup_h(self, sources, opts) -> list[list[ExpInst_d]]:
        """ Lookup the indirect version, the direct version, then use the fallback """
        fallback = opts.get("fallback", self._fallback) or self
        return [[
            ExpInst_d(val=f"{self:i}", lift=True),
            ExpInst_d(val=f"{self:d}", convert=False),
            ExpInst_d(val=fallback, literal=True, convert=False),
        ]]
