#!/usr/bin/env python3
"""

"""
# ruff: noqa:

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import atexit# for @atexit.register
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
from collections import defaultdict, deque
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

import sh

# ##-- 1st party imports
from jgdv import identity_fn
from jgdv._abstract.protocols import Key_p, SpecStruct_p, Buildable_p
from jgdv.structs.dkey._meta import DKey, DKeyMark_e
from jgdv.util.chain_get import ChainedKeyGetter
from jgdv.structs.strang import Strang, CodeReference

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, Self, Any
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, overload
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
   from jgdv import Maybe, M_, Func, RxStr, Rx, Ident, FmtStr
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

MAX_KEY_EXPANSIONS  : Final[int]                   = 200

DEFAULT_COUNT       : Final[int]                   = 1
PAUSE_COUNT         : Final[int]                   = 0

chained_get         : Func                         = ChainedKeyGetter.chained_get

# Body:

class _DKeyExpander_m:
    """
    A Mixin for DKeys, which does expansion locally
    in order it:
    - pre-formats the value to (A, coerceA,B, coerceB)
    - (lookup A) or (lookup B) or None
    - manipulates the retrieved value
    - potentially recurses on retrieved values
    - type coerces the value
    - runs a post-coercion hook
    - checks the type of the value to be returned

    All of those steps are fallible.
    If one of them fails, then the expansion tries to return, in order:
    - a 'fallback' value passed into the expansion call
    - a 'fallback' value stored on construction of the key
    - None

    Redirection Rules:
    - Hit          : {test}  -> state[test->blah]  -> blah
    - Soft Miss    : {test}  -> state[test_->blah] -> {blah}
    - Hard Miss    : {test}  -> state[...] -> fallback or None

    Indirect Keys act as:
    - Indirect Hard Hit :  {test_}  -> state[test->blah] -> blah
    - Indirect Hit      :  {test_}  -> state[test_->blah] -> {blah}
    - Indirect Miss     :  {test_} -> state[...]         -> {test_}

    """

    def local_expand(self, *sources, **kwargs) -> Maybe[Any]:
        logging.info("Locally Expanding: %s : %s : multi=%s", self, kwargs, self.multi)
        if self._mark is DKeyMark_e.NULL:
            return self

        full_sources = [*sources, *self.exp_extra_sources()]
        fallback     = kwargs.get("fallback", self._fallback) or None
        limit        = kwargs.get("limit", None)
        targets = self.exp_pre_lookup_hook(sources, kwargs)
        match (vals:=self.exp_do_lookup(targets, full_sources, kwargs)):
            case []:
                logging.debug("Failed lookup")
                return fallback

        match (vals:=self.exp_pre_recurse_hook(vals, sources, kwargs)):
            case []:
                logging.deug("Failed Post Lookup Hook")
                return fallback

        match (vals:=self.exp_do_recursion(vals, sources, kwargs, limit=limit)):
            case []:
                logging.debug("Failed Recursion Hook")
                return fallback

        match (flattened:=self.exp_flatten_hook(vals, kwargs)):
             case None:
                logging.debug("Failed Flatten Hook")
                return fallback

        match (coerced:=self.exp_coerce_result(flattened, kwargs)):
            case None:
                logging.debug("Failed Coercion")
                return fallback

        match (final_val:=self.exp_final_hook(coerced, kwargs)):
            case None:
                logging.debug("Failed Post Coerce")
                return fallback

        self.exp_check_result(final_val, kwargs)
        logging.info("%s -> %s", self, final_val)
        return final_val

    def exp_extra_sources(self) -> list[Any]:
        return []

    def exp_pre_lookup_hook(self, sources, opts) -> list:
        return [
            (f"{self:d}", False, None),
            (f"{self:i}", True, None)
        ]

    def exp_do_lookup(self, targets:list, sources:list, opts:dict) -> list:
        """ customisable method for each key subtype """
        result = []
        for key,coerce,fallback in targets:
            if coerce is None:
                result.append(key)
                continue
            match chained_get(key, *sources):
                case None:
                    pass
                case str() as x if coerce:
                    result.append(DKey(x, implicit=True, fallback=fallback))
                case x:
                    result.append(x)
        else:
            return result


    def exp_pre_recurse_hook(self, vals:list[Any], sources, opts) -> list:
        return vals

    def exp_do_recursion(self, vals:list[Any], sources, opts, *, limit=None) -> list:
        match limit:
            case 0 | 1:
                return vals
            case int() as x:
                limit = x - 1
            case None:
                pass

        result = []
        for x in vals:
            match x:
                case DKey():
                    result.append(x.local_expand(*sources, fallback=x, limit=limit))
                case str():
                    as_key = DKey(x)
                    result.append(as_key.local_expand(*sources, fallback=x, limit=limit))
                case x:
                    result.append(x)
        else:
            return result

    def exp_flatten_hook(self, vals:list[Any], opts) -> Maybe[Any]:
        match vals:
            case []:
                return None
            case [x, *xs]:
                return x

    def exp_coerce_result(self, val:Any, opts) -> Maybe[Any]:
        if self._expansion_type is not identity_fn:
            return self._expansion_type(val)

        logging.debug("Coercing: %s : %s", val, self._conv_params)
        match self._conv_params:
            case None:
                return val
            case "p":
                return pl.Path(val).resolve()
            case "s":
                return str(val)
            case "S":
                return Strang(val)
            case "c":
                return CodeReference(val)
            case "i":
                return int(val)
            case "f":
                return float(val)
            case x:
                logging.warning("unknown conversion parameter: %s", x)
                return None

    def exp_final_hook(self, val, opts) -> Maybe[Any]:
        return val

    def exp_check_result(self, val, opts) -> None:
        pass

