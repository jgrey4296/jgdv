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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, NewType, _caller
from typing import TypeAliasType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from types import resolve_bases
from pydantic import BaseModel, create_model

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

AnnotateKWD      : Final[str] = "annotate_to"
AnnotationTarget : Final[str] = "_typevar"

class Subclasser:

    @staticmethod
    def make_annotated_subclass(cls, *params) -> type:
        """ Make a subclass of cls,
        annotated to have params in cls[cls._annotate_to]
        """
        match params:
            case [NewType() as param]:
                p_str = param.__name__
            case [TypeAliasType() as param]:
                p_str = param.__value__.__name__
            case [type() as param]:
                p_str = param.__name__
            case [str() as param]:
                p_str = param
            case [param]:
                p_str = str(param)
            case [param, *params]:
                raise NotImplementedError("Multi Param Annotation not supported yet")
            case _:
                raise ValueError("Bad param value for making an annotated subclass", params)


        # Get the module definer 3 frames up.
        # So not make_annotated_subclass, or __class_getitem__, but where the subclass is created
        def_mod = _caller(3)
        subname = f"{cls.__name__}[{p_str}]"
        subdata = {cls._annotate_to : param,
                   "__module__" : def_mod,
                   }
        sub = Subclasser.make_subclass(subname, cls, namespace=subdata)
        setattr(sub, cls._annotate_to, param)
        return sub

    @staticmethod
    def make_subclass(name:str, cls:type, *, namespace:Maybe[dict]=None, mro:Maybe[tuple]=None) -> type:
        """
        Build a dynamic subclass of cls, with name,
        possibly with a maniplated mro and internal namespace
        """
        if (ispydantic:=issubclass(cls, BaseModel)) and mro is not None:
                raise NotImplementedError("Extending pydantic classes with a new mro is not implemented")
        elif ispydantic:
            sub = Subclasser._new_pydantic_class(name, cls, namespace=namespace)
            return sub
        else:
            sub = Subclasser._new_std_class(name, cls, namespace=namespace, mro=mro)
            return sub

    @staticmethod
    def _new_std_class(name:str, cls:type, *, namespace:Maybe[dict]=None, mro:Maybe[tuple]=None) -> type:
        """
        Dynamically creates a new class
        """
        assert(not issubclass(cls, BaseModel)), cls
        mcls = type(cls)
        match mro:
            case None:
                mro = cls.mro()
            case tuple() | list():
                mro = mro
            case x:
                raise TypeError("Unexpected mro type", x)
        ##--|
        mro = tuple(resolve_bases(mro))
        match namespace:
            case None:
                namespace = mcls.__prepare__(name, mro)
            case dict():
                namespace = mcls.__prepare__(name, mro) | namespace
            case x:
                raise TypeError("Unexpected namespace type", x)
        return mcls(name, mro, namespace)

    @staticmethod
    def _new_pydantic_class(name:str, cls:type, *, namespace:Maybe[dict]=None) -> type:
        assert(issubclass(cls, BaseModel)), cls
        sub = create_model(name, __base__=cls)
        for x,y in (namespace or {}).items():
            setattr(sub, x, y)
        return sub

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

    _annotate_to : ClassVar[str] = AnnotationTarget

    def __init_subclass__(cls, **kwargs):
        """ TODO does this need to call super? """
        match kwargs.get(AnnotateKWD, None):
            case str() as target:
                logging.debug("Annotate Subclassing: %s : %s", cls, kwargs)
                del kwargs[AnnotateKWD]
                cls._annotate_to = target
                setattr(cls, cls._annotate_to, None)
            case None if not hasattr(cls, cls._annotate_to):
                setattr(cls, cls._annotate_to, None)
            case _:
                pass

    @classmethod
    @ftz.cache
    def __class_getitem__(cls, *params) -> Self:
        """ Auto-subclass as {cls.__name__}[param]"""
        logging.debug("Annotating: %s : %s : (%s)", cls.__name__, params, cls._annotate_to)
        match params:
            case []:
                return cls
            case _:
                return Subclasser.make_annotated_subclass(cls, *params)

    @classmethod
    def _get_annotation(cls) -> Maybe[str]:
        return getattr(cls, cls._annotate_to, None)



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

    @classmethod
    def _maybe_subclass_form(cls, *, param=None) -> Maybe[Self]:
        param = param or cls._get_annotation()
        return cls._registry.get(param, None)
