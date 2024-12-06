"""
Utility decorators
"""
#pylint: disable=invalid-sequence-index
##-- imports
from __future__ import annotations

import logging as logmod
from enum import Enum
from functools import wraps
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Dict, Generic,
                    Iterable, Iterator, List, Mapping, Match, MutableMapping,
                    Optional, ParamSpec, Sequence, Set, Tuple, TypeAlias,
                    TypeVar, Union, cast)

##-- end imports

##-- logging
logging                                      = logmod.getLogger(__name__)
##-- end logging

import inspect

JGDV_ANNOTATIONS : Final[str]                = "__JGDV_ANNOTATIONS__"
KEYS_HANDLED     : Final[str]                = "_jgdv_keys_handler"
ORIG_ARGS        : Final[str]                = "_jgdv_orig_args"
KEY_ANNOTS       : Final[str]                = "_jgdv_keys"
FUNC_WRAPPED     : Final[str]                = "__wrapped__"
PARAM_PREFIX     : Final[str]                = "_"
PARAM_SUFFIX     : Final[str]                = "_ex"

class DecorationUtils:

    _annot = JGDV_ANNOTATIONS

    @staticmethod
    def _unwrap(fn:callable) -> callable:
        # if not hasattr(fn, FUNC_WRAPPED):
        #     return fn

        # return getattr(fn, FUNC_WRAPPED)
        return inspect.unwrap(fn)

    @staticmethod
    def verify_signature(fn, head:list, tail:list=None) -> bool:
        """
          Inspect the signature of a function, an check the parameter names are correct
        """
        match fn:
            case inspect.Signature():
                sig = fn
            case _:
                sig = inspect.signature(fn, follow_wrapped=False)

        params      = list(sig.parameters)
        tail        = tail or []

        for x,y in zip(params, head):
            if x != y:
                logging.debug("Mismatch in signature head: %s != %s", x, y)
                return False

        for x,y in zip(params[::-1], tail[::-1]):
            key_str = str(y)
            if x.startswith(PARAM_PREFIX) or x.endswith(PARAM_SUFFIX):
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

        return True

    def verify_action_signature(fn:Signature|callable, args:list) -> bool:
        """
          verify that a callable signature is [self?, spec, state, *keys]
        """
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

        return DecorationUtils.verify_signature(sig, head_sig, args)

    @staticmethod
    def manipulate_signature(fn, args) -> callable:
        pass

    @staticmethod
    def has_annotations(fn, *keys) -> bool:
        if not hasattr(fn, JGDV_ANNOTATIONS):
            return False

        annots = getattr(fn, JGDV_ANNOTATIONS)
        return all(key in annots for key in keys)

    @staticmethod
    def annotate(fn:callable, annots:dict|set) -> callable:
        """
          Annotate a function with additional information
          applies update to the wrapper and wrapped

          a dict updates the function dict directory,
          a set gets added to DecorationUtils._annot
        """
        unwrapped = DecorationUtils.unwrap(fn)
        match annots:
            case dict():
                fn.__dict__.update(annots)
            case set():
                if not hasattr(fn, JGDV_ANNOTATIONS):
                    setattr(fn, JGDV_ANNOTATIONS, set())

                annotations = getattr(fn, JGDV_ANNOTATIONS)
                annotations.update(annots)
        return fn

    @staticmethod
    def truncate_signature(fn):
        """
           actions are (self?, spec, state)
          with and extracted keys from the spec and state.
          This truncates the signature of the action to what is *called*, not what is *used*.

          TODO: could take a callable as the prototype to build the signature from
        """
        sig = inspect.signature(fn)
        min_index = len(sig.parameters) - len(getattr(fn, KEY_ANNOTS))
        newsig = sig.replace(parameters=list(sig.parameters.values())[:min_index])
        fn.__signature__ = newsig
        return fn

    @staticmethod
    def _update_key_annotations(fn, keys:list[JGDVKey]) -> True:
        """ update the declared expansion keys on the wrapped action """
        sig = inspect.signature(fn)

        # prepend annotations, so written decorator order is the same as written arg order:
        # (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        new_annotations = keys + getattr(fn, KEY_ANNOTS, [])
        setattr(fn, KEY_ANNOTS, new_annotations)

        if not DecorationUtils.verify_action_signature(sig, new_annotations):
            raise ValueError("Annotations do not match signature", sig)

        return True

    @staticmethod
    def prepare_expansion(keys:list[JGDVKey], fn):
        """ used as a partial fn. adds declared keys to a function,
          and idempotently adds the expansion decorator
        """
        is_func = True
        match DecorationUtils._unwrap(fn):
            case x if DecorationUtils.has_annotations(x, KEYS_HANDLED):
                DecorationUtils._update_key_annotations(x, keys)
                return fn
            case orig:
                is_func = inspect.signature(orig).parameters.get("self", None) is None
                DecorationUtils._update_key_annotations(x, keys)
                DecorationUtils.annotate(orig, {KEYS_HANDLED})

        match is_func:
            case False:
                wrapper = DecorationUtils.add_method_expander(fn)
            case True:
                wrapper = DecorationUtils.add_fn_expander(fn)

        return wrapper

    @staticmethod
    def add_method_expander(fn):

        @ftz.wraps(fn)
        def method_action_expansions(self, spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, KEY_ANNOTS)]
            except KeyError as err:
                printer.warning("Action State Expansion Failure: %s", err)
                return False
            all_args = (*call_args, *expansions)
            return fn(self, spec, state, *all_args, **kwargs)

        # -
        return method_action_expansions

    @staticmethod
    def add_fn_expander(fn):

        @ftz.wraps(fn)
        def fn_action_expansions(spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, KEY_ANNOTS)]
            except KeyError as err:
                printer.warning("Action State Expansion Failure: %s", err)
                return False
            all_args = (*call_args, *expansions)
            return fn(spec, state, *all_args, **kwargs)

        # -
        return fn_action_expansions

