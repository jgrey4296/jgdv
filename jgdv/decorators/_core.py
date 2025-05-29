#!/usr/bin/env python2
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import functools as ftz
import inspect
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import sys
import time
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
import jgdv.errors
from jgdv.debugging import TraceBuilder
from jgdv.mixins.annotate import Subclasser
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
import typing
from typing import cast, assert_type, assert_never
from typing import Generic, NewType
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
from . import _interface as API  # noqa: N812
from ._interface import Signature, Decorable, Decorated, DForm_e, Decorator_p

if typing.TYPE_CHECKING:
    import types
    import enum
    from typing import Final, ClassVar, Any, LiteralString
    from typing import Never, Self, Literal, TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Either, Func
    from jgdv._abstract.types import Method

##--|
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# TODO use ideas from pytest.mark
# TODO use strang for mark/data keys
ProtoMeta : Final[type] = type(Protocol)
#--|

class DecoratorMeta(ProtoMeta):

    @overload
    def __call__[T](cls:type[API.Decorator_p], target:type[T], *args:Any, **kwargs:Any) -> type[T]: ...  # noqa: ANN401, N805

    @overload
    def __call__(cls:type[API.Decorator_p], *args:Any, **kwargs:Any) -> type[API.Decorator_p]: ...  # noqa: ANN401, N805

    def __call__(cls, *args:Any, **kwargs:Any):  # noqa: N805
        """ When called with a class as the first arg, builds and calls the decorator on it """
        dec : API.Decorator_p
        dec = cls.__new__(cls)
        assert(isinstance(dec, cls))
        dec.__init__(*args, **kwargs) # type: ignore[misc]
        return dec

class _DecAnnotate_m:
    """ Utils for manipulating annotations related to the decorator
    Annotations for a decorator are stored in a dict entry.
    of the form: '{annotation_prefix}:{data_suffix}'
    """

    def data_key(self:Decorator_p) -> str:
        if not self._data_key:
            self._data_key = f"{self._annotation_prefix}:{self._data_suffix}"

        assert(self._data_key is not None)
        return self._data_key

    def annotate_decorable(self:Decorator_p, target:Decorable) -> list:
        """
        Essentially: target[data_key] += self.{data_key}[:]
        """
        current = target.__annotations__.get(self.data_key(), [])
        match self._build_annotations_h(target, current):
            case []:
                # No Annotations to add
                return []
            case [*xs]:
                logging.info("Applying Annotations to: %s", target)
                target.__annotations__[self.data_key()] = xs
                return xs
            case x:
                msg = "Bad annotation type"
                raise TypeError(msg, x)

    def get_annotations(self:Decorator_p, target:Decorable) -> list[str]:
        """ Get the annotations of the target """
        if not hasattr(target, API.ATTR_TARGET):
            return []
        bottom  = self._unwrap(target)
        data    = bottom.__annotations__.get(self.data_key(), [])
        return data[:]

    def is_annotated(self:Decorator_p, target:Decorable) -> bool:
        logging.info("Testing for annotation data: %s : %s", self.data_key(), target)
        match target:
            case x if not hasattr(x, API.ATTR_TARGET):
                return False
            case type():
                return self._data_key in target.__annotations__
            case _:
                return self._data_key in target.__annotations__

class _DecMark_m:
    """ For Marking and checking Decorables.
    Marks are for easily testing if Decorator decorated something already

    """

    def mark_key(self:Decorator_p) -> str:
        if not self._mark_key:
            self._mark_key = f"{self._annotation_prefix}:{self._mark_suffix}"

        assert(self._mark_key is not None)
        return self._mark_key

    def apply_mark(self:Decorator_p, *args:Decorable) -> None:
        """ Mark the UNWRAPPED, original target as already decorated """
        logging.info("Applying Mark %s to : %s", self._mark_key, args)
        for x in args:
            x.__annotations__[self.mark_key()] = True

    def is_marked(self:Decorator_p, target:Decorable) -> bool:
        logging.info("Testing for mark: %s : %s", self._mark_key, target)
        match target:
            case x if not hasattr(x, API.ATTR_TARGET):
                return False
            case type() as x:
                return self._mark_key in x.__annotations__
            case x:
                local_key = self._mark_key in x.__annotations__
                return local_key or self.is_marked(type(target))

