#!/usr/bin/env python2
"""


"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import abc
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

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe, Ident
from jgdv._abstract.protocols import Decorator_p

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

WRAPPED             : Final[str]       = "__wrapped__"
ANNOTATIONS_PREFIX  : Final[str]       = "__JGDV__"
MARK_SUFFIX         : Final[str]       = "_mark"
DATA_SUFFIX         : Final[str]       = "_data"

type Signature = inpec.Signature

class _TargetType_e(enum.Enum):

    CLASS    = enum.auto()
    FUNC     = enum.auto()
    METHOD   = enum.auto()

class DecoratorBase(Decorator_p):
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

    def __init__(self, *, prefix:Maybe[str]=None, mark:Maybe[str]=None, data:Maybe[str]=None):
        self._annotation_prefix   : str              = prefix  or ANNOTATIONS_PREFIX
        self._mark_suffix         : str              = mark    or MARK_SUFFIX
        self._data_suffix         : str              = data    or DATA_SUFFIX
        self._wrapper_assignments : list[str]        = list(ftz.WRAPPER_ASSIGNMENTS)
        self._wrapper_updates     : list[str]        = list(ftz.WRAPPER_UPDATES)
        self._mark_key            : str              = f"{self._annotation_prefix}:{self._mark_suffix}"
        self._data_key            : str              = f"{self._annotation_prefix}:{self._data_suffix}"

    def _wraps(self, wrapper, wrapped):
        return ftz.update_wrapper(wrapper, wrapped, assigned=self._wrapper_assignments, updated=self._wrapper_updates)

    def _unwrap(self, fn) -> Callable:
        """ Get the un-decorated function if there is one """
        return inspect.unwrap(fn)

    def _unwrapped_depth(self, fn) -> int:
        """ the code of inspect.unwrap, but used for getting the unwrap depth """
        f               = fn
        memo            = {id(f): f}
        depth           = 0
        recursion_limit = sys.getrecursionlimit()
        while not isinstance(f, type) and hasattr(f, WRAPPED):
            f = f.__wrapped__
            depth += 1
            id_func = id(f)
            if (id_func in memo) or (len(memo) >= recursion_limit):
                raise ValueError('wrapper loop when unwrapping {!r}'.format(fn))
            memo[id_func] = f

        return depth

    def _signature(self, fn) -> Signature:
        return inspect.signature(fn, follow_wrapped=False)

    def _target_type(self, fn) -> _TargetType_e:
        if inspect.isclass(fn):
            return _TargetType_e.CLASS
        if inspect.ismethod(fn):
            return _TargetType_e.METHOD
        if inspect.ismethodwrapper(fn):
            return _TargetType_e.METHOD

        match self._signature(fn).parameters.get("self", False):
            case False:
                return _TargetType_e.FUNC
            case _:
                return _TargetType_e.METHOD

        raise TypeError("Unknown decoration target type", fn)

    def __call__(self, fn):
        """ Decorate the passed target """
        orig              = fn
        fn                = self._unwrap(fn)
        t_type            = self._target_type(fn)
        total_annotations = self._update_annotations(fn)

        if self._is_marked(fn):
            assert(total_annotations == self.get_annotations(fn))
            self._verify_signature(self._signature(fn), t_type, total_annotations)
            self._verify_target(fn, t_type, total_annotations)
            return orig

        # Not already decorated
        self._verify_target(fn, t_type, total_annotations)
        self._verify_signature(self._signature(fn), t_type, total_annotations)

        # add wrapper by target type
        match t_type:
            case _TargetType_e.CLASS:
                wrapper = self._wrap_class(fn)
            case _TargetType_e.METHOD:
                wrapper = self._wrap_method(fn)
                updated_wrapper = self._wraps(wrapper, fn)
            case _TargetType_e.FUNC:
                wrapper = self._wrap_fn(fn)
                updated_wrapper = self._wraps(wrapper, fn)

        self._apply_mark(fn, wrapper)
        return updated_wrapper

    def _wrap_method(self, fn) -> Callable:
        """ Override this to add a decoration function to method """

        def basic_method_wrapper(_self, *args, **kwargs):
            logging.debug("Calling Wrapped Method: %s", fn.__qualname__)
            return fn(_self, *args, **kwargs)

        return basic_method_wrapper

    def _wrap_fn(self, fn) -> Callable:
        """ override this to add a decorator to a function """

        def basic_fn_wrapper(*args, **kwargs):
            logging.debug("Calling Wrapped Fn: %s", fn.__qualname__)
            return fn(*args, **kwargs)

        return basic_fn_wrapper

    def _wrap_class(self, cls) -> type:
        original        = cls.__call__
        wrapper         = self._wrap_method(original)
        updated_wrapper = self._wraps(wrapper, original)
        cls.__call__    = updated_wrapper
        return cls

    def _update_annotations(self, fn) -> list:
        """ Apply metadata to target
        Override this to specialize
        """
        fn.__dict__[self._data_key] = fn.__dict__.get(self._data_key, [])
        return []

    def _apply_mark(self, bottom:Callable, top:Callable=None) -> None:
        """ Mark the UNWRAPPED, original target as already decorated """
        assert(self._unwrapped_depth(bottom) == 0)
        bottom.__dict__[self._mark_key]      = True
        if top is not None:
            top.__dict__[self._mark_key]     = True

    def _is_marked(self, fn) -> bool:
        match self._target_type(fn):
            case _TargetType_e.CLASS:
                return self._mark_key in fn.__call__.__dict__
            case _:
                return self._mark_key in fn.__dict__

    def _verify_target(self, fn, ttype:_TargetType_e, args) -> None:
        """ Abstract class for specialization.
        Given the original target, throw an error here if it isn't 'correct' in some way
        """
        pass

    def _verify_signature(self, sig, ttype:_TargetType_e, args):
        pass

    def get_annotations(self, fn) -> list[str]:
        """ Get the annotations of the target """
        fn   = self._unwrap(fn)
        data = getattr(fn, self._data_key, [])
        return data[:]

class MetaDecorator(DecoratorBase):
    """
    Adds metadata without modifying runtime behaviour of target
    """

    def __init__(self, value:str|list[str], **kwargs):
        kwargs.setdefault("mark", "_meta_marked")
        kwargs.setdefault("data", "_meta_vals")
        super().__init__(**kwargs)
        match value:
            case list():
                self._data = value
            case _:
                self._data = [value]

    def _update_annotations(self, fn) -> list:
        """ Apply metadata to target

        prepend annotations, so written decorator order is the same as written arg order:
        (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        """
        data                        = self._data[:]
        new_annotations             = data + fn.__dict__.get(self._data_key, [])
        fn.__dict__[self._data_key] = new_annotations
        return new_annotations

class DataDecorator(DecoratorBase):
    """ Adds Data to the target for use in the decorator """

    def __init__(self, keys:str|list[str], **kwargs):
        kwargs.setdefault("mark", "_d_marked")
        kwargs.setdefault("data", "_d_vals")
        super().__init__(**kwargs)
        match keys:
            case list():
                self._data = keys
            case _:
                self._data = [keys]

    def __call__(self, fn):
        if not bool(self._data):
            return fn

        return super().__call__(fn)

    def _update_annotations(self, fn) -> list:
        """ Apply metadata to target

        prepend annotations, so written decorator order is the same as written arg order:
        (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        """
        data                        = self._data[:]
        new_annotations             = data + fn.__dict__.get(self._data_key, [])
        fn.__dict__[self._data_key] = new_annotations
        return new_annotations

class DecoratorAccessor_m:
    """ A Base Class for building Decorator Accessors like DKeyed.
    Holds a _decoration_builder class, and helps you build it
    """

    _decoration_builder : ClassVar[type] = DataDecorator

    @classmethod
    def _build_decorator(cls, keys) -> Decorator_p:
        return cls._decoration_builder(keys)

    @classmethod
    def get_keys(cls, fn) -> list[Ident]:
        """ Retrieve key annotations from a decorated function """
        dec = cls._build_decorator([])
        return dec.get_annotations(fn)
