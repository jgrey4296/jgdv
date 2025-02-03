#!/usr/bin/env python3
"""

"""
# ruff: noqa:

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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from collections import defaultdict, deque
from jgdv.util.chain_get import ChainedKeyGetter
from jgdv._abstract.protocols import Key_p, SpecStruct_p
from jgdv.structs.dkey.meta import DKey, DKeyMark_e

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
   from jgdv import Maybe, Func, RxStr, Rx, Ident, FmtStr
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

# Vars:

KEY_PATTERN         : Final[RxStr]                 = "{(.+?)}"
MAX_KEY_EXPANSIONS  : Final[int]                   = 200

FMT_PATTERN         : Final[Rx]                    = re.compile("[wdi]+")
PATTERN             : Final[Rx]                    = re.compile(KEY_PATTERN)
FAIL_PATTERN        : Final[Rx]                    = re.compile("[^a-zA-Z_{}/0-9-]")
EXPANSION_HINT      : Final[Ident]                 = "_doot_expansion_hint"
HELP_HINT           : Final[Ident]                 = "_doot_help_hint"
MAX_DEPTH           : Final[int]                   = 10

DEFAULT_COUNT       : Final[int]                   = 1
RECURSE_GUARD_COUNT : Final[int]                   = 2
PAUSE_COUNT         : Final[int]                   = 0

chained_get         : Func                         = ChainedKeyGetter.chained_get

# Body:

class _DKeyFormatter_Expander_m:
    """
    Expanding a dkey starts in _expand,
    """

    def _expand(self, key:Key_p, *, fallback=None, count=DEFAULT_COUNT) -> Maybe[Any]:
        """
          Expand the key, returning fallback if it fails,
          counting each loop as `count` attempts

        """
        if not isinstance(key, Key_p):
            raise TypeError("Key needs to be a jgdv.protocols.Key_p")

        memo               = {}
        sources            = defaultdict(list)
        incomplete : deque = deque([(None, key)])
        complete   : deque = deque()
        count              = 0

        def _expand_key(key) -> list:
            return []

        while bool(incomplete):
            source, key = incomplete.pop()
            count += 1
            if source in sources[key] and key in sources[source]:
                raise RecursionError("Mutual Dependency in Expansion", key, source)

            sources[key].append(source)
            # Null Key
            # Expand Single Key
            # Expand Multi Key

            expanded = _expand_key(key)

        return complete.pop()

    def _single_expand(self, key:Key_p, fallback=None) -> Maybe[Any]:
        """
          Expand a single key up to {rec_remaining} times
        """
        assert(isinstance(key, Key_p))
        logging.debug("solo(%s)", key)
        match chained_get(key, *self.sources, *[x for x in key.extra_sources() if x not in self.sources], fallback=fallback):
            case None:
                return None
            case Key_p() as x:
                return x
            case x if self.rec_remaining == 0:
                return x
            case str() as x if key._mark is DKey.mark.PATH:
                return DKey(x, mark=DKey.mark.PATH)
            case str() as x if x == key:
                # Got the key back, wrap it and don't expand it any more
                return "{%s}" % x
            case str() | pl.Path() as x:
                return DKey(x)
            case x:
                return x

class _DKeyExpander_m:
    """ Instead of relying on a dkey formatter, a local expander for keys """

    def local_expand(self, *sources, **kwargs) -> Maybe[Any]:
        logging.info("Locally Expanding: %s : %s", self, kwargs)
        if self._mark is DKeyMark_e.NULL:
            return self

        full_sources = [*sources, *self._extra_sources()]
        fallback     = kwargs.get("fallback", self._fallback) or None
        limit        = kwargs.get("limit", None)
        match self._do_redirect(full_sources, kwargs):
            case None:
                pass
            case x:
                return x.local_expand(*sources, **kwargs)

        match (vals:=self._do_lookup(full_sources, kwargs)):
            case None:
                return fallback

        match (vals:=self._post_lookup_hook(vals, sources, kwargs)):
            case None | []:
                return fallback

        if limit is None or 1 < limit:
            match (vals:=self._recursion_hook(vals, sources, kwargs)):
                case None:
                    return fallback

        match (coerced:=self._coerce_result(vals, kwargs)):
            case None:
                return fallback

        match (final_val:=self._post_coerce_hook(coerced, kwargs)):
            case None:
                return fallback

        self._check_result(final_val, kwargs)
        logging.info("%s -> %s", self, final_val)
        return final_val

    def _extra_sources(self) -> list[Any]:
        return []

    def _do_redirect(self, sources, opts) -> Maybe[DKey]:
        key_str = f"{self:i}"
        return chained_get(key_str, *sources)


    def _do_lookup(self, sources, opts) -> Maybe[list]:
        """ customisable method for each key subtype

        single key: lookup in sources, return val
        multi key : lookup each subkey in sources, return list

        """
        match chained_get(self, *sources):
            case None:
                return None
            case x:
                return [x]

    def _post_lookup_hook(self, vals:list[Any], sources, opts) -> Maybe[list]:
        return vals
    def _recursion_hook(self, vals:list[Any], sources, opts) -> Maybe[list]:
        match opts.get("limit", None):
            case None:
                limit = None
            case int() as x:
                limit = x - 1
        subkeys = [DKey(x) if isinstance(x, str) else x for x in vals]
        subexps = [x.local_expand(*sources, limit=limit) if isinstance(x, DKey) else x for x in subkeys]
        return subexps

    def _coerce_result(self, vals:list[Any], opts) -> Maybe[Any]:
        return self._expansion_type(vals[0])

    def _post_coerce_hook(self, val, opts) -> Maybe[Any]:
        match val:
            case DKey():
                return f"{val:w}"
            case _:
                return val

    def _check_result(self, val, opts) -> None:
        pass
