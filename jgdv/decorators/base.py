#!/usr/bin/env python2
"""

See EOF for license/metadata/notes as applicable
"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import abc

# import abc
import datetime
import enum
import functools as ftz
import inspect
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import decorator
from jgdv._abstract.protocols import Decorator_p

# ##-- end 3rd party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

FUNC_WRAPPED     : Final[str]                = "__wrapped__"
jgdv_ANNOTATIONS : Final[str]                = "__JGDV_ANNOTATIONS__"
WRAPPER          : Final[str]                = "__wrapper"

class JGDVDecorator(Decorator_p):
    """
    Utility class for idempotently decorating actions with auto-expanded keys
    """

    def __init__(self, keys, *, prefix=None, mark=None, data=None, ignores=None):
        self._data              = keys
        self._annotation_prefix = prefix  or jgdv_ANNOTATIONS
        self._mark_suffix       = mark    or "_keys_expansion_handled_"
        self._data_suffix       = data    or "_expansion_keys"
        self._param_ignores     = ignores or ["_", "_ex"]
        self._mark_key          = f"{self._annotation_prefix}:{self._mark_suffix}"
        self._data_key          = f"{self._annotation_prefix}:{self._data_suffix}"

    def __call__(self, fn):
        if not bool(self._data):
            return fn

        orig = fn
        fn   = self._unwrap(fn)
        # update annotations
        total_annotations = self._update_annotations(fn)

        if not self._verify_action(fn, total_annotations):
            raise TypeError("Annotations do not match signature", orig, fn, total_annotations)

        if self._is_marked(fn):
            self._update_annotations(orig)
            return orig

        # add wrapper
        is_func = inspect.signature(fn).parameters.get("self", None) is None

        match is_func:
            case False:
                wrapper = self._target_method(fn)
            case True:
                wrapper = self._target_fn(fn)

        return self._apply_mark(fn)

    def get_annotations(self, fn):
        fn = self._unwrap(fn)
        return getattr(fn, self._data_key, [])

    def _unwrap(self, fn) -> Callable:
        return inspect.unwrap(fn)

    def _target_method(self, fn) -> Callable:
        data_key = self._data_key

        @ftz.wraps(fn)
        def method_action_expansions(self, spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, data_key)]
            except KeyError as err:
                logging.warning("Action State Expansion Failure: %s", err)
                return False
            else:
                all_args = (*call_args, *expansions)
                return fn(self, spec, state, *all_args, **kwargs)

        # -
        return method_action_expansions

    def _target_fn(self, fn) -> Callable:
        data_key = self._data_key

        @ftz.wraps(fn)
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

    def _target_class(self, cls) -> type:
        original = cls.__call__
        cls.__call__ = self._target_method(cls.__call__)
        return cls

    def _update_annotations(self, fn) -> list:
        # prepend annotations, so written decorator order is the same as written arg order:
        # (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        new_annotations = self._data + getattr(fn, self._data_key, [])
        setattr(fn, self._data_key, new_annotations)
        return new_annotations

    def _is_marked(self, fn) -> bool:
        match fn:
            case type():
                return hasattr(fn, self._mark_key) or (fn.__call__, self._mark_key)
            case _:
                return hasattr(fn, self._mark_key)

    def _apply_mark(self, fn:Callable) -> Callable:
        unwrapped = self._unwrap(fn)
        setattr(unwrapped, self._mark_key, True)
        if unwrapped is not fn:
            setattr(fn, self._mark_key, True)

        return fn

    def _verify_action(self, fn, args) -> bool:
        return True
