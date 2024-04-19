#!/usr/bin/env python3
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
# import more_itertools as mitz
# from boltons import
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

T = TypeVar('T')
P = ParamSpec('P')


def ForceListArgDecorator(f:Callable[..., T]) -> Callable[..., T]:
    """ Force the first arg to be a list """

    @wraps(f)
    def wrapped(self, *the_args, **the_kwargs):
        forced = []
        if isinstance(the_args[0], list):
            forced = the_args
        else:
            forced.append([the_args[0]])
            forced += the_args[1:]

        return f(self, *forced, **the_kwargs)

    return wrapped

def cache(f:Callable[..., T]) -> Callable[..., T]:
    cache_key : str = f"{f.__name__}.__cached_val"

    @wraps(f)
    def wrapped(self, *args, **kwargs):
        if hasattr(self, cache_key): #type:ignore
            return cast(T, getattr(self, cache_key)) #type:ignore

        object.__setattr__(self, cache_key, f(self, *args, **kwargs)) #type:ignore
        return getattr(self, cache_key) #type:ignore

    wrapped.__name__ = f"Cached({f.__name__})"
    return wrapped #type:ignore

def invalidate_cache(f:Callable[..., T]) -> Callable[..., T]:
    cache_key = f"{f.__name__}__cached_val"

    @wraps(f)
    def wrapped(self, *args, **kwargs):
        if hasattr(self, cache_key): #type:ignore
            object.__setattr__(self, cache_key, None) #type:ignore

        return f(self, *args, **kwargs)

    wrapped.__name__ = f"CacheInvalidatator({f.__name__})"
    return wrapped

def HandleSignal(sig : str) -> Callable[..., Any]:
    """
    Utility to easily add a signal to classes for use in the handler system
    """

    def __add_sig(sig, method):
        """ used to add 'signal' as an argument to a class' init method """

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if 'signal' not in kwargs:
                kwargs['signal'] = sig #type:ignore
            return method(self, *args, **kwargs)

        return wrapper

    def wrapper(cls):
        cls.__init__ = __add_sig(sig, cls.__init__) #type:ignore
        return cls

    return wrapper

def factory(f:Callable[..., T]) -> Callable[..., T]:
    """
    Curry a constructor, naming it in a useful way

    """

    @wraps(f)
    def awaiting_arg(first_arg:Any) -> Callable[..., T]:

        @wraps(f)
        def ready_to_apply(*args:Any, **kwargs:Any) -> T:
            return f(first_arg, *args, **kwargs)

        ready_to_apply.__name__ = f"{f.__name__} partial"
        return ready_to_apply

    return awaiting_arg #type:ignore
