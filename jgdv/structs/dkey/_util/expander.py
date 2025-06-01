#!/usr/bin/env python3
"""

"""
# ruff: noqa: ARG002
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
from jgdv import identity_fn, Proto
from jgdv.decorators import DoMaybe
from jgdv.structs.strang import CodeReference, Strang
from .getter import ChainGetter as CG  # noqa: N817
from .. import _interface as API # noqa: N812
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
   from .._interface import Expandable_p, Key_p
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable

   from jgdv import Maybe, M_, Func, RxStr, Rx, Ident, FmtStr, Ctor
##--|
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

@Proto(API.Expander_p)
class DKeyExpander:
    """ A Static class to control expansion.

    In order it does::

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
    When one of them fails, then the expansion tries to return, in order::

        - a fallback value passed into the expansion call
        - a fallback value stored on construction of the key
        - None

    Redirection Rules::

        - Hit          || {test}  => state[test=>blah]  => blah
        - Soft Miss    || {test}  => state[test_=>blah] => {blah}
        - Hard Miss    || {test}  => state[...]         => fallback or None

    Indirect Keys act as::

        - Indirect Soft Hit ||  {test_}  => state[test_=>blah] => {blah}
        - Indirect Hard Hit ||  {test_}  => state[test=>blah]  => blah
        - Indirect Miss     ||  {test_} => state[...]          => {test_}

    """

    _ctor : Ctor[API.Key_p]

    def __init__(self) -> None:
        self._ctor = None # type: ignore[assignment]

    def set_ctor(self, ctor:Ctor[API.Key_p]) -> None:
        """ Dependency injection from DKey.__init_subclass__ """
        if self._ctor is not None:
            return

        self._ctor = ctor

    def redirect(self, source:API.Key_p, *sources:dict, **kwargs:Any) -> list[Maybe[API.ExpInst_d]]:  # noqa: ANN401
            return [self.expand(source, *sources, limit=1, **kwargs)]

    def expand(self, source:API.Key_p, *sources:dict, **kwargs:Any) -> Maybe[API.ExpInst_d]:  # noqa: ANN401, PLR0912
        logging.info("- Locally Expanding: %s : %s : multi=%s", repr(source), kwargs, source.data.multi)
        if source.MarkOf(source) is API.DKeyMark_e.NULL:
            return API.ExpInst_d(value=source, literal=True)

        match kwargs.get("fallback", source.data.fallback):
            case None:
                fallback = None
            case type() as ctor:
                x = ctor()
                fallback = API.ExpInst_d(value=x, literal=True)
            case API.ExpInst_d() as x:
                fallback = x
                logging.debug("Fallback %s -> %s", source, fallback.value)
            case x:
                fallback = API.ExpInst_d(value=x, literal=True)
                logging.debug("Fallback %s -> %s", source, fallback.value)

        full_sources = list(sources)
        full_sources += [x for x in self.extra_sources(source) if x not in full_sources]
        # Limit defaults to -1 / until completion
        # but recursions can pass in limits
        match kwargs.get("limit", None):
            case 0:
                return fallback or API.ExpInst_d(value=source, literal=True)
            case None | -1:
                limit = -1
            case x if x < -1:
                limit = -1
            case x:
                limit = x - 1

        targets       = self.pre_lookup(full_sources, kwargs, source=source)
        # These are Maybe monads:
        vals          = self.do_lookup(targets, full_sources, kwargs, source=source)
        vals          = self.pre_recurse(vals, sources, kwargs, source=source)
        vals          = self.do_recursion(vals, full_sources, kwargs, max_rec=limit, source=source)
        flattened     = self.flatten(vals, kwargs, source=source)
        coerced       = self.coerce_result(flattened, kwargs, source=source)
        final_val     = self.finalise(coerced, kwargs, source=source)
        self.check_result(source, final_val, kwargs)
        match final_val:
            case None:
                logging.debug("Expansion Failed, using fallback")
                return fallback
            case API.ExpInst_d(literal=False) as x:
                msg = "Expansion didn't result in a literal"
                raise ValueError(msg, x, source)
            case API.ExpInst_d() as x:
                logging.info("- %s -> %s", source, final_val)
                return x
            case x:
                raise TypeError(type(x))

    def extra_sources(self, source:API.Key_p) -> list[Any]:
        match source.exp_extra_sources_h():
            case None:
                return []
            case list() as xs:
                return xs
            case x:
                raise TypeError(type(x))

    def pre_lookup(self, sources:list[dict], opts:dict, *, source:API.Key_p) -> list[list[API.ExpInst_d]]:
        """
        returns a list (L1) of lists (L2) of target tuples (T).
        When looked up, For each L2, the first T that returns a value is added
        to the final result
        """
        match source.exp_pre_lookup_h(sources, opts):
            case [] | None:
                return [[
                    API.ExpInst_d(value=f"{source:d}"),
                    API.ExpInst_d(value=f"{source:i}", lift=True),
                ]]
            case list() as xs:
                return xs
            case x:
                raise TypeError(type(x))

    @DoMaybe()
    def do_lookup(self, targets:list[list[API.ExpInst_d]], sources:list, opts:dict, *, source:API.Key_p) -> Maybe[list]:
        """ customisable method for each key subtype
            Target is a list (L1) of lists (L2) of target tuples (T).
            For each L2, the first T that returns a value is added to the final result
            """
        result = []
        for target in targets:
            match CG.lookup(target, sources, ctor=self._ctor):
                case None:
                    logging.debug("Lookup Failed for: %s", target)
                    return []
                case API.ExpInst_d(value=API.Key_p() as key, rec=-1) as res if source == key:
                    res.rec = API.RECURSION_GUARD
                    result.append(res)
                case API.ExpInst_d() as x:
                    result.append(x)
                case x:
                    msg = "LookupTarget didn't return an API.ExpInst_d"
                    raise TypeError(msg, x)
        else:
            return result

    @DoMaybe()
    def pre_recurse(self, insts:list[API.ExpInst_d], sources:list[dict], opts:dict, *, source:API.Key_p) -> Maybe[list[API.ExpInst_d]]:
        """ Produces a list[Key|Val|(Key, rec:int)]"""
        match source.exp_pre_recurse_h(insts, sources, opts):
            case None:
                return insts
            case list() as newinsts:
                return newinsts
            case x:
                raise TypeError(type(x))

    @DoMaybe()
    def do_recursion(self, insts:list[API.ExpInst_d], sources:list[dict], opts:dict, max_rec:int=API.RECURSION_GUARD, *, source:API.Key_p) -> Maybe[list[API.ExpInst_d]]:  # noqa: PLR0912
        """
        For values that can expand futher, try to expand them

        """
        result = []
        logging.debug("Recursing: %r", source)
        for x in insts:
            match x:
                case API.ExpInst_d(literal=True) | API.ExpInst_d(rec=0) as res:
                    result.append(res)
                case API.ExpInst_d(value=API.Key_p() as key, rec=-1) if key is source or key == source:
                    msg = "Unrestrained Recursive Expansion"
                    raise RecursionError(msg, source)
                case API.ExpInst_d(value=API.Key_p() as key, rec=-1, fallback=fallback, lift=lift):
                    match self.expand(key, *sources, limit=max_rec, fallback=fallback):
                        case None if lift:
                            return [API.ExpInst_d(value=as_key, literal=True)]
                        case None:
                            return []
                        case API.ExpInst_d() as exp if lift:
                            exp.convert = False
                            result.append(exp)
                        case API.ExpInst_d() as exp:
                            result.append(exp)
                case API.ExpInst_d(value=str() as key, rec=-1, fallback=fallback, lift=lift):
                    as_key = self._ctor(key)
                    match self.expand(as_key, *sources, limit=max_rec, fallback=fallback):
                        case None if lift:
                            return [API.ExpInst_d(value=as_key, literal=True)]
                        case None:
                            return []
                        case API.ExpInst_d() as exp if lift:
                            exp.convert = False
                            result.append(exp)
                        case API.ExpInst_d() as exp:
                            result.append(exp)

                case API.ExpInst_d(value=API.Key_p() as key, rec=rec, fallback=fallback, lift=lift):
                    new_limit = min(max_rec, rec)
                    match self.expand(key, *sources, limit=new_limit, fallback=fallback):
                        case None if lift:
                            return [API.ExpInst_d(value=key, literal=True)]
                        case None:
                            return []
                        case API.ExpInst_d() as exp:
                            result.append(exp)
                        case other:
                            raise TypeError(type(other))
                case API.ExpInst_d(value=str() as key, rec=rec, fallback=fallback, lift=lift):
                    new_limit = min(max_rec, rec)
                    as_key = self._ctor(key)
                    match self.expand(as_key, *sources, limit=new_limit, fallback=fallback):
                        case None if lift:
                            return [API.ExpInst_d(value=as_key, literal=True)]
                        case None:
                            return []
                        case API.ExpInst_d() as exp:
                            result.append(exp)
                        case other:
                            raise TypeError(type(other))
                case API.ExpInst_d() as x:
                    result.append(x)
                case x:
                    msg = "Unexpected Recursion Value"
                    raise TypeError(msg, x)
        else:
            logging.debug("Finished Recursing: %r : %r", source, result)
            return result

    @DoMaybe()
    def flatten(self, insts:list[API.ExpInst_d], opts:dict, *, source:API.Key_p) -> Maybe[API.ExpInst_d]:
        match insts:
            case []:
                return None

        match source.exp_flatten_h(insts, opts):
            case None:
                return insts[0]
            case False:
                return None
            case API.ExpInst_d() as x:
                return x
            case x:
                raise TypeError(type(x))

    @DoMaybe()
    def coerce_result(self, inst:API.ExpInst_d, opts:dict, *, source:API.Key_p) -> Maybe[API.ExpInst_d]:
        """
        Coerce the expanded value accoring to source's expansion type ctor
        """
        logging.debug("%r Type Coercion: %r : %s", source, inst, source.data.convert)
        result : Maybe[API.ExpInst_d] = None
        match source.exp_coerce_h(inst, opts):
            case API.ExpInst_d() as x:
                return x
            case None:
                pass

        match inst:
            case API.ExpInst_d(convert=False):
                # Conversion is off
                inst.literal = True
                result = inst
            case API.ExpInst_d(value=value, convert=None) if isinstance(source.data.expansion_type, type) and isinstance(value, source.data.expansion_type):
                # Type is already correct
                inst.literal = True
                result = inst
            case API.ExpInst_d(value=value, convert=None) if source.data.expansion_type is not identity_fn:
                # coerce a real ctor
                if not isinstance(value, source.data.expansion_type):
                    inst.value = source.data.expansion_type(value)
                inst.literal = True
                result = inst
            case API.ExpInst_d(convert=None) if source.data.convert is None:
                # No conv params
                inst.literal = True
                result = inst
            case API.ExpInst_d(convert=str() as conv):
                # Conv params in expinst
                result = self._coerce_result_by_conv_param(inst, conv, opts, source=source)
            case _ if source.data.convert:
                #  Conv params in source
                result = self._coerce_result_by_conv_param(inst, source.data.convert, opts, source=source)
            case API.ExpInst_d():
                result = inst
            case x:
                raise TypeError(type(x))

        ##--|
        return result

    @DoMaybe()
    def _coerce_result_by_conv_param(self, inst:API.ExpInst_d, conv:str, opts:dict, *, source:API.Key_p) -> Maybe[API.ExpInst_d]:
        """ really, keys with conv params should been built as a
        specialized registered type, to use an exp_final_hook
        """
        match conv:
            case "p":
                inst.value = pl.Path(inst.value).expanduser().resolve()
            case "s":
                inst.value = str(inst.value)
            case "S":
                inst.value = Strang(inst.value)
            case "c":
                inst.value = CodeReference(inst.value)
            case "i":
                inst.value = int(inst.value)
            case "f":
                inst.value = float(inst.value)
            case x:
                logging.warning("Unknown Conversion Parameter: %s", x)
                return None

        return inst

    @DoMaybe()
    def finalise(self, inst:API.ExpInst_d, opts:dict, *, source:API.Key_p) -> Maybe[API.ExpInst_d]:
        match source.exp_final_h(inst, opts):
            case None:
                inst.literal = True
                return inst
            case False:
                return None
            case API.ExpInst_d() as x:
                return x
            case x:
                raise TypeError(type(x))

    @DoMaybe()
    def check_result(self, source:API.Key_p, inst:API.ExpInst_d, opts:dict) -> None:
        """ check the type of the expansion is correct,
        throw a type error otherwise
        """
        source.exp_check_result_h(inst, opts)

##--|
