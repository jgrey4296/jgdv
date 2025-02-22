#/usr/bin/env python3
""""""
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

from ._interface import TomlTypes
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Mapping
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

@Mixin(GuardProxyEntry_m, TomlLoader_m, TomlWriter_m, silent=True)
@Mixin(TomlAccess_m, DefaultedReporter_m, silent=True)
class ChainGuard(GuardBase):

    @classmethod
    def merge(cls, *guards:Self, dfs:callable=None, index=None, shadow=False) -> Self:
        """
        Given an ordered list of guards and dicts, convert them to dicts,
        update an empty dict with each,
        then wrap that combined dict in a ChainGuard

        *NOTE*: classmethod, not instance. search order is same as arg order.
        So merge(a, b, c) will retrive from c only if a, then b, don't have the key

        # TODO if given a dfs callable, use it to merge more intelligently
        """
        curr_keys = set()
        # Check for conflicts:
        for data in guards:
            new_keys = set(data.keys())
            if bool(curr_keys & new_keys) and not shadow:
                raise KeyError("Key Conflict:", curr_keys & new_keys)
            curr_keys |= new_keys

        # Build a TG from a chainmap
        return ChainGuard.from_dict(ChainMap(*(dict(x) for x in guards)))

    def remove_prefix(self, prefix) -> ChainGuard:
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
