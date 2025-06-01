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
from .dkey import DKey
from ._interface import INDIRECT_SUFFIX, DKeyMark_e, RAWKEY_ID, ExpInst_d
from . import _interface as API # noqa: N812
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
from typing import Never

if TYPE_CHECKING:
   import pathlib as pl
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   from jgdv._abstract.protocols import SpecStruct_p

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class SingleDKey(DKey[DKeyMark_e.FREE], core=True):
    """
      A Single key with no extras.
      ie: {x}. not {x}{y}, or {x}.blah.
    """
    __slots__ = ()

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        match self.data.raw:
            case [x] if self.data.convert is None:
                self.data.convert  = x.convert
                self.data.format   = x.format
            case [_]:
                pass
            case None | []:
                msg = "A Single Key has no raw key data"
                raise ValueError(msg)
            case [*xs]:
                msg = "A Single Key got multiple raw key data"
                raise ValueError(msg, xs)

class MultiDKey(DKey[DKeyMark_e.MULTI], core=True):
    """ Multi keys allow 1+ explicit subkeys.

    They have additional fields:

    _subkeys  : parsed information about explicit subkeys

    """
    __slots__ = ("anon",)
    anon  : str

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        match self.data.raw:
            case [] | None:
                msg = "Tried to build a multi key with no subkeys"
                raise ValueError(msg, self.data.raw, kwargs)
            case [*xs]:
                self.anon  = "".join(x.anon() for x in xs)

    def __str__(self) -> str:
        return self[:]

    def __contains__(self, other:object) -> bool:
         return other in self.keys()

    def __format__(self, spec, **kwargs) -> str:  # noqa: ANN002, ANN003
        """ Just does normal str formatting """
        rem, _, _= self._processor.consume_format_params(spec) # type: ignore
        return super().__format__(rem, **kwargs)

    def _multi(self) -> Literal[True]:
        return True

    @override
    def keys(self) -> list[DKey]: # type: ignore[override]
        return [DKey(x, implicit=True) for x in self.data.meta if bool(x)]

    def exp_pre_lookup_h(self, sources:list[dict], opts:dict) -> list[list[ExpInst_d]]:  # noqa: ARG002
        """ Lift subkeys to expansion instructions """
        targets = []
        for key in self.keys():
            targets.append([ExpInst_d(value=key, fallback=None)])
        else:
            return targets

    def exp_flatten_h(self, vals:list[ExpInst_d], opts:dict) -> Maybe[ExpInst_d]:  # noqa: ARG002
        """ Flatten the multi-key expansion into a single string,
        by using the anon-format str
        """
        flat : list[str] = []
        for x in vals:
            match x:
                case ExpInst_d(value=IndirectDKey() as k):
                    flat.append(f"{k:wi}")
                case ExpInst_d(value=API.Key_p() as k):
                    flat.append(k[:])
                case ExpInst_d(value=x):
                    flat.append(str(x))
        else:
            return ExpInst_d(value=self.anon.format(*flat), literal=True)

class NonDKey(DKey[DKeyMark_e.NULL], core=True):
    """ Just a string, not a key.

    ::

        But this lets you call no-ops for key specific methods.
        It can coerce itself though
    """
    __slots__ = ()

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        if (fb:=kwargs.get('fallback', None)) is not None and fb != self:
            msg = "NonKeys can't have a fallback, did you mean to use an explicit key?"
            raise ValueError(msg, self)

    def __format__(self, spec, **kwargs) -> str:  # noqa: ANN002, ANN003
        """ Just does normal str formatting """
        rem, _, _= self._processor.consume_format_params(spec) # type: ignore
        return super().__format__(rem, **kwargs)

    def expand(self, *args, **kwargs) -> Maybe:  # noqa: ANN002, ANN003, ARG002
        """ A Non-key just needs to be coerced into the correct str format """
        val = ExpInst_d(value=self[:])
        match self._expander.coerce_result(val, kwargs, source=self):
            case None if (fallback:=kwargs.get("fallback")) is not None:
                return ExpInst_d(value=fallback, literal=True)
            case None:
                return self.data.fallback
            case ExpInst_d() as x:
                return x.value
            case x:
                msg = "Nonkey coercion didn't return an ExpInst_d"
                raise TypeError(msg, x)

class IndirectDKey(DKey[DKeyMark_e.INDIRECT], conv="I", core=True):
    """
      A Key for getting a redirected key.
      eg: RedirectionDKey(key) -> SingleDKey(value)

      re_mark :
    """
    __slots__  = ("multi_redir", "re_mark")
    __hash__ = SingleDKey.__hash__

    def __init__(self, *, multi:bool=False, re_mark:Maybe[API.KeyMark]=None, **kwargs) -> None:  # noqa: ANN003
        assert(not self.endswith(INDIRECT_SUFFIX)), self[:]
        kwargs.setdefault("fallback", Self)
        super().__init__(**kwargs)
        self.multi_redir      = multi
        self.re_mark          = re_mark

    def __eq__(self, other:object) -> bool:
        match other:
            case str() if other.endswith(INDIRECT_SUFFIX):
                return f"{self:i}" == other
            case _:
                return super().__eq__(other)

    def _indirect(self) -> Literal[True]:
        return True

    def exp_pre_lookup_h(self, sources:list[dict], opts:dict) -> list[list[ExpInst_d]]:  # noqa: ARG002
        """ Lookup the indirect version, the direct version, then use the fallback """
        match opts.get("fallback", self.data.fallback):
            case x if x is Self:
                fallback = self
            case None:
                fallback = self
            case x:
                fallback = x
        return [[
            ExpInst_d(value=f"{self:i}", lift=True),
            ExpInst_d(value=f"{self:d}", convert=False),
            ExpInst_d(value=fallback, literal=True, convert=False),
        ]]
