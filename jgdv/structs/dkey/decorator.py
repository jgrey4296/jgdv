#!/usr/bin/env python3
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
import keyword
import logging as logmod
import pathlib as pl
import re
import time
import types as types_
import typing
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Mixin
from jgdv.decorators import (
    DataDec,
    MetaDec,
    DecoratorAccessor_m,
    DForm_e,
)
from jgdv.structs.strang import CodeReference
from .core import errors as dkey_errs
from .core.meta import DKey
from ._interface import ARGS_K, KWARGS_K, PARAM_IGNORES

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from types import MethodType

if TYPE_CHECKING:
    from jgdv import Decorator, FmtStr, Func, Ident, Maybe, Method, Rx
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

class DKeyMetaDecorator(MetaDec):
    """ A Meta decorator that registers keys for input and output
    verification"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("mark", "_dkey_meta_marked")
        kwargs.setdefault("data", "_dkey_meta_vals")
        super().__init__(*args, **kwargs)

class DKeyExpansionDecorator(DataDec):
    """
    Utility class for idempotently decorating actions with auto-expanded keys

    """

    def __init__(self, keys:list[DKey], ignores:Maybe[list[str]]=None, **kwargs):
        kwargs.setdefault("mark", "_dkey_marked")
        kwargs.setdefault("data", "_dkey_vals")
        super().__init__(keys, **kwargs)
        self._param_ignores     : tuple[str, str] = ignores or PARAM_IGNORES

    def _wrap_method_h(self, meth:Method) -> Method:
        data_key = self._data_key

        def _method_action_expansions(_self, spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(meth, data_key)]
            except KeyError as err:
                logging.warning("Action State Expansion Failure: %s", err)
                return False
            else:
                all_args = (*call_args, *expansions)
                return meth(_self, spec, state, *all_args, **kwargs)

        # -
        return _method_action_expansions

    def _wrap_fn_h(self, fn:Func) -> Func:
        data_key = self._data_key

        def _fn_action_expansions(spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, data_key)]
            except KeyError as err:
                logging.warning("Action State Expansion Failure: %s", err)
                return False
            else:
                all_args = (*call_args, *expansions)
                return fn(spec, state, *all_args, **kwargs)

        # -
        return _fn_action_expansions

    def _validate_sig_h(self, sig:Signature, form:DForm_e, args:Maybe[list[DKey]]=None) -> None:
        # Get the head args
        match form:
            case DForm_e.FUNC:
                head = ["spec", "state"]
            case DForm_e.METHOD:
                head = ["self", "spec", "state"]

        params      = list(sig.parameters)
        tail        = args or []

        # Check the head
        for x,y in zip(params, head, strict=False):
            if x != y:
                raise dkey_errs.DecorationMismatch("Mismatch in signature head", x, y, form)

        prefix_ig, suffix_ig = self._param_ignores
        # Then the tail, backwards, because the decorators are applied in reverse order
        for x,y in zip(params[::-1], tail[::-1], strict=False):
            key_str = str(y)
            if x.startswith(prefix_ig) or x.endswith(suffix_ig):
                logging.debug("Skipping: %s", x)
                continue

            if keyword.iskeyword(key_str):
                raise dkey_errs.DecorationMismatch("Key is a keyword, use an alias like _{} or {}_ex", x, y)

            if not key_str.isidentifier():
                raise dkey_errs.DecorationMismatch("Key is not an identifier, use an alias _{} or {}_ex", x,y)

            if x != y:
                raise dkey_errs.DecorationMismatch("Mismatch in signature tail", str(x), str(y))

class DKeyed:
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

    _extensions         : ClassVar[set[type]] = set()
    _decoration_builder : ClassVar[type]      = DKeyExpansionDecorator

    def __init_subclass__(cls):
        """
        Subclasses of DKeyed are stored, and used to extend DKeyed
        """
        if cls in DKeyed._extensions:
            return
        DKeyed._extensions.add(cls)
        for x in dir(cls):
            match getattr(cls, x):
                case MethodType() as y if not hasattr(DKeyed, x):
                    setattr(DKeyed, x, y)
                case _:
                    pass

class DKeyedMeta(DKeyed):
    """ Mixin for decorators that declare meta information,
    but doesnt modify the behaviour
    """

    @classmethod
    def requires(cls, *args, **kwargs) -> DKeyMetaDecorator:
        """ mark an action as requiring certain keys to in the state, but aren't expanded """
        keys = [DKey(x, implicit=True, mark=DKey.Mark.NULL, **kwargs) for x in args]
        return DKeyMetaDecorator(keys)

    @classmethod
    def returns(cls, *args, **kwargs) -> DKeyMetaDecorator:
        """ mark an action as needing to return certain keys """
        keys = [DKey(x, implicit=True, mark=DKey.Mark.NULL, **kwargs) for x in args]
        return DKeyMetaDecorator(keys)

class DKeyedRetrieval(DecoratorAccessor_m, DKeyed):
    """ Mixin for decorators which modify the calling behaviour of the decoration target

    """

    _decoration_builder : ClassVar[type] = DKeyExpansionDecorator

    @classmethod
    def formats(cls, *args, **kwargs) -> Decorator:
        keys     = [DKey(x, implicit=True, mark=DKey.Mark.STR, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def expands(cls, *args, **kwargs) -> Decorator:
        """ mark an action as using expanded string keys """
        return cls.formats(*args, **kwargs)

    @classmethod
    def paths(cls, *args, **kwargs) -> Decorator:
        """ mark an action as using expanded path keys """
        kwargs.setdefault("implicit", True)
        keys = [DKey(x, mark=DKey.Mark.PATH, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def types(cls, *args, **kwargs) -> Decorator:
        """ mark an action as using raw type keys """
        keys = [DKey(x, implicit=True, mark=DKey.Mark.FREE, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def toggles(cls, *args, **kwargs) -> Decorator:
        keys = [DKey(x, implicit=True, mark=DKey.Mark.FREE, ctor=bool, check=bool, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def args(cls, fn) -> Decorator:
        """ mark an action as using spec.args """
        keys = [DKey(ARGS_K, implicit=True, mark=DKey.Mark.ARGS)]
        return cls._build_decorator(keys)(fn)

    @classmethod
    def kwargs(cls, fn) -> Decorator:
        """ mark an action as using all kwargs"""
        keys = [DKey(KWARGS_K, implicit=True, mark=DKey.Mark.KWARGS)]
        return cls._build_decorator(keys)(fn)

    @classmethod
    def redirects(cls, *args, **kwargs) -> Decorator:
        """ mark an action as using redirection keys """
        kwargs.setdefault("max_exp", 1)
        keys = [DKey(x, implicit=True, mark=DKey.Mark.INDIRECT, ctor=DKey, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def references(cls, *args, **kwargs) -> Decorator:
        """ mark keys to use as to_coderef imports """
        keys = [DKey(x, implicit=True, mark=DKey.Mark.CODE, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def postbox(cls, *args, **kwargs) -> Decorator:
        keys = [DKey(x, implicit=True, mark=DKey.Mark.POSTBOX, **kwargs) for x in args]
        return cls._build_decorator(keys)
