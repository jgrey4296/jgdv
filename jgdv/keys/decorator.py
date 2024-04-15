#!/usr/bin/env python3
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
# import more_itertools as mitz
# from boltons import
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv.decorators.base import JGDVBaseDecorator

class KWrapper(JGDVBaseDecorator):
    """ Decorators for actions
    Kwrapper is accessible as DootKey.kwrap

    It registers arguments on an action and extracts them from the spec and state automatically.

    provides: expands/paths/types/requires/returns/args/kwargs/redirects/redirects_many

    The kwarg 'hint' takes a dict and passes the contents to the relevant expansion method as kwargs

    arguments are added to the tail of the action args, in order of the decorators.
    the name of the expansion is expected to be the name of the action parameter,
    with a "_" prepended if the name would conflict with a keyword., or with "_ex" as a suffix
    eg: @DootKey.kwrap.paths("from") -> def __call__(self, spec, state, _from):...
    or: @DootKey.kwrap.paths("from") -> def __call__(self, spec, state, from_ex):...
    """

    @staticmethod
    def _annotate_keys(f, keys:list) -> bool:
        """ cache original args, and cache declared keys """
        if hasattr(f, FUNC_WRAPPED): # Deal with the actual function, not any decorators
            return KWrapper._annotate_keys(f.__wrapped__, keys)

        if not hasattr(f, ORIG_ARGS): # store the original arguments for easy access
            setattr(f, ORIG_ARGS, f.__code__.co_varnames[:f.__code__.co_argcount])

        if not hasattr(f, KEY_ANNOTS): # ensure theres a place for annotations
            setattr(f, KEY_ANNOTS, [])

        # prepend annotations, so written decorator order is the same as written arg order:
        # (ie: @wrap(x) @wrap(y) @wrap(z) def f (x, y, z), even though z's decorator is applied first
        new_annotations = keys + getattr(f, KEY_ANNOTS)
        setattr(f, KEY_ANNOTS, new_annotations)

        # run the key check
        if not KWrapper._check_keys(f, getattr(f, KEY_ANNOTS)):
            raise doot.errors.DootKeyError("Annotations do not match signature", getattr(f, ORIG_ARGS, []), getattr(f, KEY_ANNOTS), f.__qualname__)

        return True

    @staticmethod
    def _annotate_non_expansions(f, keys:list, type_="in") -> bool:
        """
        Annotate required inputs and output
        """
        if hasattr(f, FUNC_WRAPPED):
            return KWrapper._annotate_non_expansions(f.__wrapped__, keys)

    @staticmethod
    def _check_keys(f, keys, offset=0) -> bool:
        """ test declared args to a list of keys """
        if hasattr(f, ORIG_ARGS):
            code_args           = getattr(f, ORIG_ARGS)
            code_argcount       = len(code_args)
        else:
            code_argcount           = f.__code__.co_argcount
            code_args               = f.__code__.co_varnames[:code_argcount]

        result                  = True
        if code_args[0]         == "self":
            code_args           = code_args[1:]

        # First two params should always be spec and state
        result &= code_args[:2] == ("spec", "state")

        # The rest should match keys
        for actual, expected in zip(code_args[:1+offset:-1], keys[::-1]):
            match expected:
                case DootMultiKey():
                    pass
                case DootSimpleKey() | str() if actual.startswith("_"):
                    pass
                case DootSimpleKey() | str():
                    result &= ((actual == expected) or (actual == f"{expected}_ex"))

        return result

    @staticmethod
    def _add_key_handler(f):
        """ idempotent key handler so decorated functions dont add unnecessary stack frames """
        if DootDecorator.has_annotations(f):
            return f

        DootDecorator.truncate_signature(f)

        match getattr(f, ORIG_ARGS)[0]:
            case "self": # The method form handler

                @ftz.wraps(f)
                def action_expands(self, spec, state, *call_args, **kwargs):
                    try:
                        expansions = [x(spec, state) for x in getattr(f, KEY_ANNOTS)]
                    except KeyError as err:
                        printer.warning("Action State Expansion Failure: %s", err)
                        return False
                    all_args = (*call_args, *expansions)
                    return f(self, spec, state, *all_args, **kwargs)
            case _: # The function form handler

                @ftz.wraps(f)
                def action_expands(spec, state, *call_args, **kwargs):
                    try:
                        expansions = [x(spec, state) for x in getattr(f, KEY_ANNOTS)]
                    except KeyError as err:
                        printer.warning("Action State Expansion Failure: %s", err)
                        return False
                    all_args = (*call_args, *expansions)
                    return f(spec, state, *all_args, **kwargs)

        DootDecorator.annotate(action_expands, {KEYS_HANDLED})
        return action_expands

    @staticmethod
    def taskname(f):
        KWrapper._annotate_keys(f, [DootKey.build(STATE_TASK_NAME_K, exp_hint="type")])
        return KWrapper._add_key_handler(f)

    @staticmethod
    def expands(*args, hint:dict|None=None, **kwargs):
        """ mark an action as using expanded string keys """
        exp_hint = {"expansion": "str", "kwargs" : hint or {} }
        keys = [DootKey.build(x, exp_hint=exp_hint, **kwargs) for x in args]

        def expand_wrapper(f):
            KWrapper._annotate_keys(f, keys)
            return KWrapper._add_key_handler(f)

        return expand_wrapper

    @staticmethod
    def paths(*args, hint:dict|None=None, **kwargs):
        """ mark an action as using expanded path keys """
        exp_hint = {"expansion": "path", "kwargs" : hint or {} }
        keys = [DootKey.build(x, exp_hint=exp_hint, **kwargs) for x in args]

        def expand_wrapper(f):
            KWrapper._annotate_keys(f, keys)
            return KWrapper._add_key_handler(f)

        return expand_wrapper

    @staticmethod
    def types(*args, hint:dict|None=None, **kwargs):
        """ mark an action as using raw type keys """
        exp_hint = {"expansion": "type", "kwargs" : hint or {} }
        keys = [DootKey.build(x, exp_hint=exp_hint, **kwargs) for x in args]

        def expand_wrapper(f):
            KWrapper._annotate_keys(f, keys)
            return KWrapper._add_key_handler(f)

        return expand_wrapper

    @staticmethod
    def args(f):
        """ mark an action as using spec.args """
        # TODO handle expansion hint for the args
        KWrapper._annotate_keys(f, [DootArgsKey("args")])
        return KWrapper._add_key_handler(f)

    @staticmethod
    def kwargs(f):
        """ mark an action as using spec.args """
        KWrapper._annotate_keys(f, [DootKwargsKey("kwargs")])
        return KWrapper._add_key_handler(f)

    @staticmethod
    def redirects(*args):
        """ mark an action as using redirection keys """
        keys = [DootKey.build(x, exp_hint="redirect") for x in args]

        def expand_wrapper(f):
            KWrapper._annotate_keys(f, keys)
            return KWrapper._add_key_handler(f)

        return expand_wrapper

    @staticmethod
    def redirects_many(*args, **kwargs):
        """ mark an action as using redirection key lists """
        keys = [DootKey.build(x, exp_hint="redirect_multi") for x in args]

        def expand_wrapper(f):
            KWrapper._annotate_keys(f, keys)
            return KWrapper._add_key_handler(f)

        return expand_wrapper

    @staticmethod
    def requires(*args, **kwargs):
        """ mark an action as requiring certain keys to be passed in """
        keys = [DootKey.build(x, **kwargs) for x in args]

        def expand_wrapper(f):
            KWrapper._annotate_non_expansions(f, keys)
            return f

        return expand_wrapper

    @staticmethod
    def returns(*args, **kwargs):
        """ mark an action as needing to return certain keys """
        keys = [DootKey.build(x, **kwargs) for x in args]

        def expand_wrapper(f):
            KWrapper._annotate_non_expansions(f, keys)
            return f

        return expand_wrapper

    @staticmethod
    def references(*args, **kwargs):
        """ mark keys to use as to_coderef imports """
        exp_hint = {"expansion": "coderef", "kwargs" : {} }
        keys = [DootKey.build(x, exp_hint=exp_hint, **kwargs) for x in args]

        def expand_wrapper(f):
            KWrapper._annotate_keys(f, keys)
            return KWrapper._add_key_handler(f)

        return expand_wrapper
