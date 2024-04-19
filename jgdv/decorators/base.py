#!/usr/bin/env python2
"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import inspect
import abc
from typing import Type
import decorator

FUNC_WRAPPED     : Final[str]                = "__wrapped__"
jgdv_ANNOTATIONS : Final[str]                = "__JGDV_ANNOTATIONS__"
WRAPPER          : Final[str]                = "__wrapper"


class JGDVBaseDecorator(abc.ABC):
    """ Base Class for decorators that annotate action callables
      set self._annotations:dict to add annotations to fn.__DOOT_ANNOTATIONS (:set)
      implement self._wrapper to add a wrapper around the fn.
      TODO: set self._idempotent=True to only add a wrapper once
      """

    def __init__(self):
        self._idempotent  = False
        self._annotations =  set()

    def __call__(self, fn):
        if bool(self._annotations):
            self.annotate(fn, self._annotations)

        if not hasattr(self, WRAPPER):
            return fn

        if isinstance(fn, Type):
            return self.wrap_method(fn, fn.__call__, self._wrapper)

        decorated = decorator.decorate(fn, self._wrapper)
        return decorated

    def _strip_wrappers(self, fn:callable) -> callable:
        return inspect.unwrap(fn)

    def has_annotations(self, fn, *keys) -> bool:
        base = self._strip_wrappers(fn)
        if not hasattr(base, jgdv_ANNOTATIONS):
            return False

        annots = getattr(base, jgdv_ANNOTATIONS)
        return all(key in annots for key in keys)

    def annotate(self, fn:callable, annots:set) -> callable:
        base = self._strip_wrappers(fn)
        if not hasattr(base, jgdv_ANNOTATIONS):
            setattr(base, jgdv_ANNOTATIONS, set())

        annotations = getattr(base, jgdv_ANNOTATIONS)
        for cls in getattr(fn, '__mro__', []):
            annotations.update(getattr(cls, jgdv_ANNOTATIONS, {}))

        annotations.update(annots)
        return fn

    def wrap_method(self, obj:Type, method:callable, wrapper:callable) -> Type:
        wrapped = decorator.decorate(method, wrapper)
        setattr(obj, method.__name__, wrapped)
        return obj

    def truncate_signature(self, fn):
        """
           actions are (self?, spec, state)
          with and extracted keys from the spec and state.
          This truncates the signature of the action to what is *called*, not what is *used*.

          TODO: could take a callable as the prototype to build the signature from
        """
        sig              = inspect.signature(fn)
        min_index        = len(sig.parameters) - len(getattr(fn, "_doot_keys"))
        newsig           = sig.replace(parameters=list(sig.parameters.values())[:min_index])
        fn.__signature__ = newsig
        return fn

