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
from jgdv import identity_fn, Proto
from jgdv.decorators import MethodMaybe
from jgdv.structs.strang import CodeReference, Strang
from .. import _interface as API # noqa: N812
# ##-- end 1st party imports

from collections.abc import Mapping
from . import _interface as ExpAPI # noqa: N812
from ._interface import Expander_p, SourceChain_d
from ._interface import ExpInst_d, ExpInstChain_d
from .._interface import Key_p

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
    from collections.abc import Callable
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Generator
    from collections.abc import Sequence, MutableMapping, Hashable

    from jgdv import Maybe, M_, Func, RxStr, Rx, Ident, FmtStr, Ctor
    from ._interface import Expandable_p
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
type ExpOpts                = ExpAPI.ExpOpts
type InstructionAlts        = list[ExpInst_d]
type InstructionExpansions  = list[ExpInst_d]
type InstructionList        = list[InstructionAlts|ExpInst_d]
DoMaybe                     = MethodMaybe()
# Body:

class InstructionFactory:
    _ctor : Maybe[type[Key_p]]

    def __init__(self, *, ctor:Maybe[type[Key_p]]=None) -> None:
        self._ctor = ctor

    def set_ctor(self, ctor:Maybe[type[Key_p]]) -> None:
        if ctor is None:
            return
        self._ctor = ctor

    def build_chains(self, val:ExpInst_d, opts:ExpOpts) -> list[ExpInstChain_d|ExpInst_d]:
        match val:
            case ExpInst_d(value=key) if hasattr(key, "exp_generate_chains_h"):
                return cast("list[ExpInstChain_d|ExpInst_d]", val.value.exp_generate_chains_h(val, self, opts))
            case ExpInst_d(value=Key_p() as key):
                chain = [
                    self.build_inst(key, val, opts, decrement=False),
                    self.lift_inst(f"{key:i}", val, opts, decrement=False, implicit=True),
                    self.null_inst(),
                ]
            case ExpInst_d(value=key):
                chain = [
                    self.build_inst(key, val, opts, decrement=False),
                    self.null_inst(),
                ]
            case x:
                raise TypeError(type(x))

        ##--|

        return [ExpInstChain_d(*[x for x in chain if x is not None], root=val.value)]

    def build_inst(self, val:Maybe, root:Maybe[ExpInst_d], opts:ExpOpts, *, decrement:bool=True) -> Maybe[ExpInst_d]:  # noqa: PLR0911
        x          : Any
        implicit   : bool
        lift       : bool
        ##--|
        assert(self._ctor is not None)
        lift, implicit = self._calc_lift(root, opts)
        ##--|
        match val:
            case None:
                return None
            case x if hasattr(x, "exp_to_inst_h"):
                return x.exp_to_inst_h(root, self) # type: ignore[no-any-return]
            case API.NonKey_p() as key:
                return self.literal_inst(key)
            case API.Key_p() as key:
                rec_count  : Maybe[int]  = self._calc_recursion(key, root, opts, decrement=decrement)
                return ExpInst_d(value=key,
                                 convert=key.data.convert,
                                 rec=rec_count if rec_count is not None else key.data.max_expansions,
                                 )
            case x if lift:
                return self.lift_inst(x, root, opts, decrement=decrement, implicit=implicit)
            case pl.Path() | str() as x:
                return self.lift_inst(str(x), root, opts, decrement=decrement, implicit=implicit)
            case x:
                return self.literal_inst(x)

    def literal_inst(self, val:Any) -> ExpInst_d:  # noqa: ANN401
        return ExpInst_d(value=val, literal=True)

    def lift_inst(self, val:str, root:Maybe[ExpInst_d], opts:ExpOpts, *, decrement:bool=False, implicit:bool=False) -> ExpInst_d:
        assert(self._ctor               is               not               None)
        key        : Key_p            = self._ctor(val, implicit=implicit)  # type: ignore[call-arg]
        rec_count  : Maybe[int]       = self._calc_recursion(key, root, opts, decrement=decrement)
        convert    : Maybe[str|bool]  = key.data.convert
        match root:
            case None:
                pass
            case ExpInst_d(convert=convert):
                pass
        return ExpInst_d(value=key,
                         convert=convert,
                         rec=rec_count)

    def null_inst(self) -> ExpInst_d:
        return ExpInst_d(value=None, literal=True)
    ##--|

    def _calc_recursion(self, key:Maybe[Key_p], val:Maybe[ExpInst_d], opts:ExpOpts, *, decrement:bool=True) -> Maybe[int]:
        rec_count : Maybe[int] = None
        match val:
            case _ if "rec" in opts:
                rec_count = opts.get("rec", None)
            case ExpInst_d(rec=int() as rec_count):
                pass
            case ExpInst_d(rec=int() as rec_count):
                pass
            case _:
                pass
        match key:
            case None:
                pass
            case Key_p() as k if rec_count is None:
                rec_count = k.data.max_expansions

        if decrement and rec_count and 0 < rec_count:
            rec_count -= 1

        if val and val.value == key and rec_count is None:
            rec_count = API.RECURSION_GUARD

        return rec_count

    def _calc_lift(self, val:Maybe[ExpInst_d], opts:ExpOpts) -> tuple[bool, bool]:  # noqa: ARG002
        match val:
            case ExpInst_d(value=API.IndirectKey_p(), lift=bool() as lift):
                return lift, True
            case ExpInst_d(lift=bool() as lift):
                return lift, False
            case ExpInst_d(lift=[bool() as lift, bool() as implicit]):
                return lift, implicit
            case _:
                return False, False