class _DecorationUtils_b:
    """
      utilities for decorators
    """

    @staticmethod
    def unwrap(fn:callable) -> callable:
        # if not hasattr(fn, FUNC_WRAPPED):
        #     return fn

        # return getattr(fn, FUNC_WRAPPED)
        return inspect.unwrap(fn)

    @staticmethod
    def verify_signature(fn, head:list, tail:list=None) -> bool:
        """
          Inspect the signature of a function, an check the parameter names are correct
        """
        match fn:
            case inspect.Signature():
                sig = fn
            case _:
                sig = inspect.signature(fn, follow_wrapped=False)

        params      = list(sig.parameters)
        tail        = tail or []

        for x,y in zip(params, head):
            if x != y:
                logging.debug("Mismatch in signature head: %s != %s", x, y)
                return False

        for x,y in zip(params[::-1], tail[::-1]):
            key_str = str(y)
            if x.startswith(PARAM_PREFIX) or x.endswith(PARAM_SUFFIX):
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

        return True

    @staticmethod
    def verify_action_signature(fn:Signature|callable, args:list) -> bool:
        """
          verify that a callable signature is [self?, spec, state, *keys]
        """
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

        return DecorationUtils.verify_signature(sig, head_sig, args)

    @staticmethod
    def manipulate_signature(fn, args) -> callable:
        raise NotImplementedError()

    @staticmethod
    def truncate_signature(fn):
        """
           actions are (self?, spec, state)
          with and extracted keys from the spec and state.
          This truncates the signature of the action to what is *called*, not what is *used*.

          TODO: could take a callable as the prototype to build the signature from
        """
        sig              = inspect.signature(fn)
        min_index        = len(sig.parameters) - len(getattr(fn, DecorationUtils._keys))
        newsig           = sig.replace(parameters=list(sig.parameters.values())[:min_index])
        fn.__signature__ = newsig
        return fn

    @staticmethod
    def has_annotations(fn, *keys) -> bool:
        """
          test a function for doot annotations
          unwraps a function if necessary
        """
        unwrapped = DecorationUtils.unwrap(fn)
        if not hasattr(unwrapped, DecorationUtils._annot):
            return False

        annots = getattr(unwrapped, DecorationUtils._annot)
        return all(key in annots for key in keys)

    @staticmethod
    def annotate(fn:callable, annots:dict|set) -> callable:
        """
          Annotate a function with additional information
          applies update to the wrapper and wrapped

          a dict updates the function dict directory,
          a set gets added to DecorationUtils._annot
        """
        unwrapped = DecorationUtils.unwrap(fn)
        match annots:
            case dict():
                unwrapped.__dict__.update(annots)
                if fn is not unwrapped:
                    fn.__dict__.update(annots)
                return fn
            case set() if not hasattr(unwrapped, DecorationUtils._annot):
                new_set = set()
                setattr(unwrapped, DecorationUtils._annot, new_set)
                if fn is not unwrapped:
                    setattr(fn, DecorationUtils._annot, new_set)
            case set():
                pass
            case _:
                raise TypeError("Tried to annotate a function with an unknown type", annots)

        annotations = getattr(unwrapped, DecorationUtils._annot)
        annotations.update(annots)

        return fn

    @staticmethod
    def _update_key_annotations(fn, keys:list[Key_p]) -> True:
        """ update the declared expansion keys on an action
          If the action has been wrapped already, annotations will be applied to both the wrapper and wrapped.
        """
        unwrapped = DecorationUtils.unwrap(fn)
        sig = inspect.signature(unwrapped)

        # prepend annotations, so written decorator order is the same as written arg order:
        # (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        new_annotations = keys + getattr(unwrapped, DecorationUtils._keys, [])
        setattr(unwrapped, DecorationUtils._keys, new_annotations)
        if unwrapped is not fn:
            setattr(fn, DecorationUtils._keys, new_annotations)

        if not DecorationUtils.verify_action_signature(sig, new_annotations):
            raise doot.errors.DootKeyError("Annotations do not match signature", sig)

        return True

    @staticmethod
    def add_method_expander(fn):

        @ftz.wraps(fn)
        def method_action_expansions(self, spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, DecorationUtils._keys)]
            except KeyError as err:
                printer.warning("Action State Expansion Failure: %s", err)
                return False
            all_args = (*call_args, *expansions)
            return fn(self, spec, state, *all_args, **kwargs)

        # -
        return method_action_expansions

    @staticmethod
    def add_fn_expander(fn):

        @ftz.wraps(fn)
        def fn_action_expansions(spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, DecorationUtils._keys)]
            except KeyError as err:
                printer.warning("Action State Expansion Failure: %s", err)
                return False
            all_args = (*call_args, *expansions)
            return fn(spec, state, *all_args, **kwargs)

        # -
        return fn_action_expansions

    @staticmethod
    def prepare_expansion(keys:list[Key_p], fn):
        """ used as a partial fn. adds declared keys to a function,
          and idempotently adds the expansion decorator
        """
        is_func = True
        DecorationUtils._update_key_annotations(fn, keys)

        if DecorationUtils.has_annotations(fn, DecorationUtils._wrapped_flag):
            # keys are handled, so the fn already has an expander, no need to add one
            return fn

        is_func = inspect.signature(fn).parameters.get("self", None) is None
        match is_func:
            case False:
                wrapper = DecorationUtils.add_method_expander(fn)
            case True:
                wrapper = DecorationUtils.add_fn_expander(fn)

        # mark the function as having a wrapper installed
        DecorationUtils.annotate(fn, {DecorationUtils._wrapped_flag})
        return wrapper
