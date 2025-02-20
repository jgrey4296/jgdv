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

from .core import MonotonicDec, IdempotentDec, Decorator

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, TypeAliasType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from types import resolve_bases, FunctionType, MethodType

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
##--| Funcs

##--| Body

class _CheckProtocol_m:
    """ A Class Decorator to ensure a class has no abc.abstractmethod's
    or unimplemented protocol members

    pass additional protocols when making the decorator,
    eg:

    @CheckProtocol(Proto1_p, Proto2_p, AbsClass...)
    class MyClass:
    pass
    """

    def _get_protos(self, target:type) -> set[Protocol]:
        # From MRO
        protos = [x for x in target.__mro__
                  if issubclass(x, Protocol|abc.ABC)
                  and x is not target
                  and x is not Protocol]

        # from JGDV Annotations
        protos += self.get_annotations(target)
        return set(protos)

    def _test_method(self, cls:type, name:str) -> bool:
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

    def _test_protocol(self, proto:Protocol, cls) -> list[str]:
        """ Returns a list of methods which are defined in the protocol,
        no where else in the mro.
        ie: they are unimplemented protocol requirements

        Can handle type aliases, so long as they actually point to a protocol.
        eg: type proto_alias = MyProtocol_p
        where issubclass(MyProtocol_p, Protocol)
        """
        result = []
        # Get the members of the protocol/abc
        match proto:
            case type() if issubclass(proto, Protocol):
                members  = proto.__protocol_attrs__
                qualname = proto.__qualname__
            case type() if issubclass(proto, abc.ABC):
                return []
            case TypeAliasType() if (origin:=getattr(proto.__value__, "__origin__", None)) and issubclass(origin, Protocol):
                members = origin.__protocol_attrs__
                qualname = origin.__qualname__
            case TypeAliasType() if issubclass(proto.__value__, Protocol):
                members = proto.__value__.__protocol_attrs__
                qualname = proto.__value__.__qualname__
            case x if (origin:=getattr(proto, "__origin__", None)) and issubclass(origin, Protocol):
                members = origin.__protocol_attrs__
                qualname = origin.__qualname__
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
                case MethodType():
                    pass
                case x:
                    raise TypeError("Unexpected Type in protocol checking", member, type(x), x, cls)
        else:
            return result

    def validate_protocols(self, cls:type) -> type:
        still_abstract = set()
        for meth in getattr(cls, ABSMETHS, []):
            if self._test_method(cls, meth):
                still_abstract.add(meth)
        ##--|
        for proto in self._get_protos(cls):
            still_abstract.update(self._test_protocol(proto, cls))
        ##--|
        for proto in self._protos:
            still_abstract.update(self._test_protocol(proto, cls))
        ##--|
        if not bool(still_abstract):
            return cls

        raise NotImplementedError("Class has Abstract Methods",
                                  cls.__qualname__,
                                  f"module:{cls.__module__}",
                                  still_abstract)

class Proto(_CheckProtocol_m, MonotonicDec):
    """ Decorator to explicitly annotate a class as an implementer of a set of protocols
    Protocols are annotated into cls._jgdv_protos : set[Protocol]

    class ClsName(Supers*, P1, P1..., **kwargs):...

    becomes:

    @Protocols(P1, P2,...)
    class ClsName(Supers): ...

    Protocol *definition* remains the typical way:

    class Proto1(Protocol): ...

    class ExtProto(Proto1, Protocol): ...
    """

    def __init__(self, *protos:Protocol, check=True):
        super().__init__(data=PROTO_SUFFIX)
        self._protos = protos or []
        self._check = check

    def _validate_target_h(self, target:Decorable, form:DForm_e, args:Maybe[list]=None) -> None:
        match target:
            case type() if issubclass(target, Protocol):
                raise TypeError("Don't use @Proto to combine protocols, use normal inheritance", target)
            case type():
                pass
            case _:
                raise TypeError("Unexpected type passed for protocol annotation")

    def _wrap_class_h(self, cls:type) -> Maybe[type]:
        """ """
        new_name = f"{cls.__qualname__}<+Protocols>"
        namespace : dict = dict(cls.__dict__)

        self.annotate_decorable(cls)
        match namespace.get(PROTO_SUFFIX, None):
            case None:
                namespace[PROTO_SUFFIX] = set([*self._get_protos(cls), *self._protos])
            case [*xs]:
                namespace[PROTO_SUFFIX] = set([*xs, *self._protos])
        try:
            customized = self._new_class(new_name, cls, namespace=namespace)
        except TypeError as err:
            raise TypeError(*err.args, cls, self._protos) from None

        match self._check:
            case True:
                self.validate_protocols(customized)
            case _:
                pass
        ##--|
        return customized


    def _build_annotations_h(self, target:Decorable, current:list) -> Maybe[list]:
        updated = current[:]
        updated += [x for x in self._protos if x not in current]
        return updated

    @staticmethod
    def get(cls:type) -> list[Protocol]:
        """ Get a List of protocols the class is annotated with """
        return list(Proto()._get_protos(cls))
