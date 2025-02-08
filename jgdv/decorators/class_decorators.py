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

from .core import DecoratorBase
from .check_protocol import CheckProtocol
from types import resolve_bases

# ##-- types
# isort: off
if typing.TYPE_CHECKING:
   from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Global Vars:

# Body:

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

    def _mod_class(self, cls):

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



class WithProto(DecoratorBase):
    """ Mixin to change:

    class ClsName(mixins, Supers, Protocols, metaclass=MCls, **kwargs):...

    into:

    @Mixin(*ms)
    @Protocols(*ps)
    class ClsName(Supers): ...

"""
    def __init__(self, *protos:Protocol, check=True):
        super().__init__()
        self._protos = protos or []
        self._check = check

    def _mod_class(self, cls):
        bases = [*cls.mro()[:-1], *self._protos]
        new_mro = resolve_bases(bases)
        new_name = f"{cls.__qualname__}<WithProtocols>"
        try:
            custom = type(cls)(new_name, tuple(new_mro), dict(cls.__dict__))
            if not self._check:
                return custom

            checker = CheckProtocol()
            return checker(custom)
        except TypeError as err:
            raise TypeError(*err.args, new_mro) from None
