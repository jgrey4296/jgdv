#!/usr/bin/env python3
"""


"""
# ruff: noqa:

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

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from types import GenericAlias
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

class SubAlias_m:
    """ Create and register alias of types.

    cls[val] -> GenericAlias(cls, val)

    then:

    class RealSub(cls[val]) ...
    so:
    cls[val] is RealSub

    the annotation is added into cls.__annotations__,
    under the cls._annotate_to key name.

    """
    __slots__                                    = ()
    _annotate_to  : ClassVar[str]                = API.AnnotationTarget
    # TODO make this a weakdict?
    _registry     : ClassVar[dict[tuple, type]]  = {}

    def __init_subclass__(cls:type[Self], *args:Any, annotation:Maybe=None, **kwargs:Any) -> None:  # noqa: ANN401, PLR0912
        x : Any
        # ensure a new annotations dict
        cls.__annotations__ = cls.__annotations__.copy()

        full_annotation : list = []

        if kwargs.pop(API.FreshKWD, False):
            cls._registry = {}

        # set the annotation target
        match kwargs.pop(API.AnnotateKWD, None):
            case str() as target:
                logging.debug("Annotate Subclassing: %s : %s", cls, kwargs)
                cls._annotate_to = target
                setattr(cls, cls._annotate_to, None)
            case None if not hasattr(cls, cls._annotate_to):
                setattr(cls, cls._annotate_to, None)
            case _:
                pass

        # If the subclass is based on a GenericAlias, copy the annotation
        match cls.__dict__.get(API.ORIG_BASES_K, []):
            case [GenericAlias() as x]:
                full_annotation += x.__args__
            case _:
                y : type[SubAlias_m]
                _, y, *_ = cls.mro()
                if y is not cls and hasattr(y, "cls_annotation"):
                    full_annotation += y.cls_annotation()

        match annotation:
            case None:
                pass
            case [*xs]:
                full_annotation += xs
            case x:
                full_annotation.append(x)

        ##--| Register
        cls.__annotations__[cls._annotate_to] = tuple(full_annotation)
        mark = cls.cls_annotation()
        match mark, cls._registry.get(mark, None):
            case (), _:
                pass
            case _, None:
                cls._registry[mark] = cls
            case _, x:
                msg = "already has a registration"
                raise TypeError(msg, x, cls, mark, args, kwargs)

    def __class_getitem__[K:type|LiteralString](cls:type[Self], *key:K) -> type|GenericAlias:
        return cls._retrieve_subtype(*key)

    @classmethod
    def _retrieve_subtype[K:type|LiteralString](cls:type[Self], *key:K) -> type|GenericAlias:
        use_key : tuple
        cls_key : tuple = cls.cls_annotation()
        match key:
            case [*xs]:
                use_key = (*cls_key, *xs)
            case x:
                use_key = (*cls_key, x)

        match cls._registry.get(use_key, None):
            case type() as result:
                return result
            case _:
                return GenericAlias(cls, use_key)

    @classmethod
    def _clear_registry(cls) -> None:
        cls._registry.clear()

    @classmethod
    def cls_annotation(cls) -> tuple:
        return cls.__annotations__.get(cls._annotate_to, ())
