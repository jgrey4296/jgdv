#!/usr/bin/env python3
"""

"""
# mypy: disable-error-code="attr-defined"
# ruff: noqa: ANN002, ANN003
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
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
from .. import errors as dkey_errs
from ..dkey import DKey
from .._interface import ARGS_K, KWARGS_K, PARAM_IGNORES, Key_p

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
from collections.abc import Mapping
from typing import Any

if TYPE_CHECKING:
    from jgdv import Method
    import inspect
    from jgdv import Decorator, FmtStr, Func, Ident, Maybe, Rx
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, MutableMapping, Hashable

    from jgdv.decorators._interface import Decorated, Decorable
    type Signature = inspect.Signature
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class DKeyMetaDecorator(MetaDec):
    """ A Meta decorator that registers keys for input and output
    verification"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("mark", "_dkey_meta_marked")
        kwargs.setdefault("data", "_dkey_meta_vals")
        super().__init__(*args, **kwargs)

class DKeyExpansionDecorator(DataDec):
    """
    Utility class for idempotently decorating actions with auto-expanded keys

    """
    _param_ignores : tuple[str, ...]

    def __init__(self, keys:list[DKey], ignores:Maybe[list[str]]=None, **kwargs) -> None:
        kwargs.setdefault("mark", "_dkey_marked")
        kwargs.setdefault("data", "_dkey_vals")
        super().__init__(keys, **kwargs) # type: ignore[arg-type]
        match ignores:
            case None:
                self._param_ignores = PARAM_IGNORES
            case list():
                self._param_ignores = tuple(ignores)
            case x:
                raise TypeError(type(x))

    @override
    def _wrap_method_h[**In, Out](self, meth:Func[In,Out]) -> Decorated[In, Out]:
        data_key = self._data_key

        def _method_action_expansions(*call_args:In.args, **kwargs:In.kwargs) -> Out:
            _self, spec, state, *rest = call_args
            try:
                expansions = [x(spec, state) for x in meth.__annotations__[data_key]]
            except KeyError as err:
                logging.warning("Action State Expansion Failure: %s", err)
                return cast("Out", False)  # noqa: FBT003
            else:
                return meth(*call_args, *expansions, **kwargs)

        # -
        return cast("Decorated[In, Out]", _method_action_expansions)

    @override
    def _wrap_fn_h[**In, Out](self, fn:Func[In, Out]) -> Decorated[In, Out]:
        data_key = self._data_key

        def _fn_action_expansions(*args:In.args, **kwargs:In.kwargs) -> Out:
            spec, state, *rest = args
            try:
                expansions = [x(spec, state) for x in fn.__annotations__[data_key]]
            except KeyError as err:
                logging.warning("Action State Expansion Failure: %s", err)
                return cast("Out", False)  # noqa: FBT003
            else:
                return fn(*args, *expansions, **kwargs)

        # -
        return _fn_action_expansions

    @override
    def _validate_sig_h(self, sig:Signature, form:DForm_e, args:Maybe[list[DKey]]=None) -> None:
        x : Any
        y : Any
        ##--|
        # Get the head args
        match form:
            case DForm_e.FUNC:
                head = ["spec", "state"]
            case DForm_e.METHOD:
                head = ["self", "spec", "state"]
            case x:
                raise TypeError(type(x))

        params      = list(sig.parameters)
        tail        = args or []

        # Check the head
        for x,y in zip(params, head, strict=False):
            if x != y:
                msg = "Mismatch in signature head"
                raise dkey_errs.DecorationMismatch(msg, x, y, form)

        prefix_ig, suffix_ig = self._param_ignores
        # Then the tail, backwards, because the decorators are applied in reverse order
        for x,y in zip(params[::-1], tail[::-1], strict=False):
            assert(isinstance(y, Key_p))
            key_str = y.var_name()
            if x.startswith(prefix_ig) or x.endswith(suffix_ig):
                logging.debug("Skipping: %s", x)
                continue

            if keyword.iskeyword(key_str):
                msg = "Key is a keyword, use an alias like _{} or {}_ex, or use named={}"
                raise dkey_errs.DecorationMismatch(msg, x, key_str)

            if not key_str.isidentifier():
                msg = "Key is not an identifier, use an alias _{} or {}_ex or use named={}"
                raise dkey_errs.DecorationMismatch(msg, x, key_str)

            if x != y:
                msg = "Mismatch in signature tail"
                raise dkey_errs.DecorationMismatch(msg, str(x), key_str)

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

    @override
    def __init_subclass__(cls) -> None:
        """
        Subclasses of DKeyed are stored, and used to extend DKeyed
        """
        super().__init_subclass__()
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
    """ Subclass extension for decorators that declare meta information,
    but doesnt modify the behaviour
    """

    @classmethod
    def requires(cls, *args, **kwargs) -> DKeyMetaDecorator:
        """ mark an action as requiring certain keys to in the state, but aren't expanded """
        keys = [DKey[Any](x, implicit=True, **kwargs) for x in args]
        return DKeyMetaDecorator(keys)

    @classmethod
    def returns(cls, *args, **kwargs) -> DKeyMetaDecorator:
        """ mark an action as needing to return certain keys """
        keys = [DKey[Any](x, implicit=True, **kwargs) for x in args]
        return DKeyMetaDecorator(keys)