##--|

@Proto(Expander_p[API.Key_p])
class DKeyExpanderStack:
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
    _factory : ClassVar[InstructionFactory] = InstructionFactory()
    _ctor : Ctor[API.Key_p]

    def __init__(self, *, ctor:Maybe[Ctor[API.Key_p]]=None) -> None:
        self._factory.set_ctor(ctor)

    def set_ctor(self, ctor:Ctor[API.Key_p]) -> None:
        """ Dependency injection from DKey.__init_subclass__ """
        self._factory.set_ctor(ctor)

    ##--|

    def redirect(self, source:API.Key_p, *sources:ExpAPI.SourceBases, **kwargs:Any) -> list[Maybe[ExpInst_d]]:  # noqa: ANN401
            return [self.expand(source, *sources, limit=1, **kwargs)]

    def expand(self, key:API.Key_p, *sources:ExpAPI.SourceBases|SourceChain_d, **kwargs:Any) -> Maybe[ExpInst_d]:  # noqa: ANN401, PLR0912, PLR0915
        """ The entry point for expanding a key """
        x : Any
        stack         : list[ExpInst_d|ExpInstChain_d|None]
        result_stack  : list[ExpInst_d|None]

        ##--|
        logging.info("- Expanding: [%s]", repr(key))
        if key.MarkOf(key) is False:
            return ExpInst_d(value=key, literal=True)

        root          = self._factory.build_inst(key, None, {"rec":kwargs.get("limit", None), **kwargs}, decrement=False)
        assert(root is not None)
        stack         = [root]
        result_stack  = []
        source_chain  = SourceChain_d(*sources)
        ## Pop each expansion from the stack,
        ## Adding new expansions back to it,
        ## and literals to the result stack.
        ## Merge instructions trigger result stack entries to be consumed
        while bool(stack):
            logging.info("Stack: %s", stack)
            curr = stack.pop()
            match curr:
                case None | ExpInst_d(value=None):
                    logging.info("[Stack Clear]")
                    stack         = []
                    result_stack  = []
                case ExpInst_d(value=API.NonKey_p()) | ExpInst_d(literal=True) | ExpInst_d(rec=0) as inst:
                    logging.info("[Result shift]: %s", inst)
                    value = self.coerce_result(inst, None, kwargs)
                    result_stack.append(value)
                case ExpInst_d(value=API.Key_p()) as inst:
                    logging.info("[Build Chain]: %s / %s", str(inst.value), result_stack)
                    stack += self._factory.build_chains(inst, kwargs)
                case ExpInstChain_d(merge=int() as count) as inst:
                    logging.info("[Merge Chain]: %s / %s", str(inst.root), result_stack)
                    values, result_stack = reversed(result_stack[-count:]), result_stack[:-count]
                    value         = self.flatten(list(values), inst.root, kwargs)
                    value         = self.coerce_result(value, inst.root, kwargs)
                    self.check_result(value, inst.root, kwargs)
                    result_stack.append(value)
                case ExpInstChain_d() as inst:
                    logging.info("[Lookup Chain]: %s / %s", str(inst.root), result_stack)
                    lookup = self.do_lookup(inst, source_chain, kwargs)
                    stack.append(lookup)
                case x:
                    raise TypeError(type(x))

        else:
            logging.info("Result Stack: %s", result_stack)
            match root.value.data.fallback, kwargs:
                case _, {"fallback": fallback}:
                    pass
                case fallback, _:
                    pass
                case _:
                    fallback = None

            match result_stack:
                case [] | [ExpInst_d(value=None)] | [None]:
                    match fallback:
                        case None:
                            return None
                        case type() as fb_type:
                            return self._factory.literal_inst(fb_type())
                        case fb:
                            return self._factory.literal_inst(fb)
                case [ExpInst_d(value=API.NonKey_p()) as x] | [ExpInst_d(literal=True) as x]:
                    logging.info("|-| %s -> %s", key, x)
                    return self.finalise(x, root.value, kwargs)
                case [ExpInst_d() as x]:
                    msg = "Expansion didn't result in a literal"
                    raise ValueError(msg, x, key)
                case [*_]:
                    msg = "Expansion finished with unmerged results"
                    raise ValueError(msg, result_stack)
                case x:
                    raise TypeError(type(x))
    ##--| Expansion phases

    def do_lookup(self, target:ExpInstChain_d, sources:SourceChain_d, opts:ExpOpts)  -> Maybe[ExpInst_d]:
        """ customisable method for each key subtype
            Target is a list (L1) of lists (L2) of target tuples (T).
            For each L2, the first T that returns a value is added to the final result
            """
        logging.debug("- Lookup: %s", target)
        sources = self.extra_sources(target, sources)
        match sources.lookup(target):
            case None:
                logging.debug("Lookup Failed for: %s", target)
                return None
            case ExpInst_d() as val:
                return val
            case x, y:
                return self._factory.build_inst(x, y, opts)
            case x:
                msg = "Invalid lookup result"
                raise TypeError(msg, x)

    def extra_sources(self, chain:ExpInstChain_d, sources:SourceChain_d) -> SourceChain_d:
        x : Any
        extended : SourceChain_d
        match chain.root:
            case x if not hasattr(x, "exp_extra_sources_h"):
                return sources
            case x:
                extended = x.exp_extra_sources_h(sources)
                assert(extended is not sources)
                return extended

    def flatten(self, values:list[Maybe[ExpInst_d]], root:Key_p, opts:ExpOpts) -> Maybe[ExpInst_d]:
        """
        Flatten separate expansions into a single value
        """
        x : Any
        match values:
            case _ if hasattr(root,"exp_flatten_h"):
                return cast("Maybe[ExpInst_d]", root.exp_flatten_h(values, self._factory, opts))
            case []:
                return None
            case [x, *_]:
                return x
            case x:
                raise TypeError(type(x))

    def coerce_result(self, inst:Maybe[ExpInst_d], root:Maybe[API.Key_p], opts:ExpOpts) -> Maybe[ExpInst_d]:  # noqa: PLR0912
        """
        Coerce the expanded value accoring to source's expansion type ctor
        """
        param         : str
        root_convert  : Maybe[str]        = root.data.convert if root else None
        root_etype    : Maybe[Callable]   = root.data.expansion_type if root else None
        inst_convert  : Maybe[str|bool]   = None
        inst_etype    : Maybe[Callable]   = None
        result        : Maybe[ExpInst_d]  = None
        ##--|
        match inst:
            case None:
                return None
            case ExpInst_d(value=API.Key_p() as k, convert=inst_convert):
                inst_etype = k.data.expansion_type
            case _:
                pass

        if root and hasattr(root, "exp_coerce_h"):
            return cast("Maybe[ExpInst_d]", root.exp_coerce_h(inst, self._factory, opts))

        match (root_etype, root_convert), (inst_etype, inst_convert):
            case _, [_, False]: # Conversion is off
                result = inst
            case [type() as x, None], _: # theres a root expansion type
                if not isinstance(inst.value, x):
                    result = self._factory.literal_inst(x(inst.value))
                else:
                    result = inst
            case [None, _], [type() as x, None]: # theres a inst expansion type
                if not isinstance(inst.value, x):
                    result = self._factory.literal_inst(x(inst.value))
                else:
                    result = inst
            case [_, x], [_, y] if (param:=str(y or x or "")) and bool(param): # conv param
                result = (self._coerce_result_by_conv_param(inst, param, opts)
                          or inst)
            case _:
                result = inst

        ##--|
        logging.debug("- Type Coerced: %r -> %r", root, result)
        result.literal = True
        return result

    def check_result(self, inst:Maybe[ExpInst_d], root:Key_p, opts:ExpOpts) -> None:
        """ check the type of the expansion is correct,
        throw a type error otherwise
        """
        if inst is None:
            return
        if not hasattr(root, "exp_check_result_h"):
            return

        root.exp_check_result_h(inst, opts)

    def finalise(self, inst:ExpInst_d, root:API.Key_p, opts:ExpOpts) -> Maybe[ExpInst_d]:
        """
        A place for any remaining modifications of the result or fallback value
        """
        if hasattr(root, "exp_final_h"):
            return cast("Maybe[ExpInst_d]", root.exp_final_h(inst, root, self._factory, opts))
        else:
            match self.coerce_result(inst, root, opts):
                case None:
                    return None
                case ExpInst_d() as coerced:
                    coerced.literal = True
                    return coerced
                case x:
                    raise TypeError(type(x))

    ##--| Utils

    def _coerce_result_by_conv_param(self, inst:ExpInst_d, conv:str, opts:ExpOpts) -> Maybe[ExpInst_d]:  # noqa: ARG002
        """ really, keys with conv params should been built as a
        specialized registered type, to use an exp_final_hook
        """
        match ExpAPI.EXPANSION_CONVERT_MAPPING.get(conv, None):
            case fn if callable(fn):
                val : Any = fn(inst.value)
                return self._factory.literal_inst(val)
            case None:
                return inst
            case x:
                logging.warning("Unknown Conversion Parameter: %s", x)
                return None
