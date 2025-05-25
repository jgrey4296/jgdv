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
from .._interface import TomlTypes
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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
from typing import Any, Never

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class GuardProxy:
    """ A Base Class for Proxies """
    __slots__ = ("_types", "_data", "__index")

    def __init__(self, data:GuardBase, types:Any=None, index:Maybe[list[str]]=None, fallback:TomlTypes|Literal[Never]=Never):
        self._types                         = types or Any
        self._data                          = data
        self.__index : list[str]            = index or ["<root>"]

    def __repr__(self) -> str:
        type_str = self._types_str()
        index_str = ".".join(self._index())
        return f"<GuardProxy: {index_str}:{type_str}>"

    def __len__(self) -> int:
        if hasattr(self._data, "__len__"):
            return len(self._data)

        return 0

    def __bool__(self) -> bool:
        return self._data is not None and self._data is not Never

    def __call__(self, *, wrapper:Maybe[callable[[TomlTypes], Any]]=None, **kwargs) -> Any:
        return None

    def _inject(self, val:tuple[Any]=Never, attr:Maybe[str]=None, clear:bool=False) -> GuardProxy:
        match val:
            case _ if clear:
                val = Never
            case x if x is Never:
                val = self._data
            case _:
                pass

        return GuardProxy(val,
                          types=self._types,
                          index=self._index(attr),
                          fallback=self._fallback)

    def _notify(self) -> None:
        types_str = self._types_str()
        match self._data, self._fallback, self._index():
            case GuardBase(), _, _:
                pass
            case _, _, []:
                pass
            case x , val, [*index] if x is Never:
                DefaultedReporter_m.add_defaulted(".".join(index), val, types_str)
            case val, _, [*index]:
                DefaultedReporter_m.add_defaulted(".".join(index), val, types_str)
            case val, flbck, index,:
                raise TypeError("Unexpected Values found: ", val, index, flbck)

    def _types_str(self) -> str:
        match self._types:
            case types.UnionType() as targ:
                types_str = repr(targ)
            case type(__name__=targ):
                types_str = targ
            case _ as targ:
                types_str = str(targ)

        return types_str

    def _match_type(self, val:TomlTypes) -> TomlTypes:
        if self._types != Any and not isinstance(val, self._types):
            types_str = self._types_str()
            index_str  = ".".join(self.__index + ['(' + types_str + ')'])
            raise TypeError("TomlProxy Value doesn't match declared Type: ", index_str, val, self._types)

        return val

    def _index(self, sub:str=None) -> list[str]:
        if sub is None:
            return self.__index[:]
        return self.__index[:] + [sub]
