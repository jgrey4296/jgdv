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
from .. import _interface as API # noqa: N812
# ##-- end 1st party imports

from . import _interface as ExpAPI # noqa: N812
from ._interface import Expander_p, ExpInst_d, SourceChain_d

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, Self, Any
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, overload
from collections.abc import Callable

if TYPE_CHECKING:
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, M_, Func, RxStr, Rx, Ident, FmtStr, Ctor
    from ._interface import Expandable_p
    from .._interface import Key_p
##--|
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
type ExpOpts          = ExpAPI.ExpOpts
type InstructionAlts  = ExpAPI.InstructionAlts
type InstructionList  = ExpAPI.InstructionList

# Body:

@Proto(Expander_p[API.Key_p])
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

    ##--|

    def redirect(self, source:API.Key_p, *sources:ExpAPI.SourceBases, **kwargs:Any) -> list[Maybe[ExpInst_d]]:  # noqa: ANN401
            return [self.expand(source, *sources, limit=1, **kwargs)]

    def expand(self, key:API.Key_p, *sources:ExpAPI.SourceBases|SourceChain_d, **kwargs:Any) -> Maybe[ExpInst_d]:  # noqa: ANN401, PLR0912
        """ The entry point for expanding a key """
        full_sources  : SourceChain_d
        targets       : InstructionAlts
        alts          : Maybe[InstructionList]
        value         : Maybe[ExpInst_d]
        fallback      : Maybe[ExpInst_d]

        ##--|
        logging.info("- Expanding: [%s]", repr(key))
        if key.MarkOf(key) is API.DKeyMark_e.NULL:
            return ExpInst_d(value=key, literal=True)

        match kwargs.get("fallback", key.data.fallback):
            case None:
                fallback = None
            case type() as ctor:
                x = ctor()
                fallback = ExpInst_d(value=x, literal=True)
            case ExpInst_d() as x:
                fallback = x
            case x:
                fallback = ExpInst_d(value=x, literal=True)

        # Limit defaults to -1 / until completion
        # but recursions can pass in limits
        match kwargs.get("limit", key.data.max_expansions):
            case ExpAPI.NO_EXPANSIONS_PERMITTED:
                return fallback or ExpInst_d(value=key, literal=True)
            case None | ExpAPI.UNRESTRICTED_EXPANSION:
                limit = ExpAPI.UNRESTRICTED_EXPANSION
            case x if x < ExpAPI.UNRESTRICTED_EXPANSION:
                limit = ExpAPI.UNRESTRICTED_EXPANSION
            case x:
                # decrement the limit
                limit  = x - 1

        full_sources   = self.extra_sources(sources, source=key)
        targets        = self.generate_alternatives(full_sources, kwargs, source=key)
        # These are Maybe monads:
        alts       = self.do_lookup(targets, full_sources, kwargs, source=key)
        alts       = self.configure_recursion(alts, full_sources, kwargs, source=key)
        alts       = self.do_recursion(alts, full_sources, kwargs, max_rec=limit, source=key)
        value      = self.flatten(alts, kwargs, source=key)
        value      = self.coerce_result(value, kwargs, source=key)
        self.check_result(key, value, kwargs)
        match value:
            case None if fallback:
                logging.debug("|-| %s -> None, Fallback: %s", key, fallback)
                return self.finalise(fallback, kwargs, source=key)
            case None:
                return None
            case ExpInst_d(literal=False) as x:
                msg = "Expansion didn't result in a literal"
                raise ValueError(msg, x, key)
            case ExpInst_d() as x:
                logging.info("|-| %s -> %s", key, x)
                return self.finalise(x, kwargs, source=key)
            case x:
                raise TypeError(type(x))

    ##--| Expansion phases

    def extra_sources(self, sources:Iterable[ExpAPI.SourceBases|SourceChain_d], *, source:API.Key_p) -> SourceChain_d:
        x : Any
        mapping : SourceChain_d
        match sources:
            case [SourceChain_d() as x]:
                mapping = x
            case [*xs]:
                mapping = SourceChain_d(*xs, lifter=self._ctor)

        if not hasattr(source, "exp_extra_sources_h"):
            return mapping

        match source.exp_extra_sources_h(mapping):
            case SourceChain_d() as x:
                return x
            case x:
                raise TypeError(type(x))

    def generate_alternatives(self, sources:SourceChain_d, opts:ExpOpts, *, source:API.Key_p) -> InstructionAlts:
        """
        returns a list (L1) of lists (L2) of target tuples (T).
        When looked up, For each L2, the first T that returns a value is added
        to the final result
        """
        if not hasattr(source, "exp_generate_alternatives_h"):
            return [[
                source.to_exp_inst(),
                source.to_exp_inst(indirect=True, lift=True),
            ]]

        match source.exp_generate_alternatives_h(sources, opts):
            case [] | None:
                return [[
                    source.to_exp_inst(),
                    source.to_exp_inst(indirect=True, lift=True),
                ]]
            case list() as xs:
                return xs
            case x:
                raise TypeError(type(x))

    @DoMaybe()
    def do_lookup(self, targets:InstructionAlts, sources:SourceChain_d, opts:ExpOpts, *, source:API.Key_p) -> Maybe[InstructionList]:
        """ customisable method for each key subtype
            Target is a list (L1) of lists (L2) of target tuples (T).
            For each L2, the first T that returns a value is added to the final result
            """
        target : list[ExpInst_d]
        result = []
        logging.debug("- Lookup: %s", targets)
        for target in targets:
            match sources.lookup(target):
                case None:
                    logging.debug("Lookup Failed for: %s", target)
                    return []
                case ExpInst_d(value=API.Key_p() as key, rec=ExpAPI.UNRESTRICTED_EXPANSION) as res if source == key:
                    # guard against infinit recursion
                    res.rec = API.RECURSION_GUARD
                    result.append(res)
                case ExpInst_d() as x:
                    result.append(x)
                case x:
                    msg = "LookupTarget didn't return an ExpInst_d"
                    raise TypeError(msg, x)
        else:
            return result

    @DoMaybe()
    def configure_recursion(self, insts:InstructionList, sources:SourceChain_d, opts:ExpOpts, *, source:API.Key_p) -> Maybe[InstructionList]:
        """ Produces a list[Key|Val|(Key, rec:int)]"""
        if not hasattr(source, "exp_configure_recursion_h"):
            return insts

        match source.exp_configure_recursion_h(insts, sources, opts):
            case None:
                return insts
            case list() as newinsts:
                return newinsts
            case x:
                raise TypeError(type(x))

    @DoMaybe()
    def do_recursion(self, insts:InstructionList, sources:SourceChain_d, opts:ExpOpts, *, max_rec:int=API.RECURSION_GUARD, source:API.Key_p) -> Maybe[InstructionList]:  # noqa: PLR0912
        """
        For values that can expand futher, try to expand them

        """
        x : Any
        recurse_on  : Maybe[API.Key_p]
        result      : list[ExpInst_d]  = []

        if not bool(insts):
            return result
        logging.debug("- Recursing: %r : %s : %s", source, insts, max_rec)
        for inst in insts:
            recurse_on  = None
            # Decide if there should be a recursion
            match inst:
                case ExpInst_d(literal=True) | ExpInst_d(rec=ExpAPI.NO_EXPANSIONS_PERMITTED) as res:
                    result.append(res)
                case ExpInst_d(value=API.Key_p() as key, rec=ExpAPI.UNRESTRICTED_EXPANSION) if key is source or key == source:
                    msg = "Unrestrained Recursive Expansion"
                    raise RecursionError(msg, source)
                case ExpInst_d(value=API.Key_p() as key, rec=ExpAPI.UNRESTRICTED_EXPANSION):
                    recurse_on = key
                case ExpInst_d(value=API.Key_p() as key):
                    recurse_on  = key
                case ExpInst_d(value=str() as key):
                    recurse_on = self._ctor(key)
                case ExpInst_d(value=key):
                    recurse_on  = self._ctor(key)
                case x:
                    msg = "Unexpected Recursion Value"
                    raise TypeError(msg, x)

            # do the recursion
            if recurse_on is None:
                continue

            match inst.rec, max_rec:
                case ExpAPI.UNRESTRICTED_EXPANSION, x:
                    rec_limit = x
                case x, ExpAPI.UNRESTRICTED_EXPANSION:
                    rec_limit = x
                case int() as x, int() as y:
                    rec_limit = min(x, y)
            logging.debug("----")
            match self.expand(recurse_on, sources, limit=rec_limit, fallback=inst.fallback, convert=inst.convert):
                case None if inst.lift:
                    result.append(ExpInst_d(value=recurse_on, literal=True))
                case None:
                    pass
                case ExpInst_d() as exp if inst.lift:
                    exp.convert = False
                    result.append(exp)
                case ExpInst_d() as exp:
                    result.append(exp)
                case other:
                    raise TypeError(type(other))
            logging.debug("----")
        else:
            logging.debug("- Recursion Finished: %r : %r", source, result)
            return result

    @DoMaybe()
    def flatten(self, insts:InstructionList, opts:ExpOpts, *, source:API.Key_p) -> Maybe[ExpInst_d]:
        """
        Flatten separate expansions into a single value
        """
        match insts:
            case []:
                return None
            case [x, *_] if not hasattr(source ,"exp_flatten_h"):
                return x
            case _ if not hasattr(source ,"exp_flatten_h"):
                return None
            case _:
                pass

        match source.exp_flatten_h(insts, opts):
            case None:
                return None
            case ExpInst_d() as x:
                return x
            case x:
                raise TypeError(type(x))

    @DoMaybe()
    def coerce_result(self, inst:ExpInst_d, opts:ExpOpts, *, source:API.Key_p) -> Maybe[ExpInst_d]:
        """
        Coerce the expanded value accoring to source's expansion type ctor
        """

        result : Maybe[ExpInst_d] = None

        if hasattr(source, "exp_coerce_h"):
            match source.exp_coerce_h(inst, opts):
                case ExpInst_d() as x:
                    return x
                case None:
                    pass

        ##--|
        match inst:
            case ExpInst_d(convert=False):
                # Conversion is off
                result = inst
            case ExpInst_d(value=value, convert=None) if isinstance(source.data.expansion_type, type) and isinstance(value, source.data.expansion_type):
                # Type is already correct
                result = inst
            case ExpInst_d(value=value, convert=None) if source.data.expansion_type is not identity_fn:
                # coerce a real ctor
                if not isinstance(value, source.data.expansion_type):
                    inst.value = source.data.expansion_type(value)
                result = inst
            case ExpInst_d(convert=None) if source.data.convert is None:
                # No conv params
                result = inst
            case ExpInst_d(convert=str() as conv):
                # Conv params in expinst
                result = (self._coerce_result_by_conv_param(inst, conv, opts, source=source)
                          or inst)
            case ExpInst_d() if source.data.convert:
                #  Conv params in source
                result = (self._coerce_result_by_conv_param(inst, source.data.convert, opts, source=source)
                          or inst)
            case ExpInst_d():
                result = inst
            case x:
                raise TypeError(type(x))

        ##--|
        logging.debug("- Type Coerced: (%r) %s -> %s", source, source.data.convert, result)
        result.literal = True
        return result

    @DoMaybe()
    def finalise(self, inst:ExpInst_d, opts:ExpOpts, *, source:API.Key_p) -> Maybe[ExpInst_d]:
        """
        A place for any remaining modifications of the result or fallback value
        """
        if not hasattr(source, "exp_final_h"):
            inst.literal = True
            return inst

        match source.exp_final_h(inst, opts):
            case None:
                return None
            case ExpInst_d() as x:
                return x
            case x:
                raise TypeError(type(x))

    @DoMaybe()
    def check_result(self, source:API.Key_p, inst:ExpInst_d, opts:ExpOpts) -> None:
        """ check the type of the expansion is correct,
        throw a type error otherwise
        """
        if not hasattr(source, "exp_check_result_h"):
            return

        source.exp_check_result_h(inst, opts)

    ##--| Utils
    def _coerce_result_by_conv_param(self, inst:ExpInst_d, conv:str, opts:ExpOpts, *, source:API.Key_p) -> Maybe[ExpInst_d]:
        """ really, keys with conv params should been built as a
        specialized registered type, to use an exp_final_hook
        """
        match ExpAPI.EXPANSION_CONVERT_MAPPING.get(conv, None):
            case fn if callable(fn):
                val : Any = fn(inst.value)
                return ExpInst_d(value=val)
            case None:
                return inst
            case x:
                logging.warning("Unknown Conversion Parameter: %s", x)
                return None
