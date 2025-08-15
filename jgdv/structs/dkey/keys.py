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

from . import _interface as API # noqa: N812
from ._interface import INDIRECT_SUFFIX, RAWKEY_ID, DKeyMark_e, Key_p, NonKey_p
from ._util._interface import (ExpInst_d, ExpInstChain_d, InstructionFactory_p,
                               SourceChain_d)
from .dkey import DKey

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
from typing import Any
from collections.abc import Mapping

if TYPE_CHECKING:
   import pathlib as pl
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, LiteralString
   from typing import Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, MutableMapping, Hashable
   from jgdv._abstract.protocols.general import SpecStruct_p

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class SingleDKey(DKey, mark=Any, default=True):
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

    def _post_process_h(self, data:Maybe[dict]=None) -> None:  # noqa: ARG002
        fmt : str
        match self.data.raw[0].format:
            case None:
                return
            case str() as fmt :
                pass

        match API.EXPANSION_LIMIT_PATTERN.search(fmt):
            case re.Match() as m:
                self.data.max_expansions = int(m[1])
            case None:
                pass

class MultiDKey(DKey, mark=list):
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

    @override
    def __str__(self) -> str:
        return self[:]

    @override
    def __contains__(self, other:object) -> bool:
         return other in self.keys()

    @override
    def __format__(self, spec:str, **kwargs:Any) -> str:
        """ Just does normal str formatting """
        rem, _, _= self._processor.consume_format_params(spec)
        return super().__format__(rem, **kwargs)

    def _multi(self) -> Literal[True]:
        return True

    def keys(self) -> list[DKey]:
        return [DKey(x, implicit=True) for x in self.data.meta if bool(x)]

    def exp_generate_chains_h(self, root:ExpInst_d, factory:InstructionFactory_p, opts:dict) -> list[ExpInstChain_d|ExpInst_d]:
        """ Lift subkeys to expansion instructions """
        targets : list[ExpInstChain_d|ExpInst_d]= []
        keys  = self.keys()
        targets.append(ExpInstChain_d(root=self, merge=len(keys))) # type: ignore[arg-type]
        for key in keys:
            match factory.build_inst(key, root, opts, decrement=False):
                case None:
                    targets.append(factory.null_inst())
                case ExpInst_d() as inst if inst.literal is True:
                    targets.append(inst)
                case ExpInst_d() as inst if inst.value != self:
                    assert(inst.value != root.value)
                    targets += factory.build_chains(inst, opts)
                case ExpInst_d() as inst:
                    vals = [
                        inst,
                        factory.null_inst(),
                    ]
                    targets.append(factory.build_single_chain(vals, self))
        else:
            return targets

    def exp_flatten_h(self, vals:list[ExpInst_d], factory:InstructionFactory_p, opts:dict) -> Maybe[ExpInst_d]:  # noqa: ARG002
        """ Flatten the multi-key expansion into a single string,
        by using the anon-format str
        """
        flat : list[str]  = []
        key_meta          = [x for x in self.data.meta if bool(x)]
        if bool(vals) and not bool(key_meta):
            return vals[0]
        if len(vals) != len([x for x in self.data.meta if bool(x)]):
            return None

        for x in vals:
            match x:
                case ExpInst_d(value=IndirectDKey() as k):
                    flat.append(f"{k:wi}")
                case ExpInst_d(value=API.Key_p() as k):
                    flat.append(f"{k:w}")
                case ExpInst_d(value=x):
                    flat.append(str(x))
        else:
            return ExpInst_d(value=self.anon.format(*flat), literal=True)

class NonDKey(DKey, mark=False):
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

    @override
    def __format__(self, spec:str, **kwargs:Any) -> str:
        """ Just does normal str formatting """
        rem, _, _= self._processor.consume_format_params(spec)
        return super().__format__(rem, **kwargs)

    def _nonkey(self) -> Literal[True]:
        return True

    @override
    def expand(self, *args, **kwargs) -> Maybe:  # noqa: ANN002, ANN003
        """ A Non-key just needs to be coerced into the correct str format """
        assert(isinstance(self, API.Key_p))
        val = ExpInst_d(value=self[:])
        match self._expander.coerce_result(val, self, kwargs):
            case None if (fallback:=kwargs.get("fallback")) is not None:
                return ExpInst_d(value=fallback, literal=True)
            case None:
                return self.data.fallback
            case ExpInst_d() as x:
                return x.value
            case x:
                msg = "Nonkey coercion didn't return an ExpInst_d"
                raise TypeError(msg, x)

class IndirectDKey(DKey, mark=Mapping, convert="I"):
    """
      A Key for getting a redirected key.
      eg: RedirectionDKey(key) -> SingleDKey(value)

      re_mark :
    """
    __slots__  = ("multi_redir", "re_mark")
    __hash__ = SingleDKey.__hash__

    def __init__(self, *, multi:bool=False, re_mark:Maybe[API.KeyMark]=None, **kwargs) -> None:  # noqa: ANN003
        assert(not self.endswith(INDIRECT_SUFFIX)), self[:]
        super().__init__(**kwargs)
        self.multi_redir      = multi
        self.re_mark          = re_mark

    @override
    def __str__(self) -> str:
        return f"{self:i}"

    @override
    def __eq__(self, other:object) -> bool:
        match other:
            case str() if other.endswith(INDIRECT_SUFFIX):
                return f"{self:i}" == other
            case _:
                return super().__eq__(other)

    def _indirect(self) -> Literal[True]:
        return True

    def exp_generate_chains_h(self, root:ExpInst_d, factory:InstructionFactory_p, opts:dict) -> list[ExpInstChain_d|ExpInst_d]:
        """ Lookup the indirect version, the direct version, then use the fallback """
        targets : list = [
            factory.build_inst(self, root, opts, decrement=False),
            factory.lift_inst(f"{self:d}", root, opts, decrement=False, implicit=True),
            factory.null_inst(),
            ]

        return [ExpInstChain_d(*targets, root=root.value)]
