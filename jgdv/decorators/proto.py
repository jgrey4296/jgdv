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
import typing
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv.mixins.annotate import Subclasser

# ##-- end 1st party imports

from . import _interface as API # noqa: N812
from ._core import Decorator, IdempotentDec, MonotonicDec, _DecAnnotate_m

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, TypeAliasType, _GenericAlias # type: ignore[attr-defined]
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from types import resolve_bases, FunctionType, MethodType, MethodDescriptorType, WrapperDescriptorType, ClassMethodDescriptorType, BuiltinFunctionType, BuiltinMethodType

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    from ._interface import Decorable, Decorated, DForm_e

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Global Vars:
PROTO_SUFFIX : Final[str] = "protocols"
ABSMETHS     : Final[str] = "__abstractmethods__"
IS_ABS       : Final[str] = "__isabstractmethod__"
NAME_MOD     : Final[str] = "P"
##--| Funcs

##--| Body

class CheckProtocols(_DecAnnotate_m):
    """ A Class Decorator to ensure a class has no abc.abstractmethod's
    or unimplemented protocol members

    pass additional protocols when making the decorator, eg::

        @CheckProtocol(Proto1_p, Proto2_p, AbsClass...)
        class MyClass:
        pass

    """
    _annotation_prefix  : ClassVar[str]  = API.ANNOTATIONS_PREFIX
    _data_suffix        : ClassVar[str]   = PROTO_SUFFIX
    _data_key = None

    def get_protos(self, target:type) -> set[Protocol]:
        """ Get the protocols of a type from its mro and annotations """
        # From MRO
        protos = []
        for x in target.mro():
            match x:
                case _ if x in [Protocol,Generic, target, object]:
                    pass
                case TypeAliasType() if issubclass(x.__value__, Protocol):
                    protos.append(x)
                case x if issubclass(x, Protocol):
                    protos.append(x)
                case x if issubclass(x, abc.ABC):
                    protos.append(x)
                case _:
                    pass
        else:
            protos += target.__annotations__.get(self.data_key(), [])
            return set(protos)

    def test_method(self, cls:type, name:str) -> bool:
        """ return True if the named method is abstract still """
        if name == ABSMETHS:
            return False
        match getattr(cls, name, None):
            case None:
                return True
            case FunctionType() as x if hasattr(x, IS_ABS):
                return x.__isabstractmethod__
            case FunctionType() | property():
                return False

    def test_protocol(self, proto:Protocol, cls) -> list[str]:
        """ Returns a list of methods which are defined in the protocol,
        and nowhere else in the mro.

        ie: they are unimplemented protocol requirements

        Can handle type aliases, so long as they actually point to a protocol.
        | eg: type proto_alias = MyProtocol_p
        | where issubclass(MyProtocol_p, Protocol)
        """
        members : set
        result  : list = []
        # Get the members of the protocol/abc
        match proto:
            case type() if issubclass(proto, Protocol):
                non_callable = getattr(proto, "__non_callable_proto_members__", set())
                fields       = getattr(proto, "__annotations__", {})
                non_attrs    = {x for x in proto.__protocol_attrs__ if getattr(proto, x, None) is None}
                members      = set(proto.__protocol_attrs__) - non_callable - fields.keys() - non_attrs
                qualname     = proto.__qualname__
            case type() if issubclass(proto, abc.ABC):
                return []
            case _:
                raise TypeError("Checking a protocol... but it isnt' a protocol", proto)

        # then filter out the implemented ones
        for member in members:
            match getattr(cls, member, None):
                case property():
                    pass
                case None:
                    result.append(member)
                case FunctionType() as meth if qualname in meth.__qualname__:
                    # (as a class, the method isn't actually bound as a method yet, its still a function)
                    result.append(member)
                case FunctionType():
                    pass
                case MethodType() as meth  if qualname in meth.__func__.__qualname__:
                    result.append(member)
                case MethodType() | ftz.cached_property():
                    pass
                case BuiltinFunctionType() | BuiltinMethodType():
                    pass
                case MethodDescriptorType() | WrapperDescriptorType() | ClassMethodDescriptorType():
                    pass
                case _:
                    pass
        else:
            return result

    def validate_protocols(self, cls:type, *, protos:Maybe[list[Protocol]]) -> type:
        still_abstract = set()
        for meth in getattr(cls, ABSMETHS, []):
            if self.test_method(cls, meth):
                still_abstract.add(meth)
        ##--|
        for proto in self.get_protos(cls):
            still_abstract.update(self.test_protocol(proto, cls))
            ##--|
        for proto in protos or []:
            still_abstract.update(self.test_protocol(proto, cls))
            ##--|
        if not bool(still_abstract):
            return cls

        raise NotImplementedError("Class has Abstract Methods",
                                  cls.__qualname__,
                                  f"module:{cls.__module__}",
                                  still_abstract)

