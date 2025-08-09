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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from . import _interface as API # noqa: N812
from .annotate import SubAnnotate_m

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class SubRegistry_m(SubAnnotate_m):
    """ Create Subclasses in a registry

    By doing:

    class MyReg(SubRegistry_m):
        _registry : dict[str, type] = {}

    class MyClass(MyReg['blah']: ...

    MyClass is created as a subclass of MyReg, with a parameter set to 'blah'.
    This is added into MyReg._registry
    """
    _registry : ClassVar[dict] = {}

    @classmethod
    def __init_subclass__(cls, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        logging.debug("Registry Subclass: %s : %s : %s", cls, args, kwargs)
        super().__init_subclass__(*args, **kwargs)
        match getattr(cls, "_registry", None):
            case None:
                logging.debug("Creating Registry: %s : %s : %s", cls.__name__, args, kwargs)
                cls._registry = {}
            case _:
                pass
        match cls.cls_annotation():
            case None:
                logging.debug("No Annotation")
                pass
            case x if x in cls._registry and issubclass(cls, (current:=cls._registry[x])):
                logging.debug("Overriding : %s : %s : %s : (%s) : %s", cls.__name__, args, kwargs, x, current)
                cls._registry[x] = cls
            case x if x not in cls._registry:
                logging.debug("Registering: %s : %s : %s : (%s)", cls.__name__, args, kwargs, x)
                cls._registry.setdefault(x, cls)

    @classmethod
    def __class_getitem__(cls:type, *params:Any) -> type: # type:ignore  # noqa: ANN401
        match cls._registry.get(params[0], None):  # type: ignore[attr-defined]
            case None:
                logging.debug("No Registered annotation class: %s :%s", cls, params)
                return super().__class_getitem__(*params)  # type: ignore[misc]
            case x:
                return x

    @classmethod
    def get_registered(cls, *, param:Maybe=None) -> Self:
        param = param or cls.cls_annotation()
        return cls._registry.get(param, cls)

    @classmethod
    def maybe_subclass(cls, *, param:Maybe=None) -> Maybe[Self]:
        param = param or cls.cls_annotation()
        return cls._registry.get(param, None)
