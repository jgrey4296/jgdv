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
type AliasAnnotation = type|str|enum.Enum|Literal[False]|Literal[True]|tuple[AliasAnnotation, ...]

# Body:

class SubAlias_m:
    """ A Mixin to manage generics that resolve to specific registered subclasses.

    On class declaration, recognizes kwargs:
    - fresh_registry:bool                         : use a separate registry for this class and subclasses
    - accumulate:bool                             : annotations accumulate from their parent class
    - strict:bool                                 : error if a subclass tries to overwrite a registration
    - default:bool                                : set this subclass as the default if no marks are specified when creating an instance
    - annotation:Maybe[str|type|enum|tuple[...]]  : the key to use for this subclass, if class_getitem hasn't been used
    - no_register:bool                            : create the class, but don't register it

    cls[val] -> GenericAlias(cls, val)

    then:

    class RealSub(cls[val]) ...
    after which:
    cls[val] is RealSub

    Annotation Keys are stored in cls.__annotation__,
    under the cls._annotate_to key name.

    """
    __slots__                                              = ()
    _annotate_to  : ClassVar[str]                          = API.AnnotationTarget
    _default_k    : ClassVar[str]                          = API.Default_K
    # TODO make this a weakdict?
    _registry     : ClassVar[dict[AliasAnnotation, type]]  = {}
    _strict       : ClassVar[bool]                         = False
    _accumulator  : ClassVar[bool]                         = False

    def __init_subclass__(cls:type[Self], *args:Any, annotation:Maybe[AliasAnnotation]=None, fresh_registry:bool=False, **kwargs:Any) -> None:  # noqa: ANN401
        x  : Any
        overwrite : bool
        # ensure a new annotations dict
        # (if a subclass doesn't add *new* annotations, the super's is used. so if we modify it here,
        # the subclass is effected)
        cls.__annotations__  = cls.__annotations__.copy()
        overwrite            = kwargs.pop("overwrite", False)
        if (strict:=kwargs.pop("strict", None)):
            cls._strict = strict or cls._strict
        if (accumulate:=kwargs.pop("accumulate", None)):
            cls._accumulator = accumulate or cls._accumulator

        if fresh_registry:
            cls._registry    = {}

        if kwargs.pop("default", None) is True:
            cls._registry[cls._default_k] = cls

        # set the annotation target
        match kwargs.pop(API.AnnotateKWD, None):
            case str() as target:
                logging.debug("Annotate Subclassing: %s : %s", cls, kwargs)
                cls._annotate_to               = target
                setattr(cls, cls._annotate_to, None)
            case None if not hasattr(cls, cls._annotate_to):
                setattr(cls, cls._annotate_to, None)
            case _:
                pass

        annotation                             = cls._build_annotation(annotation)
        cls.__annotations__[cls._annotate_to]  = annotation
        if kwargs.pop("no_register", False):
            return

        match annotation, cls._registry.get(annotation, None):
            case (), _: # No annotation
                pass
            case _, None: # No registered cls
                cls._registry[annotation] = cls
            case _, x if overwrite:
                cls._registry[annotation] = cls
            case _, x if cls._strict: # complain there s a cls
                msg = "already has a registration"
                raise TypeError(msg, x, cls, annotation, args, kwargs)

    def __class_getitem__[K:AliasAnnotation](cls:type[Self], *key:K) -> type|GenericAlias:
        return cls._retrieve_subtype(*key)

    @classmethod
    def _retrieve_subtype[K:AliasAnnotation](cls:type[Self], key:K) -> type|GenericAlias:
        use_key : AliasAnnotation = cls._build_annotation(key)
        match cls._registry.get(use_key, None):
            case type() as result:
                return result
            case None if use_key == () and cls._default_k in cls._registry:
                return cls._registry[cls._default_k]
            case _:
                return GenericAlias(cls, use_key)

    @classmethod
    def _clear_registry(cls) -> None:
        cls._registry.clear()

    @classmethod
    def cls_annotation(cls) -> tuple:
        return cls.__annotations__.get(cls._annotate_to, ())

    @classmethod
    def _build_annotation(cls, annotate:Maybe[AliasAnnotation]) -> AliasAnnotation:  # noqa: PLR0912
        """ single point of truth for determining annotations from a cls and provided annotation """
        x : Any
        result : list[AliasAnnotation] = []
        assert(hasattr(cls, "cls_annotation"))

        match cls.cls_annotation():
            case []:
                pass
            case tuple() as x:
                result += x

        match cls.__dict__.get(API.ORIG_BASES_K, []):
            case _ if bool(result):
                pass
            case [GenericAlias() as x]:
                result += x.__args__
            case _ if (annotated:=[x for x in cls.mro() if x is not cls and hasattr(x, "cls_annotation")]):
                result += annotated[0].cls_annotation()
            case _:
                pass

        match annotate:
            case None:
                pass
            case [[*xs]] if cls._accumulator:
                result += xs
            case tuple() as x if cls._accumulator:
                result += x
            case x if cls._accumulator:
                result.append(x)
            case [[*xs]]:
                result = [*xs]
            case [*xs]:
                result = [*xs]
            case x:
                result = [x]

        ##--|
        match result:
            case []:
                return ()
            case [x]:
                return tuple([x])
            case [*xs]:
                return tuple(xs)
            case _:
                return ()
