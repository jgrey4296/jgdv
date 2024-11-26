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
import types
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
from tomlguard import TomlGuard
from jgdv.structs.code_ref import CodeReference

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv.structs.dkey import errors as dkey_errs
from jgdv._abstract.protocols import Key_p, SpecStruct_p, Decorator_p
from jgdv.structs.dkey.dkey import DKey
from jgdv.decorators.base import DataDecorator, DecoratorAccessor_m

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

KEY_PATTERN                                =  "{(.+?)}"
MAX_KEY_EXPANSIONS                         = 10
ARGS_K         : Final[str]                = "args"
KWARGS_K       : Final[str]                = "kwargs"

PATTERN        : Final[re.Pattern]         = re.compile(KEY_PATTERN)
FAIL_PATTERN   : Final[re.Pattern]         = re.compile("[^a-zA-Z_{}/0-9-]")
EXPANSION_HINT : Final[str]                = "_doot_expansion_hint"
HELP_HINT      : Final[str]                = "_doot_help_hint"

class DKeyExpansionDecorator(DataDecorator):
    """
    Utility class for idempotently decorating actions with auto-expanded keys
    """

    def __init__(self, keys:list[str], *, **kwargs):
        super().__init__(keys, **kwargs)
        self._param_ignores     : list[str]        = ignores or PARAM_IGNORES

    def _wrap_method(self, fn) -> Callable:
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

    def _wrap_fn(self, fn) -> Callable:
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

    def _update_annotations(self, fn) -> list:
        """ Apply metadata to target

        prepend annotations, so written decorator order is the same as written arg order:
        (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        """
        match self._data:
            case list():
                new_annotations = self._data + getattr(fn, self._data_key, [])
                setattr(fn, self._data_key, new_annotations)
                return new_annotations
            case _:
                raise TypeError("Unknown decoration key type")

    def _verify_target(self, fn, args) -> bool:
        match fn:
            case inspect.Signature():
                sig = fn
            case _:
                sig = self._signature(fn)

        match sig.parameters.get("self", None):
            case None:
                head_sig = ["spec", "state"]
            case _:
                head_sig = ["self", "spec", "state"]


    def _verify_signature(self, sig:Callable|inspect.Signature, head:list, tail=None) -> bool:
        params      = list(sig.parameters)
        tail        = tail or []

        for x,y in zip(params, head):
            if x != y:
                logging.warning("Mismatch in signature head: %s != %s", x, y)
                return False

        prefix_ig, suffix_ig = self._param_ignores
        for x,y in zip(params[::-1], tail[::-1]):
            key_str = str(y)
            if x.startswith(prefix_ig) or x.endswith(suffix_ig):
                logging.debug("Skipping: %s", x)
                continue

            if keyword.iskeyword(key_str):
                logging.warning("Key is a keyword, the function sig needs to use _{} or {}_ex: %s : %s", x, y)
                return False

            if not key_str.isidentifier():
                logging.warning("Key is not an identifier, the function sig needs to use _{} or {}_ex: %s : %s", x,y)
                return False

            if x != y:
                logging.warning("Mismatch in signature tail: %s != %s", x, y)
                return False

        return True

class DKeyedMetaKeys_m:

    @staticmethod
    def requires(*args, **kwargs):
        """ mark an action as requiring certain keys to be passed in """
        keys = [DKey(x, implicit=True, mark=DKey.mark.NULL, **kwargs) for x in args]
        return DKeyMetaDecorator(keys)

    @staticmethod
    def returns(*args, **kwargs):
        """ mark an action as needing to return certain keys """
        keys = [DKey(x, implicit=True, mark=DKey.mark.NULL, **kwargs) for x in args]
        return DKeyMetaDecorator(keys)

class DKeyed(DKeyedMetaKeys_m, DecoratorAccessor_m):
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

    _decoration_builder : ClassVar[type] = DKeyExpansionDecorator

    @staticmethod
    def formats(*args, **kwargs):
        keys     = [DKey(x, implicit=True, mark=DKey.mark.STR, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def expands(*args, **kwargs):
        """ mark an action as using expanded string keys """
        return DKeyed.formats(*args, **kwargs)

    @staticmethod
    def paths(*args, **kwargs):
        """ mark an action as using expanded path keys """
        kwargs['implicit'] = kwargs.get('implicit', True)
        keys = [DKey(x, mark=DKey.mark.PATH, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def types(*args, **kwargs):
        """ mark an action as using raw type keys """
        kwargs['max_exp'] = kwargs.get('max_exp', 1)
        keys = [DKey(x, implicit=True, mark=DKey.mark.FREE, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def args(fn):
        """ mark an action as using spec.args """
        keys = [DKey(ARGS_K, implicit=True, mark=DKey.mark.ARGS)]
        return DKeyed._build_decorator(keys)(fn)

    @staticmethod
    def kwargs(fn):
        """ mark an action as using all kwargs"""
        keys = [DKey(KWARGS_K, implicit=True, mark=DKey.mark.KWARGS)]
        return DKeyed._build_decorator(keys)(fn)

    @staticmethod
    def redirects(*args, **kwargs):
        """ mark an action as using redirection keys """
        keys = [DKey(x, implicit=True, mark=DKey.mark.REDIRECT, ctor=DKey, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def references(*args, **kwargs):
        """ mark keys to use as to_coderef imports """
        keys = [DKey(x, implicit=True, mark=DKey.mark.CODE, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)

    @staticmethod
    def postbox(*args, **kwargs):
        keys = [DKey(x, implicit=True, mark=DKey.mark.POSTBOX, **kwargs) for x in args]
        return DKeyed._build_decorator(keys)
