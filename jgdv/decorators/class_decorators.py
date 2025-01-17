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

class MixinDecorator(DecoratorBase):
    """ Mixin to change:

    class ClsName(mixins, Supers, Protocols, metaclass=MCls, **kwargs):...

    into:

    @Mixin(*ms)
    @Protocols(*ps)
    class ClsName(Supers): ...

"""
    pass

class ProtocolDecorator(DecoratorBase):
    """ Mixin to change:

    class ClsName(mixins, Supers, Protocols, metaclass=MCls, **kwargs):...

    into:

    @Mixin(*ms)
    @Protocols(*ps)
    class ClsName(Supers): ...

"""
    pass