class DKeyExpansion_m:
    """ general expansion for dkeys """

    def redirect(self, *sources, multi=False, re_mark=None, fallback=None, **kwargs) -> list[DKey]:
        """
          Always returns a list of keys, even if the key is itself
        """
        match self.redirect(self, sources=sources, fallback=fallback):
            case []:
                return [DKey(f"{self:d}", mark=re_mark)]
            case [*xs] if multi:
                return [DKey(x, mark=re_mark, implicit=True) for x in xs]
            case [x] if x is self:
                return [DKey(f"{self:d}", implicit=True)]
            case [x]:
                return [DKey(x, mark=re_mark, implicit=True)]
            case x:
                raise TypeError("bad redirection type", x, self)

    def expand(self, *sources, fallback=None, max=None, check=None, **kwargs) -> Maybe[Any]:
        """ Entrance point for a dkey to shift into a DKeyFormatter """
        logging.debug("DKey expansion for: %s", self)
        from jgdv.structs.dkey import DKeyFormatter
        match DKeyFormatter.expand(self, sources=sources, fallback=fallback or self._fallback, max=max or self._max_expansions):
            case None:
                return None
            case DKey() as x if self._expansion_type is str:
                return f"{x:w}"
            case x:
                return x

    def _check_expansion(self, value, override=None):
        """ typecheck an expansion result """
        match override or self._typecheck:
            case x if x == Any:
                pass
            case types.GenericAlias() as x:
                if not isinstance(value, x.__origin__):
                    raise TypeError("Expansion value is not the correct container", x, value, self)
                if len((args:=x.__args__)) == 1 and not all(isinstance(y, args[0]) for y in value):
                    raise TypeError("Expansion value does not contain the correct value types", x, value, self)
            case types.UnionType() as x if not isinstance(value, x):
                raise TypeError("Expansion value does not match required type", x, value, self)
            case type() as x if not isinstance(value, x):
                raise TypeError("Expansion value does not match required type", x, value, self)
            case _:
                pass

    def _expansion_hook(self, value) -> Any:
        """ An overridable hook for post-expansion control """
        return value

class _DKeyFormatter_Expansion_m:
    """
    A Mixin for  DKeyFormatter, to expand keys without recursion
    """

    def _expand(self, key:Key_p, *, fallback=None, count=DEFAULT_COUNT) -> Maybe[Any]:
        """
          Expand the key, returning fallback if it fails,
          counting each loop as `count` attempts

        """
        if not isinstance(key, Key_p):
            raise TypeError("Key needs to be a jgdv.protocols.Key_p")
        current : DKey = key
        last    : set[str] = set()

        # TODO refactor this to do the same as locations._expand_key
        while 0 < self.rec_remaining and str(current) not in last:
            logging.debug("--- Loop (%s:%s) [%s] : %s", self._depth, MAX_KEY_EXPANSIONS - self.rec_remaining, key, repr(current))
            self.rec_remaining -= count
            last.add(str(current))
            match current:
                case sh.Command():
                    break
                case Key_p() if current._mark is DKey.mark.NULL:
                     continue
                case Key_p() if current.multi:
                    current = self._multi_expand(current)
                case Key_p():
                    redirected = self._try_redirection(current)[0]
                    current    = self._single_expand(redirected) or current
                case _:
                    break

        match current:
            case None:
                current = fallback or key._fallback
            case x if str(x) == str(key):
                current = fallback or key._fallback
            case _:
                pass

        if current is not None:
            logging.debug("Running Expansion Hook: (%s) -> (%s)", key, current)
            exp_val = key._expansion_type(current)
            key._check_expansion(exp_val)
            current = key._expansion_hook(exp_val)

        logging.debug("Expanded (%s) -> (%s)", key, current)
        return current

    def _multi_expand(self, key:Key_p) -> str:
        """
        expand a multi key,
        by formatting the anon key version using a sequence of expanded subkeys,
        this allows for duplicate keys to be used differenly in a single multikey
        """
        logging.debug("multi(%s)", key)
        logging.debug("----> %s", key.keys())
        expanded_keys   = [ str(self._expand(x, fallback=f"{x:w}", count=PAUSE_COUNT)) for x in key.keys() ]
        expanded        = self.format(key._anon, *expanded_keys)
        logging.debug("<---- %s", key.keys())
        return DKey(expanded)

    def _try_redirection(self, key:Key_p) -> list[Key_p]:
        """ Try to redirect a key if necessary,
          if theres no redirection, return the key as a direct key
          """
        key_str = f"{key:i}"
        match chained_get(key_str, *self.sources, *[x for x in key.extra_sources() if x not in self.sources]):
            case list() as ks:
                logging.debug("(%s -> %s -> %s)", key, key_str, ks)
                return [DKey(x, implicit=True) for x in ks]
            case Key_p() as k:
                logging.debug("(%s -> %s -> %s)", key, key_str, k)
                return [k]
            case str() as k:
                logging.debug("(%s -> %s -> %s)", key, key_str, k)
                return [DKey(k, implicit=True)]
            case None if key._mark is DKey.mark.REDIRECT and isinstance(key._fallback, (str,DKey)):
                logging.debug("%s -> %s -> %s (fallback)", key, key_str, key._fallback)
                return [DKey(key._fallback, implicit=True)]
            case None:
                logging.debug("(%s -> %s -> Ø)", key, key_str)
                return [key]
            case _:
                raise TypeError("Reached an unknown response path for redirection", key)

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
