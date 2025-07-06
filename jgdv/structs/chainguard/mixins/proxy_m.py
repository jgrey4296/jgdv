#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN401
##-- builtin imports
from __future__ import annotations

import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types as types_
import weakref
from uuid import UUID, uuid1

##-- end builtin imports

from ..proxies.failure import GuardFailureProxy
from ..errors import GuardedAccessError

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
    from ..proxies.base import GuardProxy
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from .. import ChainGuard

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class GuardProxyEntry_m:
    """ A Mixin to add to GuardBase.
    enables handling a number of conditions when accessing values in the underlying data.
    eg:
    tg.on_fail(2, int).a.value() # either get a.value, or 2. whichever returns has to be an int.
    """

    def on_fail(self:ChainGuard, fallback:Any=(), types:Maybe=None, *, non_root:bool=False) -> GuardFailureProxy: # type: ignore[misc]
        """
        use a fallback value in an access chain,
        eg: doot.config.on_fail("blah").this.doesnt.exist() -> "blah"

        *without* throwing a GuardedAccessError
        """
        index = self._index()
        if index != ["<root>"] and not non_root:
            msg = "On Fail not declared at entry"
            raise GuardedAccessError(msg, index)

        return GuardFailureProxy(self, types=types, fallback=fallback)

    def first_of(self:ChainGuard, fallback:Any, types:Maybe=None) -> GuardProxy: # type: ignore[misc]
        """
        get the first non-None value from a index path, even across arrays of tables
        so instead of: data.a.b.c[0].d
        just:          data.first_of().a.b.c.d()
        """
        raise NotImplementedError()

    def all_of(self:ChainGuard, fallback:Any, types:Maybe=None) -> GuardProxy: # type: ignore[misc]
        raise NotImplementedError()

    def flatten_on(self:ChainGuard, fallback:Any) -> GuardProxy: # type: ignore[misc]
        """
        combine all dicts at the call site to form a single dict
        """
        raise NotImplementedError()

    def match_on(self:ChainGuard, **kwargs:tuple[str,Any]) -> GuardProxy: # type: ignore[misc]
        raise NotImplementedError()