class _DecWrap_m:
    """ Utils for unwrapping and wrapping a  """

    def _unwrap(self:Decorator_p, target:Decorated) -> Decorable:
        """ Get the un-decorated function if there is one """
        match target:
            case type():
                return target
            case x:
                return inspect.unwrap(x)

    def _unwrapped_depth(self:Decorator_p, target:Decorated) -> int:
        """ the code of inspect.unwrap, but used for counting the unwrap depth """
        logging.info("Counting Wrap Depth of: %s", target)
        f               = target
        memo            = {id(f): f}
        depth           = 0
        recursion_limit = sys.getrecursionlimit()
        while not isinstance(f, type) and hasattr(f, API.WRAPPED):
            f = f.__wrapped__ # type: ignore[attr-defined]
            depth += 1
            id_func = id(f)
            if (id_func in memo) or (len(memo) >= recursion_limit):
                msg = f'wrapper loop when unwrapping {target!r}'
                raise ValueError(msg)
            memo[id_func] = f
        else:
            return depth

    def _build_wrapper[**I,O](self:Decorator_p, form:DForm_e, target:Decorable[I,O]) -> Maybe[Decorated[I,O]]:
        """ Create a new decoration using the appropriate hook """
        match form:
            case self.Form.CLASS:
                logging.info("Decorating class: %s", target)
                # Classes are a special case, Maybe modifying instead of wrapping
                assert(isinstance(target, type))
                return cast("Maybe[Decorated[I,O]]", self._wrap_class_h(target))
            case self.Form.METHOD:
                logging.info("Decorating Method: %s", target)
                # TODO if its actually a method type, will need to get the unbound fn
                return self._wrap_method_h(cast("types.MethodType", target))
            case self.Form.FUNC:
                logging.info("Decorating Function: %s", target)
                return self._wrap_fn_h(target)
            case x:
                msg = "Unexpected Decorable type"
                raise ValueError(msg, x)

    def _apply_onto(self:Decorator_p, wrapper:Decorated, target:Decorable) -> Decorated:
        """ Uses functools.update_wrapper,
        Modify cls._wrapper_assignments and cls._wrapper_updates as necessary
        """
        assert(wrapper is not None)
        logging.info("Applying wrapper to decorable: %s -> %s", wrapper, target)
        match target:
            case type():
                return wrapper
            case x:
                return ftz.update_wrapper(wrapper, x,
                                          assigned=self._wrapper_assignments,
                                          updated=self._wrapper_updates)

class _DecInspect_m:

    def _signature(self:Decorator_p, target:Decorable) -> Signature:
        return inspect.signature(target, follow_wrapped=False)

    def _discrim_form(self:Decorator_p, target:Decorable) -> DForm_e:
        """ Determine the type of the thing being decorated"""
        try:
            target = self._unwrap(target)
            if inspect.isclass(target):
                return self.Form.CLASS
            if inspect.ismethod(target):
                return self.Form.METHOD
            if inspect.ismethodwrapper(target):
                return self.Form.METHOD

            # A heuristic Fallback
            match self._signature(target).parameters.get("self", False):
                case False:
                    return self.Form.FUNC
                case _:
                    return self.Form.METHOD
        except TypeError as err:
            raise TypeError(*err.args) from None
        else:
            msg = "Unknown decoration target type"
            raise TypeError(msg, target)

