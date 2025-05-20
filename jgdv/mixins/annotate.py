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
MODULE_NAME              : Final[str]  = "__module__"
SLOTS_NAME               : Final[str]  = "__slots__"
ANNOTS_NAME              : Final[str]  = "__annotations__"

AnnotateKWD              : Final[str]  = "_annotate_to"
AnnotationTarget         : Final[str]  = "_typevar"
AnnotateRx               : Final[Rx]   = re.compile(r"(?P<name>\w+)(?:<(?P<extras>.*?)>)?(?:\[(?P<params>.*?)\])?")

MultiParamFail           : Final[str]  = "Multi Param Annotation not supported yet"
BadParamFail             : Final[str]  = "Bad param value for making an annotated subclass"
NoPydanticFail           : Final[str]  = "Extending pydantic classes with a new mro is not implemented"

BadDecorationNameTarget  : Final[str]  = "Unexpected name decoration target"
NoNameMatch              : Final[str]  = "Couldn't even match the cls name"
NoSubName                : Final[str]  = "No decorated name available"
UnexpectedMRO            : Final[str]  = "Unexpected mro type"
UnexpectedNameSpace      : Final[str]  = "Unexpected namespace type"
##--| Body

class Subclasser:
    """ A Util class for building subclasses programmatically

    Subclasses can have modified mro's,
    Also extended namespaces,
    And preserve the base class' __slots__/__dict__ state

    """

    @staticmethod
    def decorate_name(cls:str|type, *vals:str, params:Maybe[str]=None) -> Maybe[str]:  # noqa: PLW0211
        """ Create a new name for an annotated subclass

        decorate(cls, a,b,c) -> cls<+a+b+c>
        decorate(cls, params='blah') -> cls[blah]
        """
        name         : str
        annotations  : Maybe[str]  = None
        set_extras   : set[str]    = set(vals)

        match cls:
            case x if not (bool(params) or bool(vals)):
                return None
            case type() as x:
                name = x.__name__
            case str() as x:
                name = x
            case x:
                raise TypeError(BadDecorationNameTarget, x)

        match AnnotateRx.match(name):
            case re.Match() as mtch:
                set_extras.update({y for y in (mtch['extras'] or "").split("+") if bool(y)})
                params  = params or mtch['params'] or None
                name    = mtch['name'] or name
            case _:
                raise ValueError(NoNameMatch, cls)

        if bool(set_extras):
            annotations = "+".join(x for x in sorted(set_extras) if bool(x))

        match annotations, params:
            case str() as x, None:
                return f"{name}<+{x}>"
            case None, str() as x:
                return f"{name}[{params}]"
            case str() as x, str() as y:
                return f"{name}<+{x}>[{y}]"
            case _:
                return None

    def annotate[T](self, cls:type[T], *params:Any) -> type[T]:  # noqa: ANN401
        """ Make a subclass of cls,

        annotated to have params in getattr(cls, '_annotate_to', '_typevar')
        """
        p_str        : str
        def_mod      : str
        subname      : str
        namespace    : dict
        anno_target  : str  = getattr(cls, AnnotateKWD, AnnotationTarget)
        anno_type    : str  = "ClassVar[str]"
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
                raise NotImplementedError(MultiParamFail)
            case _:
                raise ValueError(BadParamFail, params)

        # Get the module definer 3 frames up.
        # So not annotate, or __class_getitem__, but where the subclass is created
        def_mod = _caller(3)
        match self.decorate_name(cls, params=p_str):
            case str() as x:
                subname   = x
                namespace = {
                    anno_target : param,
                    MODULE_NAME : def_mod,
                    ANNOTS_NAME : {anno_target : anno_type},
                }
                sub = self.make_subclass(subname, cls, namespace=namespace)
                setattr(sub, anno_target , param)  # type: ignore[attr-defined]
                return sub
            case _:
                raise ValueError(NoSubName)

    def make_generic[T](self, cls:type[T], *params:Any) -> GenericAlias:  # noqa: ANN401
        return GenericAlias(cls, *params)

    def make_subclass[T](self, name:str, cls:type[T], *, namespace:Maybe[dict]=None, mro:Maybe[Iterable]=None) -> type[T]:
        """
        Build a dynamic subclass of cls, with name,
        possibly with a maniplated mro and internal namespace
        """
        if (ispydantic:=issubclass(cls, BaseModel)) and mro is not None:
            raise NotImplementedError(NoPydanticFail)
        elif ispydantic:
            sub = self._new_pydantic_class(name, cls, namespace=namespace)
            return sub
        else:
            sub = self._new_std_class(name, cls, namespace=namespace, mro=mro)
            return sub

    def _new_std_class[T](self, name:str, cls:type[T], *, namespace:Maybe[dict]=None, mro:Maybe[Iterable]=None) -> type[T]:
        """
        Dynamically creates a new class
        """
        from types import new_class
        assert(not issubclass(cls, BaseModel)), cls
        mod_name  : str
        mcls      : type[type]  = type(cls)
        if name == cls.__name__:
            name = f"{name}<+>"

        match namespace:
            case dict():
                pass
            case _:
                namespace = {}
        match mro:
            case None:
                mro = cls.mro()
            case tuple() | list():
                pass
            case x:
                raise TypeError(UnexpectedMRO, x)
        ##--|
        assert(namespace is not None)
        # Expand out generics by calling __mro_entries__
        match (mro:=tuple(resolve_bases(mro))):
            case [x, *_]: # Use the base class module name
                mod_name = x.__dict__[MODULE_NAME]
                namespace.setdefault(MODULE_NAME, mod_name)
            case _:
                raise ValueError()

        # mro_dict = ChainMap(*(getattr(c, '__dict__', {}) for c in cls.mro()))
        namespace.setdefault(SLOTS_NAME, ())
        try:
            return mcls(name, mro, namespace)
        except TypeError as err:
            err.add_note(str(mro))
            raise

    def _new_pydantic_class(self, name:str, cls:type, *, namespace:Maybe[dict]=None) -> type:
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
    __slots__ = ()

    __builder     : ClassVar[Subclasser]  = Subclasser()
    _annotate_to  : ClassVar[str]         = AnnotationTarget

    def __init_subclass__(cls, **kwargs:Any) -> None:  # noqa: ANN401
        """ On init of a subclass, ensure it's annotation target is set

        TODO does this need to call super?
        """
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