class Proto(MonotonicDec):
    """ Decorator to explicitly annotate a class as an implementer of a set of protocols.

    Protocols are annotated into cls._jgdv_protos : set[Protocol]::

        class ClsName(Supers*, P1, P1..., **kwargs):...

    becomes::

        @Protocols(P1, P2,...)
        class ClsName(Supers): ...

    Protocol *definition* remains the usual way::

        class Proto1(Protocol): ...

        class ExtProto(Proto1, Protocol): ...

    """
    needs_args = True
    _checker   : ClassVar[CheckProtocols] = CheckProtocols()
    _protos    : list
    _name_mod  : str
    _mod_mro   : bool
    _check     : bool

    def __init__(self, *protos:Protocol, check:bool=True, mod_mro:bool=False):
        super().__init__(data=PROTO_SUFFIX)
        self._protos    = []
        self._name_mod  = NAME_MOD
        self._mod_mro   = mod_mro
        self._check     = check

        for x in protos:
            match x:
                case TypeAliasType() if isinstance(x.__value__, _GenericAlias):
                    x = x.__value__.__origin__
                case TypeAliasType():
                    x = x.__value__
                case _GenericAlias():
                    x = x.__origin__
                case _:
                    pass

            match x:
                case _ if issubclass(x, Protocol):
                    self._protos.append(x)
                case x:
                     raise TypeError("Tried to attach a non-protocol to a class", x)
        else:
            pass

    def _validate_target_h(self, target:Decorable, form:DForm_e, args:Maybe[list]=None) -> None:
        match target:
            case type() if issubclass(target, Protocol):
                raise TypeError("Don't use @Proto to combine protocols, use normal inheritance", target)
            case type():
                pass
            case _:
                raise TypeError("Unexpected type passed for protocol annotation")

    def _wrap_class_h(self, cls:type) -> Maybe[type]:
        """ Logic for inserting the protocol into the given cls. """
        new_name = Subclasser.decorate_name(cls, self._name_mod)
        protos = self._checker.get_protos(cls)
        protos.update(self._protos)

        try:
            if self._mod_mro:
                modified = self._build_mro(cls)
                customized = self._builder.make_subclass(new_name, cls, mro=modified)
            else:
                customized = cls
        except TypeError as err:
            raise TypeError(*err.args, cls, self._protos, protos) from None

        self.annotate_decorable(customized)
        match self._check:
            case True:
                self._checker.validate_protocols(customized, protos=self._protos)
            case _:
                pass
        ##--|
        return customized

    def _build_mro(self, cls) -> list:
        match cls.mro():
            case [*xs, typing.Protocol, x] if x is object:
                base = [*xs, *self._protos, object]
            case [*xs, x] if x is object:
                base = [*xs, *self._protos, object]
            case x:
                raise TypeError(type(x))

        return base

    def _build_annotations_h(self, target:Decorable, current:list) -> Maybe[list]:
        updated = current[:]
        updated += [x for x in self._protos if x not in current]
        updated += self._checker.get_protos(target)
        return updated

    @staticmethod
    def get(cls:type) -> list[Protocol]:
        """ Get a List of protocols the class is annotated with """
        return list(Proto._checker.get_protos(cls))

    @staticmethod
    def validate_protocols(cls:type, *protos:Protocol):
        return Proto._checker.validate_protocols(cls, protos=protos)