class DKeyedRetrieval(DecoratorAccessor_m, DKeyed):
    """ Subclass extension for DKeyed decorators,
    which modify the calling behaviour of the decoration target

    """

    _decoration_builder : ClassVar[type] = DKeyExpansionDecorator

    @classmethod
    def formats(cls, *args, **kwargs) -> Decorator:
        keys     = [DKey[str](x, implicit=True, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def expands(cls, *args, **kwargs) -> Decorator:
        """ mark an action as using expanded string keys """
        return cls.formats(*args, **kwargs)

    @classmethod
    def paths(cls, *args, **kwargs) -> Decorator:
        """ mark an action as using expanded path keys """
        kwargs.setdefault("implicit", True)
        keys = [DKey[pl.Path](x, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def types(cls, *args, **kwargs) -> Decorator:
        """ mark an action as using raw type keys """
        keys : list = [DKey[Any](x, implicit=True, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def toggles(cls, *args, **kwargs) -> Decorator:
        keys : list = [DKey(x, implicit=True, ctor=bool, check=bool, **kwargs) for x in args]
        return cls._build_decorator(keys)

    @classmethod
    def args(cls, fn:Callable) -> Decorator:
        """ mark an action as using spec.args """
        keys = [DKey[DKey.Marks.ARGS](ARGS_K, implicit=True)] # type: ignore[name-defined]
        match cls._build_decorator(keys)(fn):
            case None:
                raise dkey_errs.DecorationMismatch()
            case x:
                return x

    @classmethod
    def kwargs(cls, fn:Callable) -> Decorator:
        """ mark an action as using all kwargs"""
        keys = [DKey[DKey.Marks.KWARGS](KWARGS_K, implicit=True)] # type: ignore[name-defined]
        match cls._build_decorator(keys)(fn):
            case None:
                raise dkey_errs.DecorationMismatch()
            case x:
                return x

    @classmethod
    def redirects(cls, *args, **kwargs) -> Decorator:
        """ mark an action as using redirection keys """
        kwargs.setdefault("max_exp", 1)
        keys = [DKey[Mapping](x, implicit=True, **kwargs) for x in args] # type: ignore[name-defined]
        return cls._build_decorator(keys)

    @classmethod
    def references(cls, *args, **kwargs) -> Decorator:
        """ mark keys to use as to_coderef imports """
        keys = [DKey[CodeReference](x, implicit=True, **kwargs) for x in args] # type: ignore[name-defined]
        return cls._build_decorator(keys)

    @classmethod
    def postbox(cls, *args, **kwargs) -> Decorator:
        keys = [DKey[DKey.Marks.POSTBOX](x, implicit=True, **kwargs) for x in args] # type: ignore[name-defined]
        return cls._build_decorator(keys)
