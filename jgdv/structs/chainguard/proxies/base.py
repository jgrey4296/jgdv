#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import contextlib
import datetime
import enum
import faulthandler
import functools as ftz
import hashlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from copy import deepcopy
from time import sleep
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 1st party imports
from .._base import GuardBase
from jgdv.structs.chainguard.mixins.reporter_m import DefaultedReporter_m

# ##-- end 1st party imports

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
from typing import Any, Never

if TYPE_CHECKING:
    from .._interface import TomlTypes
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import CHECKTYPE
    from .._interface import ChainGuard_i

    type Wrapper = Callable[[TomlTypes], Any]

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class GuardProxy:
    """ A Base Class for Proxies """
    __slots__ = ("__index", "_data", "_fallback", "_types")
    _data      : Maybe[TomlTypes|GuardBase]
    _types     : CHECKTYPE
    __index    : list[str]
    _fallback  : Maybe[TomlTypes|tuple]

    def __init__(self, data:Maybe[TomlTypes|GuardBase], types:Any=None, index:Maybe[list[str]]=None, fallback:Maybe[TomlTypes|tuple]=()) -> None:  # noqa: ANN401
        self._data      = data
        self._types     = types
        self._fallback  = fallback
        self.__index    = index or ["<root>"]

    @override
    def __repr__(self) -> str:
        type_str = self._types_str()
        index_str = ".".join(self._index())
        return f"<GuardProxy: {index_str}:{type_str}>"

    def __len__(self) -> int:
        if isinstance(self._data, collections.abc.Sized):
            return len(self._data)

        return 0

    def __bool__(self) -> bool:
        return self._data is not None and self._data is not Never

    def __call__(self, *, wrapper:Maybe[Wrapper]=None, **kwargs:Any) -> Any:  # noqa: ANN401
        raise NotImplementedError()

    def __getattr__(self, attr:str) -> GuardProxy:
        raise NotImplementedError()

    def __getitem__(self, keys:int|str|tuple[str]) -> GuardProxy:
        raise NotImplementedError()

    ##--|

    def _inject(self, val:Maybe=None, attr:Maybe[str]=None, *, clear:bool=False) -> GuardProxy:
        match val:
            case _ if clear:
                val = None
            case _:
                pass

        return type(self)(val,
                          types=self._types,
                          index=self._index(attr),
                          fallback=self._fallback)

    def _notify(self) -> None:
        types_str = self._types_str()
        match self._data, self._fallback, self._index():
            case GuardBase(), _, _:
                pass
            case None, (), _:
                pass
            case _, _, []:
                pass
            case None, val, [*index]:
                DefaultedReporter_m.add_defaulted(".".join(index),
                                                  val,
                                                  types_str)
            case val, _, [*index]:
                assert(not isinstance(val, GuardBase|None))
                DefaultedReporter_m.add_defaulted(".".join(index),
                                                  val,
                                                  types_str)
            case val, flbck, index,:
                msg = "Unexpected Values found: "
                raise TypeError(msg, val, index, flbck)

    def _types_str(self) -> str:
        types_str : str
        match self._types:
            case None:
                return "Any"
            case types.UnionType() as targ:
                types_str = repr(targ)
            case type(__name__=targ):
                types_str = targ
            case _ as targ:
                types_str = str(targ)

        return types_str

    def _match_type(self, val:Maybe[TomlTypes]) -> Maybe[TomlTypes]:
        match self._types:
            case type() if not isinstance(val, self._types):
                types_str  = self._types_str()
                index_str  = ".".join(*self.__index, *['(' + types_str + ')'])
                msg        = "TomlProxy Value doesn't match declared Type: "
                raise TypeError(msg, index_str, val, self._types)
            case _:
                # TODO handle unions and generics
                pass

        return val

    def _index(self, sub:Maybe[str]=None) -> list[str]:
        if sub is None:
            return self.__index[:]
        return [*self.__index[:], sub]