class _DecoratorHooks_m:
    """ The main hooks used to actually specify the decoration """
    _builder : ClassVar[Subclasser] = Subclasser()

    def _wrap_method_h[**In, Out](self:Decorator_p, meth:Method[In,Out]) -> Decorated[In, Out]:
        """ Override this to add a decoration function to method """
        dec_name = self.dec_name()

        def _default_method_wrapper(*args:In.args, **kwargs:In.kwargs) -> Out:
            logging.debug("Calling Wrapped Method: %s of %s", meth.__qualname__, dec_name)
            return meth(*args, **kwargs)

        return cast("Method", _default_method_wrapper)

    def _wrap_fn_h[**In, Out](self:Decorator_p, fn:Func[In, Out]) -> Decorated[In, Out]:
        """ override this to add a decorator to a function """
        dec_name = self.dec_name()

        def _default_fn_wrapper(*args:In.args, **kwargs:In.kwargs) -> Out:
            logging.debug("Calling Wrapped Fn: %s : %s", fn.__qualname__, dec_name)
            return fn(*args, **kwargs)

        return cast("Method", _default_fn_wrapper)

    def _wrap_class_h[**I,O](self, cls:type[O]) -> Maybe[Decorated[I,O]]:
        """ Override this to decorate a class """
        return self._builder.make_subclass("DefaultWrappedClass", cls)

    def _validate_target_h(self:Decorator_p, target:Decorable, form:DForm_e, args:Maybe[list]=None) -> None:
        """ Abstract class for specialization.
        Given the original target, throw an error here if it isn't 'correct' in some way
        """
        pass

    def _validate_sig_h(self:Decorator_p, sig:Signature, form:DForm_e, args:Maybe[list]=None) -> None:
        pass

    def _build_annotations_h(self, target:Decorable, current:list) -> list:  # noqa: ARG002
        """ Given a list of the current annotation list,
        return its replacement
        """
        return []

##--|

class _DecoratorCombined_m(_DecAnnotate_m, _DecWrap_m, _DecMark_m, _DecInspect_m, _DecoratorHooks_m):
    """ Combines the util mixins """
    pass

##--|

class _DecIdempotentLogic_m:
    """ Decorate the passed target in an idempotent way """
    pass

##--|

class Decorator(_DecoratorCombined_m, Decorator_p, metaclass=DecoratorMeta): # type: ignore[misc]
    """
    The abstract Superclass of Decorators
    A subclass implements '_decoration_logic'
    """
    Form                 : ClassVar[type[DForm_e]] = DForm_e
    needs_args           : ClassVar[bool]          = False


    def __init__(self, *args:Any, prefix:Maybe[str]=None, mark:Maybe[str]=None, data:Maybe[str]=None) -> None:  # noqa: ANN401, ARG002
        # Ignores any args
        # TODO use strangs for mark and data key
        self._annotation_prefix   = prefix  or API.ANNOTATIONS_PREFIX
        self._mark_suffix         = mark    or self.__class__.__name__
        self._data_suffix         = data    or API.DATA_SUFFIX
        self._wrapper_assignments = list(ftz.WRAPPER_ASSIGNMENTS)
        self._wrapper_updates     = list(ftz.WRAPPER_UPDATES)
        self._mark_key            = None # type: ignore[assignment]
        self._data_key            = None # type: ignore[assignment]

    def __call__(self, target:Decorable) -> Decorated:
        try:
            decorated = self._decoration_logic(target)
        except Exception as err:  # noqa: BLE001
            # Capture all decoration exceptions,
            # and turn them into JGDVErrors,
            # So the traceback can be manipulated
            raise err.with_traceback(TraceBuilder()[1:]) from None
        else:
            assert(decorated is not None)
            return decorated

    def _decoration_logic[**I, O](self, target:Decorable[I,O]) -> Decorated[I,O]:
        """
        # need to wrap with my wrapper
        annotations = self.get_annotations(target)
        form, sig   = self._discrim_form(target), self._signature(target)
        # Verify the target, may raise exceptions
        self._validate_target_h(target, form, annotations)
        self._validate_sig_h(sig, form, annotations)
        """
        raise NotImplementedError()

    def dec_name(self) -> str:
        return self.__class__.__qualname__

##--|

class MonotonicDec(Decorator):
    """ The Base Monotonic Decorator

    Applying the decorator repeatedly adds successive decoration functions
    Monotonic's don't annotate
    """

    def _decoration_logic[**I, O](self, target:Decorable[I,O]) -> Decorated[I,O]:
        top, bottom = target, self._unwrap(target)
        form, sig = self._discrim_form(bottom), self._signature(bottom)

        self._validate_target_h(bottom, form)
        self._validate_sig_h(sig, form)
        match self._build_wrapper(form, bottom):
            case None:
                return top
            case wrapper if wrapper is top:
                return top
            case wrapper:
                self.apply_mark(wrapper, top, bottom)
                return self._apply_onto(wrapper, top)

