#/usr/bin/env python3
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
from collections import ChainMap
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from re import Pattern
from uuid import UUID, uuid1
from weakref import ref
import tomllib
# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Proto, Mixin

from ._base import GuardBase
from .errors import GuardedAccessError
from .mixins.access_m import TomlAccess_m
from .mixins.loader_m import TomlLoader_m
from .mixins.proxy_m import GuardProxyEntry_m
from .mixins.reporter_m import DefaultedReporter_m
from .mixins.writer_m import TomlWriter_m

from ._interface import TomlTypes, ChainGuard_p
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

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

super_get             = object.__getattribute__
super_set             = object.__setattr__
USCORE   : Final[str] = "_"
DASH     : Final[str] = "-"
MUTABLE  : Final[str] = "__mutable"
##--|

@Proto(ChainGuard_p)
@Mixin(TomlLoader_m, TomlWriter_m, silent=True)
@Mixin(DefaultedReporter_m, silent=True)
class ChainGuard(GuardProxyEntry_m, GuardBase):
    """ The Final ChainGuard class.

    Takes the GuardBase object, and mixes in extra capabilities.

    """
    @classmethod
    def merge(cls, *guards:Self, dfs:Maybe[Callable]=None, index:Maybe[str]=None, shadow:bool=False) -> Self:  # noqa: ARG003
        """
        Given an ordered list of guards and dicts, convert them to dicts,
        update an empty dict with each,
        then wrap that combined dict in a ChainGuard

        *NOTE*: classmethod, not instance. search order is same as arg order.
        So merge(a, b, c) will retrive from c only if a, then b, don't have the key

        # TODO if given a dfs callable, use it to merge more intelligently
        """
        curr_keys : set = set()
        # Check for conflicts:
        for data in guards:
            new_keys = set(data.keys())
            if bool(curr_keys & new_keys) and not shadow:
                msg = "Key Conflict:"
                raise KeyError(msg, curr_keys & new_keys)
            curr_keys |= new_keys

        # Build a TG from a chainmap
        return ChainGuard.from_dict(ChainMap(*(dict(x) for x in guards))) # type: ignore[attr-defined]

    def remove_prefix(self, prefix:str) -> ChainGuard:
        """ Try to remove a prefix from loaded data
          eg: ChainGuard(tools.ChainGuard.data..).remove_prefix("tools.ChainGuard")
          -> ChainGuard(data..)
        """
        match prefix:
            case None:
                return self
            case str():
                logging.debug("Removing prefix from data: %s", prefix)
                try:
                    attempt = self
                    for x in prefix.split("."):
                        attempt = attempt[x]
                    else:
                        return ChainGuard(attempt)
                except GuardedAccessError:
                    return self


    @override
    def __setattr__(self:ChainGuard_i, attr:str, value:Any) -> None:
        if not getattr(self, MUTABLE):
            raise TypeError()
        super_set(self, attr, value)

    def __getattr__(self:ChainGuard_i, attr:str) -> Any:  # noqa: ANN401
        index    : list[str]
        index_s  : str
        table    : dict  = self._table()  # type: ignore[operator,assignment]

        if attr not in table and attr.replace(USCORE, DASH) not in table:
            index      = [*self._index(), attr] # type: ignore[operator,misc]
            index_s    = ".".join(index)
            available  = " ".join(self.keys())
            msg        = f"{index_s} not found, available: [{available}]"
            raise GuardedAccessError(msg)

        match table.get(attr, None) or table.get(attr.replace(USCORE, DASH), None):
            case dict() as result:
                return type(self)(result, index=[*self._index(), attr])
            case list() as result if all(isinstance(x, dict) for x in result):
                index = self._index()
                return [type(self)(x, index=index[:]) for x in result if isinstance(x, dict)]
            case _ as result:
                return result

    def __getitem__(self:ChainGuard_i, keys:int|str|list[str]|tuple[str]) -> Any:  # noqa: ANN401
        curr : ChainGuard_i|TomlTypes = self
        match keys:
            case tuple():
                for key in keys:
                    curr = getattr(curr, key)
            case str():
                curr = getattr(self, keys)
            case _:
                pass

        return curr

    def get(self:ChainGuard_i, key:str, default:Maybe=None) -> Maybe:
        if key in self:
            return self[key]

        return default
