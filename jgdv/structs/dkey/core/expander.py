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
from jgdv.decorators import DoMaybe
from jgdv.structs.strang import CodeReference, Strang
from ._getter import ChainGetter as CG  # noqa: N817
from .meta import DKey
from .._interface import DKeyMark_e, MAX_KEY_EXPANSIONS, DEFAULT_COUNT, PAUSE_COUNT, RECURSION_GUARD, ExpInst_d
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

if TYPE_CHECKING:
   from jgdv import Maybe, M_, Func, RxStr, Rx, Ident, FmtStr
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
from .._interface import Expandable_p, Key_p
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class Expander:
    """
    A Static class to control expansion.
    In order it does |-
    - pre-format the value to (A, coerceA,B, coerceB)
    - (lookup A) or (lookup B) or None
    - manipulates the retrieved value
    - potentially recurses on retrieved values
    - type coerces the value
    - runs a post-coercion hook
    - checks the type of the value to be returned

    During the above, the hooks of Expandable_p will be called on the source,
    if they return nothing, the default hook implementation is used.

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
    - Indirect Soft Hit ||  {test_}  => state[test_=>blah] => {blah}
    - Indirect Hard Hit ||  {test_}  => state[test=>blah] => blah
    - Indirect Miss     ||  {test_} => state[...]         => {test_}

    """

    @staticmethod
    def redirect(source:Expandable_p, *sources, **kwargs) -> list[DKey]:
            return [Expander.expand(source, *sources, limit=1, **kwargs)]

    @staticmethod
    def expand(source:Expandable_p, *sources, **kwargs) -> Maybe[ExpInst_d]:
        logging.info("- Locally Expanding: %s : %s : multi=%s", repr(source), kwargs, source.multi)
        if source._mark is DKeyMark_e.NULL:
            return ExpInst_d(val=source, literal=True)

        match kwargs.get("fallback", source._fallback):
            case None:
                fallback = None
            case type() as ctor:
                x = ctor()
                fallback = ExpInst_d(val=x, literal=True)
            case ExpInst_d() as x:
                fallback = x
                logging.debug("Fallback %s -> %s", source, fallback.val)
            case x:
                fallback = ExpInst_d(val=x, literal=True)
                logging.debug("Fallback %s -> %s", source, fallback.val)

        full_sources = list(sources)
        full_sources += [x for x in Expander.extra_sources(source) if x not in full_sources]
        # Limit defaults to -1 / until completion
        # but recursions can pass in limits
        match kwargs.get("limit", None):
            case 0:
                return fallback or ExpInst_d(val=source, literal=True)
            case None | -1:
                limit = -1
            case x if x < -1:
                limit = -1
            case x:
                limit = x - 1

        targets       = Expander.pre_lookup(sources, kwargs, source=source)
        # These are Maybe monads:
        vals          = Expander.do_lookup(targets, full_sources, kwargs, source=source)
        vals          = Expander.pre_recurse(vals, sources, kwargs, source=source)
        vals          = Expander.do_recursion(vals, full_sources, kwargs, max_rec=limit, source=source)
        flattened     = Expander.flatten(vals, kwargs, source=source)
        coerced       = Expander.coerce_result(flattened, kwargs, source=source)
        final_val     = Expander.finalise(coerced, kwargs, source=source)
        Expander.check_result(source, final_val, kwargs)
        match final_val:
            case None:
                logging.debug("Expansion Failed, using fallback")
                return fallback
            case ExpInst_d(literal=False) as x:
                raise ValueError("Expansion didn't result in a literal", x, source)
            case ExpInst_d() as x:
                logging.info("- %s -> %s", source, final_val)
                return x
            case x:
                raise TypeError(type(x))

    @staticmethod
    def extra_sources(source) -> list[Any]:
        match source.exp_extra_sources_h():
            case None:
                return []
            case list() as xs:
                return xs
            case x:
                raise TypeError(type(x))

    @staticmethod
    def pre_lookup(sources, opts, *, source) -> list[list[ExpInst_d]]:
        """
        returns a list (L1) of lists (L2) of target tuples (T).
        When looked up, For each L2, the first T that returns a value is added
        to the final result
        """
        match source.exp_pre_lookup_h(sources, opts):
            case None:
                return [[
                    ExpInst_d(val=f"{source:d}"),
                    ExpInst_d(val=f"{source:i}", lift=True),
                ]]
            case list() as xs:
                return xs
            case x:
                raise TypeError(type(x))

    @staticmethod
    @DoMaybe
    def do_lookup(targets:list[list[ExpInst_d]], sources:list, opts:dict, *, source) -> Maybe[list]:
            """ customisable method for each key subtype
            Target is a list (L1) of lists (L2) of target tuples (T).
            For each L2, the first T that returns a value is added to the final result
            """
            result = []
            for target in targets:
                match CG.lookup(target, sources):
                    case None:
                        logging.debug("Lookup Failed for: %s", target)
                        return []
                    case ExpInst_d(val=DKey() as key, rec=-1) as res if source == key:
                        res.rec = RECURSION_GUARD
                        result.append(res)
                    case ExpInst_d() as x:
                        result.append(x)
                    case x:
                        msg = "LookupTarget didn't return an ExpInst_d"
                        raise TypeError(msg, x)
            else:
                return result

    @staticmethod
    @DoMaybe
    def pre_recurse(vals:list[ExpInst_d], sources, opts, *, source) -> Maybe[list[ExpInst_d]]:
        """ Produces a list[Key|Val|(Key, rec:int)]"""
        match source.exp_pre_recurse_h(vals, sources, opts):
            case None:
                return vals
            case list() as newvals:
                return newvals
            case x:
                raise TypeError(type(x))

    @staticmethod
    @DoMaybe
    def do_recursion(vals:list[ExpInst_d], sources, opts, max_rec=RECURSION_GUARD, *, source) -> Maybe[list[ExpInst_d]]:
        """
        For values that can expand futher, try to expand them

        """
        result = []
        logging.debug("Recursing: %r", source)
        for x in vals:
            match x:
                case ExpInst_d(literal=True) | ExpInst_d(rec=0) as res:
                    result.append(res)
                case ExpInst_d(val=DKey() as key, rec=-1) if key is source or key == source:
                    msg = "Unrestrained Recursive Expansion"
                    raise RecursionError(msg, source)
                case ExpInst_d(val=str() as key, rec=-1, fallback=fallback, lift=lift):
                    as_key = DKey(key)
                    match Expander.expand(as_key, *sources, limit=max_rec, fallback=fallback):
                        case None if lift:
                            return [ExpInst_d(val=as_key, literal=True)]
                        case None:
                            return []
                        case ExpInst_d() as exp if lift:
                            exp.convert = False
                            result.append(exp)
                        case ExpInst_d() as exp:
                            result.append(exp)
                case ExpInst_d(val=str() as key, rec=rec, fallback=fallback, lift=lift):
                    new_limit = min(max_rec, rec)
                    as_key = DKey(key)
                    match Expander.expand(as_key, *sources, limit=new_limit, fallback=fallback):
                        case None if lift:
                            return [ExpInst_d(val=as_key, literal=True)]
                        case None:
                            return []
                        case ExpInst_d() as exp:
                            result.append(exp)
                        case x:
                            raise TypeError(type(x))
                case ExpInst_d() as x:
                    result.append(x)
                case x:
                    msg = "Unexpected Recursion Value"
                    raise TypeError(msg, x)
        else:
            logging.debug("Finished Recursing: %r : %r", source, result)
            return result

    @staticmethod
    @DoMaybe
    def flatten(vals:list[ExpInst_d], opts, *, source) -> Maybe[ExpInst_d]:
        match vals:
            case []:
                return None

        match source.exp_flatten_h(vals, opts):
            case None:
                return vals[0]
            case False:
                return None
            case ExpInst_d() as x:
                return x
            case x:
                raise TypeError(type(x))

    @staticmethod
    @DoMaybe
    def coerce_result(val:ExpInst_d, opts, *, source) -> Maybe[ExpInst_d]:
        """
        Coerce the expanded value accoring to source's expansion type ctor
        """
        logging.debug("%r Type Coercion: %r : %s", source, val, source._conv_params)
        match source.exp_coerce_h(val, opts):
            case ExpInst_d() as x:
                return x
            case None:
                pass

        match val:
            case ExpInst_d(convert=False):
                # Conversion is off
                val.literal = True
                return val
            case ExpInst_d(val=value, convert=None) if isinstance(source._expansion_type, type) and isinstance(value, source._expansion_type):
                # Type is already correct
                val.literal = True
                return val
            case ExpInst_d(val=value, convert=None) if source._expansion_type is not identity_fn:
                # coerce a real ctor
                val.val = source._expansion_type(value)
                val.literal = True
                return val
            case ExpInst_d(convert=None) if source._conv_params is None:
                # No conv params
                val.literal = True
                return val
            case ExpInst_d(convert=str() as conv):
                # Conv params in expinst
                return Expander._coerce_result_by_conv_param(val, conv, opts, source=source)
            case _ if source._conv_params:
                #  Conv params in source
                return Expander._coerce_result_by_conv_param(val, source._conv_params, opts, source=source)
            case ExpInst_d():
                return val
            case x:
                raise TypeError(type(x))

    @staticmethod
    @DoMaybe
    def _coerce_result_by_conv_param(val, conv, opts, *, source) -> Maybe[ExpInst_d]:
        """ really, keys with conv params should been built as a
        specialized registered type, to use an exp_final_hook
        """
        match conv:
            case "p":
                val.val = pl.Path(val.val).expanduser().resolve()
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
                logging.warning("Unknown Conversion Parameter: %s", x)
                return None

        return val

    @staticmethod
    @DoMaybe
    def finalise(val:ExpInst_d, opts, *, source) -> Maybe[ExpInst_d]:
        match source.exp_final_h(val, opts):
            case None:
                val.literal = True
                return val
            case False:
                return None
            case ExpInst_d() as x:
                return x
            case x:
                raise TypeError(type(x))

    @staticmethod
    @DoMaybe
    def check_result(source, val:ExpInst_d, opts) -> None:
        """ check the type of the expansion is correct,
        throw a type error otherwise
        """
        source.exp_check_result_h(val, opts)

##--|
