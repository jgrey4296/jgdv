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

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, NewType, _caller  # type: ignore[attr-defined]
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

AnnotateKWD      : Final[str] = "annotate_to"
AnnotationTarget : Final[str] = "_typevar"
AnnotateRx       : Final[Rx]  = re.compile(r"(?P<name>\w+)(?:<(?P<extras>.*?)>)?(?:\[(?P<params>.*?)\])?")

class Subclasser:

    @staticmethod
    def make_annotated_subclass(cls:type, *params:Any) -> type:  # noqa: ANN401, PLW0211
        """ Make a subclass of cls,
        annotated to have params in cls[cls._annotate_to]
        """
        match params:
            case [NewType() as param]:
                p_str = param.__name__  # type: ignore[attr-defined]
            case [TypeAliasType() as param]:
                p_str = param.__value__.__name__
            case [type() as param]:
                p_str = param.__name__
            case [str() as param]:
                p_str = param
            case [param]:
                p_str = str(param)
            case [param, *params]:  # type: ignore[misc]
                msg = "Multi Param Annotation not supported yet"
                raise NotImplementedError(msg)
            case _:
                msg = "Bad param value for making an annotated subclass"
                raise ValueError(msg, params)

        # Get the module definer 3 frames up.
        # So not make_annotated_subclass, or __class_getitem__, but where the subclass is created
        def_mod = _caller(3)
        subname = Subclasser.decorate_name(cls, params=p_str)
        subdata = {
            cls._annotate_to : param,  # type: ignore[attr-defined]
            "__module__" : def_mod,
        }
        sub = Subclasser.make_subclass(subname, cls, namespace=subdata)
        setattr(sub, cls._annotate_to, param)  # type: ignore[attr-defined]
        return sub

    @staticmethod
    def decorate_name(cls:str|type, *vals:str, params:Maybe[str]=None) -> str:  # noqa: PLW0211
        match cls:
            case type():
                cls = cls.__name__
            case str():
                pass
            case x:
                msg = "Unexpected name decoration target"
                raise TypeError(msg, x)

        if not bool(vals) and not params:
            return cls

        extras_str, params_str  = "", ""
        set_extras = set(vals)

        match AnnotateRx.match(cls):
            case None:
                msg = "Couldn't even match the cls name"
                raise ValueError(msg, cls)
            case re.Match() as x:  # type: ignore[misc]
                set_extras.update((x['extras'] or "").split("+"))  # type: ignore[index]
                params_str = params or x['params'] or ""  # type: ignore[index]

        set_extras = {x for x in set_extras if bool(x)}
        if bool(set_extras):
            extras_str = "+".join(sorted(set_extras))
            extras_str = f"<+{extras_str}>"
        if bool(params_str):
            params_str = f"[{params_str}]"

        return f"{x['name']}{extras_str}{params_str}"  # type: ignore[index]

    @staticmethod
    def make_subclass(name:str, cls:type, *, namespace:Maybe[dict]=None, mro:Maybe[tuple]=None) -> type:
        """
        Build a dynamic subclass of cls, with name,
        possibly with a maniplated mro and internal namespace
        """
        if (ispydantic:=issubclass(cls, BaseModel)) and mro is not None:
                msg = "Extending pydantic classes with a new mro is not implemented"
                raise NotImplementedError(msg)
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
                pass
            case x:
                msg = "Unexpected mro type"
                raise TypeError(msg, x)
        ##--|
        mro = tuple(resolve_bases(mro))
        match namespace:
            case None:
                # namespace = mcls.__prepare__(name, mro)
                namespace = {}
            case dict():
                # namespace = mcls.__prepare__(name, mro) | namespace
                pass
            case x:
                msg = "Unexpected namespace type"
                raise TypeError(msg, x)
        try:
            return mcls(name, mro, namespace)
        except TypeError as err:
            err.add_note(str(mro))
            raise

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

    def __init_subclass__(cls, **kwargs:Any) -> None:  # noqa: ANN401
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
    def __class_getitem__(cls:type, *params:Any) -> type:  # noqa: ANN401
        """ Auto-subclass as {cls.__name__}[param]"""
        logging.debug("Annotating: %s : %s : (%s)", cls.__name__, params, cls._annotate_to)  # type: ignore[attr-defined]
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
    def __init_subclass__(cls, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
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
    def __class_getitem__(cls:type, *params:Any) -> type: # type:ignore  # noqa: ANN401
        match cls._registry.get(params[0], None):  # type: ignore[attr-defined]
            case None:
                logging.debug("No Registered annotation class: %s :%s", cls, params)
                return super().__class_getitem__(*params)  # type: ignore[misc]
            case x:
                return x

    @classmethod
    def _get_subclass_form(cls, *, param:Maybe=None) -> Self:
        param = param or cls._get_annotation()
        return cls._registry.get(param, cls)

    @classmethod
    def _maybe_subclass_form(cls, *, param:Maybe=None) -> Maybe[Self]:
        param = param or cls._get_annotation()
        return cls._registry.get(param, None)
