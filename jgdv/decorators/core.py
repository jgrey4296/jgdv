#!/usr/bin/env python2
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import inspect
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import sys
import time
import types
import typing
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import decorator

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv._abstract.protocols import Decorator_p
import jgdv.errors

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type Signature = inspect.Signature

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

WRAPPED             : Final[str]       = "__wrapped__"
ANNOTATIONS_PREFIX  : Final[str]       = "__JGDV__"
MARK_SUFFIX         : Final[str]       = "_mark"
DATA_SUFFIX         : Final[str]       = "_data"

# TODO use ideas from pytest.mark

class _TargetType_e(enum.Enum):

    CLASS    = enum.auto()
    FUNC     = enum.auto()
    METHOD   = enum.auto()

class _DecAnnotate_m:

    def add_annotations(self, target, ttype:_TargetType_e) -> list:
        """ Update annotations, return a list of total annotations """
        return []

    def get_annotations(self, fn) -> list[str]:
        """ Get the annotations of the target """
        fn   = self._unwrap(fn)
        data = getattr(fn, self._data_key, [])
        return data[:]

    def _is_marked(self, target) -> bool:
        match target:
            case type():
                return self._mark_key in target.__dict__
            case _:
                return self._mark_key in target.__dict__

    def _apply_mark(self, *args:Callable) -> None:
        """ Mark the UNWRAPPED, original target as already decorated """
        for x in args:
            setattr(x, self._mark_key, True)

class _DecVerify_m:

    def _verify_target(self, target, ttype:_TargetType_e, args) -> None:
        """ Abstract class for specialization.
        Given the original target, throw an error here if it isn't 'correct' in some way
        """
        pass

    def _verify_signature(self, sig, ttype:_TargetType_e, args) -> None:
        pass

class _DecWrap_m:

    def _unwrap(self, target) -> Callable:
        """ Get the un-decorated function if there is one """
        return inspect.unwrap(target)

    def _wraps(self, wrapper, base):
        """ Like functools.wraps, but gives the the decorator class control.
        Modify cls._wrapper_assignments and cls._wrapper_updates as necessary
        """
        return ftz.update_wrapper(wrapper,
                                  base,
                                  assigned=self._wrapper_assignments,
                                  updated=self._wrapper_updates)

    def _unwrapped_depth(self, target) -> int:
        """ the code of inspect.unwrap, but used for counting the unwrap depth """
        f               = target
        memo            = {id(f): f}
        depth           = 0
        recursion_limit = sys.getrecursionlimit()
        while not isinstance(f, type) and hasattr(f, WRAPPED):
            f = f.__wrapped__
            depth += 1
            id_func = id(f)
            if (id_func in memo) or (len(memo) >= recursion_limit):
                raise ValueError('wrapper loop when unwrapping {!r}'.format(target))
            memo[id_func] = f

        return depth

class _DecInspect_m:

    def _signature(self, target) -> Signature:
        return inspect.signature(target, follow_wrapped=False)

    def _target_type(self, target) -> _TargetType_e:
        """ Determine the type of the thing being decorated"""
        target = self._unwrap(target)
        if inspect.isclass(target):
            return _TargetType_e.CLASS
        if inspect.ismethod(target):
            return _TargetType_e.METHOD
        if inspect.ismethodwrapper(target):
            return _TargetType_e.METHOD

        # A Fallback
        match self._signature(target).parameters.get("self", False):
            case False:
                return _TargetType_e.FUNC
            case _:
                return _TargetType_e.METHOD

        raise TypeError("Unknown decoration target type", target)

class _DecoratorUtil_m(_DecAnnotate_m, _DecVerify_m, _DecWrap_m, _DecInspect_m):

    def __call__(self, target):
        """ Decorate the passed target """
        orig, target, t_type = target, self._unwrap(target), self._target_type(target)
        total_annotations    = self.add_annotations(target, t_type)

        if self._is_marked(target):
            # Already Decorated, don't re-decorate, just update annotations
            assert(total_annotations == self.get_annotations(target))
            try:
                self._verify_signature(self._signature(target), t_type, total_annotations)
                self._verify_target(target, t_type, total_annotations)
            except jgdv.errors.JGDVError as err:
                err.args = [f"{target.__module__}:{target.__qualname__}", *err.args]
                raise err from None
            return orig

        # Not already decorated
        try:
            self._verify_target(target, t_type, total_annotations)
            self._verify_signature(self._signature(target), t_type, total_annotations)
        except jgdv.errors.JGDVError as err:
            err.args = [f"{target.__module__}:{target.__qualname__}", *err.args]
            raise err from None

        # add wrapper by target type
        match t_type:
            case _TargetType_e.CLASS:
                # Classes are a special case, Maybe modifying instead of wrapping
                wrapper = self._wrap_class(target) or target
                self._apply_mark(wrapper)
                return wrapper
            case _TargetType_e.METHOD:
                wrapper = self._wrap_method(target)
            case _TargetType_e.FUNC:
                wrapper = self._wrap_fn(target)

        assert(wrapper is not None)
        self._apply_mark(target, wrapper)
        updated_wrapper = self._wraps(wrapper, target)
        return updated_wrapper

    def _wrap_method(self, fn) -> Callable:
        """ Override this to add a decoration function to method """

        def _basic_method_wrapper(_self, *args, **kwargs):
            logging.debug("Calling Wrapped Method: %s", fn.__qualname__)
            return fn(_self, *args, **kwargs)

        return _basic_method_wrapper

    def _wrap_fn(self, fn) -> Callable:
        """ override this to add a decorator to a function """

        def _basic_fn_wrapper(*args, **kwargs):
            logging.debug("Calling Wrapped Fn: %s", fn.__qualname__)
            return fn(*args, **kwargs)

        return _basic_fn_wrapper

    def _wrap_class(self, cls:type) -> Maybe[type]:
        pass

class DecoratorBase(_DecoratorUtil_m, Decorator_p):
    """
    Utility Base class for idempotently decorating functions, methods, and classes

    Already decorated targets are 'marked' with _mark_key as an attr.

    Can annotate targets with metadata without modifying the runtime behaviour,
    or modify the runtime behaviour

    annotations are assigned as setattr(fn, DecoratorBase._data_key, [])
    the mark is set(fn, DecoratorBase._mark_key, True)

    Moving data from wrapped to wrapper is taken care of,
    so no need for ftz.wraps in _wrap_method or _wrap_fn
    """

    def __init__(self, prefix:Maybe[str]=None, mark:Maybe[str]=None, data:Maybe[str]=None):
        self._annotation_prefix   : str              = prefix  or ANNOTATIONS_PREFIX
        self._mark_suffix         : str              = mark    or self.__class__.__name__
        self._data_suffix         : str              = data    or DATA_SUFFIX
        self._wrapper_assignments : list[str]        = list(ftz.WRAPPER_ASSIGNMENTS)
        self._wrapper_updates     : list[str]        = list(ftz.WRAPPER_UPDATES)
        self._mark_key            : str              = f"{self._annotation_prefix}:{self._mark_suffix}"
        self._data_key            : str              = f"{self._annotation_prefix}:{self._data_suffix}"

    def add_annotations(self, target, ttype:_TargetType_e) -> list:
        """ Apply metadata to target
        """
        val = target.__dict__.get(self._data_key, [])
        setattr(target, self._data_key, val)
        return []
