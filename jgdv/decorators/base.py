#!/usr/bin/env python2
"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import inspect
import abc
from typing import Type
import decorator

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
        total_annotations = self._update_annotations(self, fn)

        if not self._verify_action(fn, total_annotations):
            raise TypeError("Annotations do not match signature", orig)

        if self._is_marked(fn):
            self._update_annotations(self, orig)
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
        raise NotImplementedError()

    def _update_annotations(self, fn) -> list:
        # prepend annotations, so written decorator order is the same as written arg order:
        # (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        new_annotations = self._data + getattr(fn, self._data_key, [])
        setattr(fn, self._data_key, new_annotations)
        return new_annotations

    def _is_marked(self, fn) -> bool:
        return hasattr(fn, self._mark_key)

    def _apply_mark(self, fn:Callable) -> Callable:
        setattr(fn, self._mark_key, True)
        return fn

    def _verify_action(self, fn, args) -> bool:
        match fn:
            case inspect.Signature():
                sig = fn
            case _:
                sig = inspect.signature(fn, follow_wrapped=False)

        match sig.parameters.get("self", None):
            case None:
                head_sig = ["spec", "state"]
            case _:
                head_sig = ["self", "spec", "state"]

        return self._verify_signature(sig, head_sig, args)

    def _verify_signature(self, sig:Callable|inspect.Signature, head:list, tail=None) -> bool:
        match sig:
            case inspect.Signature():
                pass
            case _:
                sig = inspect.signature(sig)

        params      = list(sig.parameters)
        tail        = tail or []

        for x,y in zip(params, head):
            if x != y:
                logging.debug("Mismatch in signature head: %s != %s", x, y)
                return False

        prefix_ig, suffix_ig = self._param_ignores
        for x,y in zip(params[::-1], tail[::-1]):
            key_str = str(y)
            if x.startswith(prefix_ig) or x.endswith(suffix_ig):
                continue
            if keyword.iskeyword(key_str):
                logging.debug("Key is a keyword, the function sig needs to use _{} or {}_ex: %s : %s", x, y)
                return False

            if not key_str.isidentifier():
                logging.debug("Key is not an identifier, the function sig needs to use _{} or {}_ex: %s : %s", x,y)
                return False

            if x != y:
                logging.debug("Mismatch in signature tail: %s != %s", x, y)
                return False
        else:
            return True
