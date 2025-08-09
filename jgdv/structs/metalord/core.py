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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

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

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
logging.disabled = True
##-- end logging

# Vars:

# Body:

class MetalordCore(type):
    """
    The Core of Metalord.

    By default classes are constructed using type().
    https://docs.python.org/3/reference/datamodel.html#metaclasses

    Execution order::

        - Metaclass Definition
        - Metaclass Creation

        - Class Definition:
            1) MRO resolution           : __mro_entries__(self, bases)
            2) metaclass selection      : (most dervied of (type | metaclasses))
            3) namespace preparation    : metacls.__prepare__(metacls, name, bases, **kwargs) -> dict
            4) class body execution     : exec(body, globals, namespace)
            5) class object creation    : metaclass.__new__(name, bases, namespace, **kwargs) -> classobj
            6) subclass init            : parent.__init_subclass__(cls, **kwargs)
            7) class object init        : metaclass.__init__(cls, na,e, bases, namespace, **kwargs)

        - Instance Creation::
            1) metaclass.__call__(cls, ...) -> instance
            1.b) cls.__new__(cls, ...) -> instance
            1.c) cls.__init__(instance, ...)

    """

    @classmethod
    def __prepare__(mcls:type, name:str, bases:tuple, **kwargs) -> dict:
        """ Class Definition preparation of namespace """
        logging.debug("Metalord Prepare: %s %s %s", name, bases, kwargs)
        return super().__prepare__(name, bases, **kwargs)

    def __new__(mcls:type, name:str, bases:tuple, namespace:dict, **kwargs) -> type:
        """ Class Definition Object creation
        Equivalent to type(name, bases, namespace)
        """
        logging.debug("Metalord new: %s %s %s %s %s", mcls, name, bases, namespace, kwargs)
        return super().__new__(mcls, name, bases, dict(namespace), **kwargs)

    def __init__(cls, name, bases:tuple, namespace:dict, **kwargs):
        """ Class Definition initialisation """
        logging.debug("Metalord init: %s %s %s %s %s", cls, name, bases, namespace, kwargs)
        super().__init__(name, bases, namespace, **kwargs)

    def __call__(cls, *args, **kwargs):
        """ Class Instance creation
        """
        logging.debug("Metalord Call: %s %s %s", cls, args, kwargs)
        obj = cls.__new__(cls, *args, **kwargs)
        obj.__init__(*args, **kwargs)
        return obj

    def __instancecheck__(self, instance) -> bool:
        logging.debug("Metalord instance check: %s %s", self, instance)
        return super().__instancecheck__(instance)

    def __subclasscheck__(self, subclass) -> bool:
        logging.debug("Metalord subclass check: %s %s", self, subclass)
        return super().__subclasscheck__(subclass)
