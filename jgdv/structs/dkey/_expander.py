#!/usr/bin/env python3
"""

"""
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

# ##-- 3rd party imports
import sh

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import identity_fn
from jgdv._abstract.protocols import Buildable_p, Key_p, SpecStruct_p
from jgdv.structs.dkey._meta import DKey, DKeyMark_e
from jgdv.structs.strang import CodeReference, Strang
from jgdv.util.chain_get import ChainedKeyGetter
from ._expinst import ExpInst

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
RECURSION_GUARD     : Final[int]                   = 5

chained_get         : Func                         = ChainedKeyGetter.chained_get

# Body:

class DKeyLocalExpander_m:
    """
    A Mixin for DKeys, which does expansion locally
    in order it |-
    - pre-formats the value to (A, coerceA,B, coerceB)
    - (lookup A) or (lookup B) or None
    - manipulates the retrieved value
    - potentially recurses on retrieved values
    - type coerces the value
    - runs a post-coercion hook
    - checks the type of the value to be returned

    All of those steps are fallible.
    when one of them fails, then the expansion tries to return, in order
    - a fallback value passed into the expansion call
    - a fallback value stored on construction of the key
    - None

    Redirection Rules |-
    - Hit          || {test}  => state[test=>blah]  => blah
    - Soft Miss    || {test}  => state[test_=>blah] => {blah}
    - Hard Miss    || {test}  => state[...] => fallback or None

    Indirect Keys act as||-
    - Indirect Hard Hit ||  {test_}  => state[test=>blah] => blah
    - Indirect Hit      ||  {test_}  => state[test_=>blah] => {blah}
    - Indirect Miss     ||  {test_} => state[...]         => {test_}

    """

    def local_redirect(self, *sources, **kwargs) -> list[DKey]:
        return [self.local_expand(*sources, limit=1, **kwargs)]

    def local_expand(self, *sources, **kwargs) -> Maybe[ExpInst]:
        logging.info("- Locally Expanding: %s : %s : multi=%s", repr(self), kwargs, self.multi)
        if self._mark is DKeyMark_e.NULL:
            return self

        match kwargs.get("fallback", self._fallback):
            case None:
                fallback = None
            case ExpInst() as x:
                fallback = x
                logging.debug("Fallback %s -> %s", self, fallback.val)
            case x:
                fallback = ExpInst(val=x, literal=True)
                logging.debug("Fallback %s -> %s", self, fallback.val)

        full_sources = list(sources)
        full_sources += [x for x in self.exp_extra_sources() if x not in full_sources]
        # Limit defaults to -1 / until completion
        # but recursions can pass in limits
        match kwargs.get("limit", -1):
            case 0:
                return fallback or ExpInst(val=f"{self:w}", literal=True)
            case x if x < -1:
                limit = -1
            case x:
                limit = x - 1

        targets = self.exp_pre_lookup_hook(sources, kwargs)
        match (vals:=self.exp_do_lookup(targets, full_sources, kwargs)):
            case []:
                logging.debug("Failed lookup")
                return fallback

        match (vals:=self.exp_pre_recurse_hook(vals, sources, kwargs)):
            case []:
                logging.deug("Failed Post Lookup Hook")
                return fallback

        match (vals:=self.exp_do_recursion(vals, full_sources, kwargs, max_rec=limit)):
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
        logging.info("- %s -> %s", self, final_val)
        return final_val

    def exp_extra_sources(self) -> list[Any]:
        return []

    def exp_pre_lookup_hook(self, sources, opts) -> list[list[ExpInst]]:
        """
        returns a list (L1) of lists (L2) of target tuples (T).
        When looked up, For each L2, the first T that returns a value is added
        to the final result
        """
        return [[
            ExpInst(f"{self:d}"),
            ExpInst(f"{self:i}", lift=True),
        ]]

    def exp_do_lookup(self, targets:list[list[ExpInst]], sources:list, opts:dict) -> list:
        """ customisable method for each key subtype
        Target is a list (L1) of lists (L2) of target tuples (T).
        For each L2, the first T that returns a value is added to the final result
        """
        result = []

        def lookup_target(target:list[ExpInst]) -> Maybe[ExpInst]:
            """
            Handle lookup instructions:
            pass thorugh DKeys and (DKey, ..)
            lift (str(), True, fallback)
            don't lift (str(), False, fallback)

            """
            for spec in target:
                match spec:
                    case ExpInst(val=DKey()):
                        return spec
                    case ExpInst(literal=True):
                        return spec
                    case ExpInst(val=str() as key, lift=lift, fallback=fallback):
                        pass
                    case x:
                        raise TypeError("Unrecognized lookup spec", x)

                match chained_get(key, *sources):
                    case None:
                        pass
                    case str() as x if lift:
                        logging.debug("Lifting Result to Key: %s", x)
                        return ExpInst(DKey(x, implicit=True), fallback=fallback, lift=True)
                    case pl.Path() as x:
                        match DKey(str(x)):
                            case DKey(nonkey=True) as y:
                                return ExpInst(y, rec=0)
                            case y:
                                return ExpInst(y, fallback=fallback)
                    case str() as x:
                        match DKey(x):
                            case DKey(nonkey=True) as y:
                                return ExpInst(y, rec=0)
                            case y:
                                return ExpInst(y, fallback=fallback)
                    case x:
                        return ExpInst(x, fallback=fallback)

        for target in targets:
            match lookup_target(target):
                case None:
                    logging.debug("Lookup Failed for: %s", target)
                    return []
                case ExpInst(val=DKey() as key, rec=-1) as res if self == key:
                    res.rec = RECURSION_GUARD
                    result.append(res)
                case ExpInst() as x:
                    result.append(x)
                case x:
                    raise TypeError("LookupTarget didn't return an ExpInst", x)
        else:
            return result

    def exp_pre_recurse_hook(self, vals:list[ExpInst], sources, opts) -> list[ExpInst]:
        """ Produces a list[Key|Val|(Key, rec:int)]"""
        return vals

    def exp_do_recursion(self, vals:list[ExpInst], sources, opts, max_rec=RECURSION_GUARD) -> list[ExpInst]:
        """
        For values that can expand futher, try to expand them

        """
        result = []
        logging.debug("Recursing: %s", self)
        for x in vals:
            match x:
                case ExpInst(literal=True) | ExpInst(rec=0):
                    result.append(x)
                case ExpInst(val=DKey() as key, rec=-1) if key is self or key == self:
                    raise RecursionError("unrestrained recursive expansion", self)
                case ExpInst(val=str() as key, rec=-1, fallback=fallback, lift=lift):
                    as_key = DKey(key)
                    match as_key.local_expand(*sources, limit=max_rec, fallback=fallback):
                        case None if lift:
                            return [ExpInst(as_key, literal=True)]
                        case None:
                            return []
                        case exp:
                            result.append(exp)
                case ExpInst(val=str() as key, rec=rec, fallback=fallback, lift=lift):
                    new_limit = min(max_rec, rec)
                    as_key = DKey(key)
                    match as_key.local_expand(*sources, limit=new_limit, fallback=fallback):
                        case None if lift:
                            return [ExpInst(as_key, literal=True)]
                        case None:
                            return []
                        case exp:
                            result.append(exp)
                case ExpInst() as x:
                    result.append(x)
                case x:
                    raise TypeError("Unexpected recursion value", x)
        else:
            logging.debug("Finshed Recursing: %s", self)
            return result

    def exp_flatten_hook(self, vals:list[ExpInst], opts) -> Maybe[ExpInst]:
        match vals:
            case []:
                return None
            case [x, *_]:
                return x

    def exp_coerce_result(self, val:ExpInst, opts) -> Maybe[ExpInst]:
        logging.debug("Type Coercion: %s : %s", val, self._conv_params)
        match val:
            case ExpInst(convert=False):
                val.literal = True
                return val
            case ExpInst(val=value) if self._expansion_type is not identity_fn:
                return ExpInst(self._expansion_type(value), literal=True)
            case ExpInst(convert=None) if self._conv_params is None:
                val.literal = True
                return val
            case ExpInst(convert=str() as conv):
                pass
            case _:
                conv = self._conv_params

        # really, keys with conv params should been built as a
        # specialized registered type, to use an exp_final_hook
        match conv:
            case "p":
                val.val = pl.Path(val.val).resolve()
            case "s":
                val.val = str(val.val)
            case "S":
                val.val = Strang(val.val)
            case "c":
                val.val = CodeReference(val.val)
            case "i":
                val.val = int(val.val)
            case "f":
                val.val = float(val.val)
            case x:
                logging.warning("unknown conversion parameter: %s", x)
                return None

        return val

    def exp_final_hook(self, val:ExpInst, opts) -> Maybe[ExpInst]:
        return val

    def exp_check_result(self, val:ExpInst, opts) -> None:
        pass

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
                case Key_p() if current._mark is DKey.Mark.NULL:
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
            key.cent_check_expansion(exp_val)
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
            case None if key._mark is DKey.Mark.REDIRECT and isinstance(key._fallback, (str,DKey)):
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
            case str() as x if key._mark is DKey.Mark.PATH:
                return DKey(x, mark=DKey.Mark.PATH)
            case str() as x if x == key:
                # Got the key back, wrap it and don't expand it any more
                return "{%s}" % x
            case str() | pl.Path() as x:
                return DKey(x)
            case x:
                return x
