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

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from types import GenericAlias, resolve_bases
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never, TypeAliasType
from typing import no_type_check, final, override, overload, _caller # type: ignore[attr-defined]
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, create_model

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
                raise TypeError(API.BadDecorationNameTarget, x)

        match API.AnnotateRx.match(name):
            case re.Match() as mtch:
                set_extras.update({y for y in (mtch['extras'] or "").split("+") if bool(y)})
                params  = params or mtch['params'] or None
                name    = mtch['name'] or name
            case _:
                raise ValueError(API.NoNameMatch, cls)

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
        anno_target  : str  = getattr(cls, API.AnnotateKWD, API.AnnotationTarget)
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
            case [_, *_]:  # type: ignore[misc]
                raise NotImplementedError(API.MultiParamFail, params)
            case _:
                raise ValueError(API.BadParamFail, params)

        # Get the module definer 3 frames up.
        # So not annotate, or __class_getitem__, but where the subclass is created
        def_mod = _caller(3)
        match self.decorate_name(cls, params=p_str):
            case str() as x:
                subname   = x
                namespace = {
                    anno_target : param,
                    API.MODULE_NAME : def_mod,
                    API.ANNOTS_NAME : {anno_target : anno_type},
                }
                sub = self.make_subclass(subname, cls, namespace=namespace)
                setattr(sub, anno_target , param)  # type: ignore[attr-defined]
                return sub
            case _:
                raise ValueError(API.NoSubName)

    def make_generic[T](self, cls:type[T], *params:Any) -> GenericAlias:  # noqa: ANN401
        return GenericAlias(cls, *params)

    def make_subclass[T](self, name:str, cls:type[T], *, namespace:Maybe[dict]=None, mro:Maybe[Iterable]=None) -> type[T]:
        """
        Build a dynamic subclass of cls, with name,
        possibly with a maniplated mro and internal namespace
        """
        if (ispydantic:=issubclass(cls, BaseModel)) and mro is not None:
            raise NotImplementedError(API.NoPydanticFail)
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
        assert(not issubclass(cls, BaseModel)), cls
        mod_name  : str
        mcls      : type[type]  = type(cls)

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
                raise TypeError(API.UnexpectedMRO, x)
        ##--|
        assert(namespace is not None)
        # Expand out generics by calling __mro_entries__
        match (mro:=tuple(resolve_bases(mro))):
            case [x, *_]: # Use the base class module name
                mod_name = x.__dict__[API.MODULE_NAME]
                namespace.setdefault(API.MODULE_NAME, mod_name)
            case _:
                raise ValueError()

        namespace.setdefault(API.SLOTS_NAME, ())
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
