#!/usr/bin/env python3
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
import re
import time
import types as types_
import weakref
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import decorator
import keyword
import inspect
import more_itertools as mitz
from pydantic import BaseModel, Field, field_validator, model_validator
from jgdv.structs.strang import CodeReference

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe, FmtStr, Ident, Rx, Method, Func, Decorator
from jgdv.structs.dkey import errors as dkey_errs
from jgdv.structs.dkey.meta import DKey
from jgdv.decorators.base import MetaDecorator, DataDecorator, DecoratorAccessor_m, _TargetType_e

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

type Signature = inspect.Signature

KEY_PATTERN         : Final[FmtStr]               =  "{(.+?)}"
MAX_KEY_EXPANSIONS  : Final[int]                  = 10
ARGS_K              : Final[Ident]                = "args"
KWARGS_K            : Final[Ident]                = "kwargs"
PATTERN             : Final[Rx]                   = re.compile(KEY_PATTERN)
FAIL_PATTERN        : Final[Rx]                   = re.compile("[^a-zA-Z_{}/1-9-]")
EXPANSION_HINT      : Final[Ident]                = "_doot_expansion_hint"
HELP_HINT           : Final[Ident]                = "_doot_help_hint"
PARAM_IGNORES       : Final[list[str]]            = ["_", "_ex"]

class DKeyMetaDecorator(MetaDecorator):
    """ A Meta decorator that registers keys for input and output verification"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("mark", "_dkey_meta_marked")
        kwargs.setdefault("data", "_dkey_meta_vals")
        super().__init__(*args, **kwargs)

class DKeyExpansionDecorator(DataDecorator):
    """
    Utility class for idempotently decorating actions with auto-expanded keys

    """

    def __init__(self, keys:list[DKey], ignores:Maybe[list[str]]=None, **kwargs):
        kwargs.setdefault("mark", "_dkey_marked")
        kwargs.setdefault("data", "_dkey_vals")
        super().__init__(keys, **kwargs)
        self._param_ignores     : tuple[str, str] = ignores or PARAM_IGNORES

    def _wrap_method(self, fn:Method) -> Method:
        data_key = self._data_key

        def method_action_expansions(_self, spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, data_key)]
            except KeyError as err:
                logging.warning("Action State Expansion Failure: %s", err)
                return False
            else:
                all_args = (*call_args, *expansions)
                return fn(_self, spec, state, *all_args, **kwargs)

        # -
        return method_action_expansions

    def _wrap_fn(self, fn:Func) -> Func:
        data_key = self._data_key

        def fn_action_expansions(spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, data_key)]
            except KeyError as err:
                logging.warning("Action State Expansion Failure: %s", err)
                return False
            else:
                all_args = (*call_args, *expansions)
                return fn(spec, state, *all_args, **kwargs)

        # -
        return fn_action_expansions

    def _verify_signature(self, sig:Signature, ttype:_TargetType_e, args:list[DKey]) -> None:
        # Get the head args
        match ttype:
            case _TargetType_e.FUNC:
                head = ["spec", "state"]
            case _TargetType_e.METHOD:
                head = ["self", "spec", "state"]

        params      = list(sig.parameters)
        tail        = args or []

        # Check the head
        for x,y in zip(params, head):
            if x != y:
                raise TypeError("Mismatch in signature head", x, y)

        prefix_ig, suffix_ig = self._param_ignores
        # Then the tail, backwards, because the decorators are applied in reverse order
        for x,y in zip(params[::-1], tail[::-1]):
            key_str = str(y)
            if x.startswith(prefix_ig) or x.endswith(suffix_ig):
                logging.debug("Skipping: %s", x)
                continue

            if keyword.iskeyword(key_str):
                raise TypeError("Key is a keyword, use an alias like _{} or {}_ex", x, y)

            if not key_str.isidentifier():
                raise TypeError("Key is not an identifier, use an alias _{} or {}_ex", x,y)

            if x != y:
                raise TypeError("Mismatch in signature tail", x, y)

class _DKeyedMeta_m:
    """ Mixin for decorators that declare meta information,
    but doesnt modify the behaviour
    """

    @staticmethod
    def requires(*args, **kwargs) -> DKeyMetaDecorator:
        """ mark an action as requiring certain keys to in the state, but aren't expanded """
        keys = [DKey(x, implicit=True, mark=DKey.mark.NULL, **kwargs) for x in args]
        return DKeyMetaDecorator(keys)

    @staticmethod
    def returns(*args, **kwargs) -> DKeyMetaDecorator:
        """ mark an action as needing to return certain keys """
        keys = [DKey(x, implicit=True, mark=DKey.mark.NULL, **kwargs) for x in args]
        return DKeyMetaDecorator(keys)

class _DKeyedRetrieval_m(DecoratorAccessor_m):
    """ Mixin for decorators which modify the calling behaviour of the decoration target

    """

    _decoration_builder : ClassVar[type] = DKeyExpansionDecorator

    @staticmethod
    def formats(*args, **kwargs) -> Decorator:
        keys     = [DKey(x, implicit=True, mark=DKey.mark.STR, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def expands(*args, **kwargs) -> Decorator:
        """ mark an action as using expanded string keys """
        return DKeyed.formats(*args, **kwargs)

    @staticmethod
    def paths(*args, **kwargs) -> Decorator:
        """ mark an action as using expanded path keys """
        kwargs.setdefault("implicit", True)
        keys = [DKey(x, mark=DKey.mark.PATH, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def types(*args, **kwargs) -> Decorator:
        """ mark an action as using raw type keys """
        kwargs.setdefault("max_exp", 1)
        keys = [DKey(x, implicit=True, mark=DKey.mark.FREE, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def args(fn) -> Decorator:
        """ mark an action as using spec.args """
        keys = [DKey(ARGS_K, implicit=True, mark=DKey.mark.ARGS)]
        return DKeyed._build_decorator(keys)(fn)

    @staticmethod
    def kwargs(fn) -> Decorator:
        """ mark an action as using all kwargs"""
        keys = [DKey(KWARGS_K, implicit=True, mark=DKey.mark.KWARGS)]
        return DKeyed._build_decorator(keys)(fn)

    @staticmethod
    def redirects(*args, **kwargs) -> Decorator:
        """ mark an action as using redirection keys """
        keys = [DKey(x, implicit=True, mark=DKey.mark.REDIRECT, ctor=DKey, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def references(*args, **kwargs) -> Decorator:
        """ mark keys to use as to_coderef imports """
        keys = [DKey(x, implicit=True, mark=DKey.mark.CODE, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def postbox(*args, **kwargs) -> Decorator:
        keys = [DKey(x, implicit=True, mark=DKey.mark.POSTBOX, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

class DKeyed(_DKeyedRetrieval_m, _DKeyedMeta_m):
    """ Decorators for actions

    It registers arguments on an action and extracts them from the spec and state automatically.

    provides: expands/paths/types/requires/returns/args/kwargs/redirects
    The kwarg 'hint' takes a dict and passes the contents to the relevant expansion method as kwargs

    arguments are added to the tail of the action args, in order of the decorators.
    the name of the expansion is expected to be the name of the action parameter,
    with a "_" prepended if the name would conflict with a keyword., or with "_ex" as a suffix
    eg: @DKeyed.paths("from") -> def __call__(self, spec, state, _from):...
    or: @DKeyed.paths("from") -> def __call__(self, spec, state, from_ex):...
    """
    pass
