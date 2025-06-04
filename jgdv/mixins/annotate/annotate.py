#!/usr/bin/env python3
"""

"""
# ruff: noqa: ERA001
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
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

from . import _interface as API # noqa: N812
from .subclasser import Subclasser

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, NewType, _caller  # type: ignore[attr-defined]
from types import GenericAlias
from typing import TypeAliasType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from types import resolve_bases
from pydantic import BaseModel, create_model

if TYPE_CHECKING:
   from jgdv import Maybe, Rx
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

##--| Vars

##--| Body

class SubAnnotate_m:
    """
    A Mixin to create simple subclasses through annotation.
    Annotation var name can be customized through the subclass kwarg 'annotate_to'.
    eg:

    class MyExample(SubAnnotate_m, annotate_to='blah'):
        pass

    a_sub = MyExample[int]
    a_sub.__class__.blah == int

    """
    __slots__ = ()

    __builder     : ClassVar[Subclasser]  = Subclasser()
    _annotate_to  : ClassVar[str]         = API.AnnotationTarget

    def __init_subclass__(cls, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        """ On init of a subclass, ensure it's annotation target is set

        """
        super().__init_subclass__(*args)
        match kwargs.pop(API.AnnotateKWD, None):
            case str() as target:
                logging.debug("Annotate Subclassing: %s : %s", cls, kwargs)
                cls._annotate_to = target
                setattr(cls, cls._annotate_to, None)
            case None if not hasattr(cls, cls._annotate_to):
                setattr(cls, cls._annotate_to, None)
            case _:
                pass

    @classmethod
    @ftz.cache
    def __class_getitem__[T:SubAnnotate_m](cls:type[T], *params:Any) -> type[T]:  # noqa: ANN401
        """ Auto-subclass as {cls.__name__}[param]

        Caches results to avoid duplicates
        """
        logging.debug("Annotating: %s : %s : (%s)", cls.__name__, params, cls._annotate_to)  # type: ignore[attr-defined]
        match params:
            case []:
                return cls
            case _:
                return cls.__builder.annotate(cls, *params)

    @classmethod
    def cls_annotation(cls) -> Maybe[str]:
        return getattr(cls, cls._annotate_to, None)
