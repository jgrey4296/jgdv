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
    Self,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    _caller,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

from jgdv import Maybe

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

AnnotationTarget : Final[str] = "_typevar"

class SubAnnotate_m:
    """
    A Mixin to create simple subclasses through annotation.
    Annotation var name can be customized through the subclass kwarg 'AnnotateTo'.
    eg:
    class MyExample(SubAnnotate_m, AnnotateTo='blah'):
        pass

    a_sub = MyExample[int]
    a_sub.__class__.blah == int

    """

    _AnnotateTo: ClassVar[str] = AnnotationTarget

    def __init_subclass__(cls, **kwargs):
        match kwargs:
            case {"AnnotateTo": target}:
                logging.debug("Annotate Subclassing: %s : %s", cls, kwargs)
                del kwargs['AnnotateTo']
                cls._AnnotateTo = target
                setattr(cls, cls._AnnotateTo, None)
            case _ if not hasattr(cls, cls._AnnotateTo):
                setattr(cls, cls._AnnotateTo, None)



    @classmethod
    def _get_annotation(cls) -> Maybe[str]:
        return getattr(cls, cls._AnnotateTo)

    @classmethod
    @ftz.cache
    def __class_getitem__(cls, *params) -> Self:
        """ Auto-subclass as {cls.__name__}[param]"""
        logging.debug("Annotating: %s : %s : (%s)", cls.__name__, params, cls._AnnotateTo)
        match params:
            case []:
                return cls
            case [type() as param]:
                p_str = param.__name__
            case [str() as param]:
                p_str = param
            case [param]:
                p_str = str(param)
            case [param, *params]:
                raise NotImplementedError("Multi Param Annotation not supported yet")

        def_mod = _caller()
        subname = f"{cls.__name__}[{p_str}]"
        subdata = {cls._AnnotateTo : param,
                   "__module__"     : def_mod,
                   "__supertype__"  : cls,
                   "__qualname__"   : f"{def_mod}.{subname}"
                   }
        sub = type(subname, (cls,), subdata)
        setattr(sub, cls._AnnotateTo, param)
        return sub


class SubRegistry_m(SubAnnotate_m):
    """ Create Subclasses in a registry """

    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        logging.debug("Registry Subclass: %s : %s : %s", cls, args, kwargs)
        super().__init_subclass__(*args, **kwargs)
        match getattr(cls, "_registry", None):
            case None:
                logging.debug("Creating Registry: %s : %s : %s", cls.__name__, args, kwargs)
                cls._registry = {}
            case _:
                pass
        match cls._get_annotation():
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
    def __class_getitem__(cls, param) -> Self:
        match cls._registry.get(param, None):
            case None:
                logging.debug("No Registered annotation class: %s :%s", cls, param)
                return super().__class_getitem__(param)
            case x:
                return x


    @classmethod
    def _get_subclass_form(cls, *, param=None) -> Self:
        param = param or cls._get_annotation()
        return cls._registry.get(param, cls)
