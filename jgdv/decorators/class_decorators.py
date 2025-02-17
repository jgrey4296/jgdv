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

from .core import DecoratorBase

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
from types import resolve_bases, FunctionType
if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Global Vars:
MIXIN_KWD : Final[str] = "_jgdv_mixins"
PROTO_KWD : Final[str] = "_jgdv_protos"
ABSMETHS  : Final[str] = "__abstractmethods__"
IS_ABS    : Final[str] = "__isabstractmethod__"
##--| Funcs

def check_protocol(cls):
    """ Decorator. Check the class implements all its methods / has no abstractmethods """
    checker = CheckProtocol()
    return checker(cls)

##--| Body

class CheckProtocol(DecoratorBase):
    """ A Class Decorator to ensure a class has no abc.abstractmethod's
    or unimplemented protocol members

    pass additional protocols when making the decorator,
    eg:

    @CheckProtocol(Proto1_p, Proto2_p, AbsClass...)
    class MyClass:
    pass
    """

    @staticmethod
    def _get_protos(cls) -> set[Protocol]:
        # From MRO
        protos = [x for x in cls.__mro__
                  if issubclass(x, Protocol)
                  and x is not cls
                  and x is not Protocol]
        # from JGDV Annotations
        protos += getattr(cls, PROTO_KWD, [])
        return set(protos)

    def __init__(self, *protos):
        super().__init__()
        self._protos = protos

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
        """ Returns a list of methods which are defined in the protocol, no where else in the mro """
        result = []
        for member in proto.__protocol_attrs__:
            match getattr(cls, member, None):
                case property():
                    pass
                case None:
                    result.append(member)
                case FunctionType() as meth if proto.__qualname__ in meth.__qualname__:
                    # (as a class, the method isn't actually bound as a method yet, its still a function)
                    result.append(member)
                case FunctionType():
                    pass
                case x:
                    raise TypeError("Unexpected Type in protocol checking", member, x, cls)
        else:
            return result

    def _wrap_class(self, cls:type) -> type:
        still_abstract = set()
        for meth in getattr(cls, ABSMETHS, []):
            if self._test_method(cls, meth):
                still_abstract.add(meth)
        for proto in self._get_protos(cls):
            still_abstract.update(self._test_protocol(proto, cls))

        for proto in self._protos:
            still_abstract.update(self._test_protocol(proto, cls))

        if not bool(still_abstract):
            return cls

        raise NotImplementedError("Class has Abstract Methods", cls.__module__, cls.__name__, still_abstract)

class Mixin(DecoratorBase):
    """ Decorator to Prepend Mixins into the decorated class.
    kwarg 'append'

    class ClsName(mixins, Supers, Protocols, metaclass=MCls, **kwargs):...

    into:

    @Mixin(*ms)
    @Protocols(*ps)
    class ClsName(Supers): ...

"""

    def __init__(self, *mixins:type, append:tuple[type]=None):
        super().__init__()
        self._prepend_mixins = mixins or []
        self._append_mixins = append or []

    def _wrap_class(self, cls):

        match self._append_mixins:
            case []:
                ready_to_prepend = cls
            case [*xs]:
                append_mro = [*xs, *cls.mro()[1:]]
                new_name = f"{cls.__qualname__}<AppendedMixins>"
                ready_to_prepend = type(cls)(new_name, tuple(append_mro), dict(cls.__dict__))
        bases = [*self._prepend_mixins, *ready_to_prepend.__mro__]
        new_mro = resolve_bases(bases)
        new_name = f"{cls.__qualname__}<WithMixins>"
        try:
            custom = type(ready_to_prepend)(new_name, tuple(new_mro), dict(ready_to_prepend.__dict__))
            return custom
        except TypeError as err:
            raise TypeError(*err.args, new_mro) from None

class Proto(CheckProtocol):
    """ Mixin to explicitly annotate a class with a set of protocols
    Protocols are annotated into cls._jgdv_protos : set[Protocol]

    class ClsName(Supers*, P1, P1..., **kwargs):...

    into:

    @Protocols(P1, P2,...)
    class ClsName(Supers): ...

"""

    def __init__(self, *protos:Protocol, check=True):
        super().__init__()
        self._protos = protos or []
        self._check = check

    def _wrap_class(self, cls:type):
        new_name = f"{cls.__qualname__}<WithProtocols>"
        with_protos : dict = dict(cls.__dict__)

        match with_protos.get(PROTO_KWD, None):
            case None:
                with_protos[PROTO_KWD] = set([*self._get_protos(cls), *self._protos])
            case [*xs]:
                with_protos[PROTO_KWD] = set([*xs, *self._protos])
        try:
            custom = type(cls)(new_name, tuple(cls.mro()), with_protos)
            if not self._check:
                return custom

            checker = CheckProtocol()
            return checker(custom)
        except TypeError as err:
            raise TypeError(*err.args, cls, self._protos) from None

    @staticmethod
    def get(cls:type) -> list[Protocol]:
        """ Get a List of protocols the class is annotated with """
        return list(Proto._get_protos(cls))
