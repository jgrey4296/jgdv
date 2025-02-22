#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import collections
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
from dataclasses import InitVar, dataclass, field
from time import sleep
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv.structs.chainguard.errors import GuardedAccessError

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

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv.structs.chainguard._base import TomlTypes, GuardBase
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

super_get             = object.__getattribute__
super_set             = object.__setattr__

class TomlAccess_m:
    """ Mixing for dynamic attribute access """

    def __setattr__(self, attr:str, value:TomlTypes) -> None:
        if not getattr(self, "__mutable"):
            raise TypeError()
        super_set(self, attr, value)

    def __getattr__(self, attr:str) -> GuardBase | TomlTypes | list[GuardBase]:
        table = self._table()

        if attr not in table and attr.replace("_", "-") not in table:
            index     = self._index() + [attr]
            index_s   = ".".join(index)
            available = " ".join(self.keys())
            raise GuardedAccessError(f"{index_s} not found, available: [{available}]")

        match table.get(attr, None) or table.get(attr.replace("_", "-"), None):
            case dict() as result:
                return self.__class__(result, index=self._index() + [attr])
            case list() as result if all(isinstance(x, dict) for x in result):
                index = self._index()
                return [self.__class__(x, index=index[:]) for x in result if isinstance(x, dict)]
            case _ as result:
                return result

    def __getitem__(self, keys:str|list[str]|tuple[str]) -> TomlTypes:
        curr : Self = self
        match keys:
            case tuple():
                for key in keys:
                    curr = curr.__getattr__(key)
            case str():
                curr = self.__getattr__(keys)
            case _:
                pass

        return curr

    def get(self, key:str, default:Maybe[TomlTypes]=None) -> Maybe[TomlTypes]:
        if key in self:
            return self[key]

        return default