class IdempotentDec(Decorator):
    """ The Base Idempotent Decorator

    Already decorated targets are 'marked' with _mark_key as an attr.

    Can annotate targets with metadata without modifying the runtime behaviour,
    or modify the runtime behaviour

    annotations are assigned as fn.__annotations[decorator._data_key] = []
    the mark as fn.__annotations__[decorator._mark_key] = True

    Moving data from wrapped to wrapper is taken care of,
    so no need for ftz.wraps in _wrap_method_h or _wrap_fn_h

    """

    def _decoration_logic(self, target:Decorable) -> Decorated:
        top, bottom = target, self._unwrap(target)
        match self.is_marked(bottom):
            case True if top is not bottom:
                # Already wrapped, nothing to do
                return top
            case True:
                msg = "A Marked Decorable doesn't have a wrapper"
                raise ValueError(msg, target)
            case False:
                form = self._discrim_form(bottom)

        match self._build_wrapper(form, bottom):
            case None:
                # Decorable was modified
                return top
            case type() as x:
                self.apply_mark(x, top, bottom)
                return x
            case wrapper if wrapper is top:
                self.apply_mark(wrapper, top, bottom)
                return top
            case wrapper:
                self.apply_mark(wrapper, top, bottom)
                return self._apply_onto(wrapper, top)

class MetaDec(Decorator):
    """
    Adds metadata without modifying runtime behaviour of target,
    Or validates a class

    ie: annotates without wrapping
    """

    def __init__(self, value:str|list[str], **kwargs) -> None:  # noqa: ANN003
        kwargs.setdefault("mark", "_meta_marked")
        kwargs.setdefault("data", "_meta_vals")
        super().__init__(**kwargs)
        match value:
            case list():
                self._data = value
            case _:
                self._data = [value]

    def _decoration_logic(self, target:Decorable) -> Decorated:
        top, bottom = target, self._unwrap(target)
        form, sig   = self._discrim_form(target), self._signature(bottom)
        annotations = self.annotate_decorable(bottom)
        # Verify the target, may raise exceptions
        self._validate_target_h(bottom, form, annotations)
        self._validate_sig_h(sig, form, annotations)
        return top

    def _build_annotations_h(self, target:Decorable, current:list) -> list:  # noqa: ARG002
        return [*current, *self._data]

class DataDec(IdempotentDec):
    """
    An extended IdempotentDec, which uses a data annotation
    on the original Decorable,
    to run the single wrapping function
    """

    def __init__(self, keys:str|list[str], **kwargs) -> None:  # noqa: ANN003
        kwargs.setdefault("mark", "_d_marked")
        kwargs.setdefault("data", "_d_vals")
        super().__init__(**kwargs)
        match keys:
            case list():
                self._data = keys
            case _:
                self._data = [keys]

    def _decoration_logic(self, target:Decorable) -> Decorated:
        top, bottom = target, self._unwrap(target)
        match self.annotate_decorable(bottom):
            case []:
                # No annotations added
                return top
            case list() as annots if top is not bottom and self.is_marked(bottom):
                # Theres a wrapper, and its mine
                # Verify the target, may raise exceptions
                form, sig = self._discrim_form(target), self._signature(bottom)
                self._validate_target_h(bottom, form, annots)
                self._validate_sig_h(sig, form, annots)
                return top
            case list() as annots:
                form, sig = self._discrim_form(target), self._signature(bottom)
                self._validate_target_h(bottom, form, annots)
                self._validate_sig_h(sig, form, annots)
                # Now handle the wrapping
                return super()._decoration_logic(top)
            case x:
                raise TypeError(type(x))

    def _build_annotations_h(self, target:Decorable, current:list) -> list:  # noqa: ARG002
        return [*self._data, *current]
