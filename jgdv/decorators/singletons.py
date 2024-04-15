#!/usr/bin/env python3
"""
Provides Metaclasses for creating Singletons

Note: superclass is type(Protocol) so classes which
implement protocol's don't get a metaclass conflict
"""
##-- imports
import logging as logmod
from fractions import Fraction
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence, Protocol,
                    Set, Tuple, TypeAlias, TypeVar, Union, cast)

##-- end imports

logging = logmod.getLogger(__name__)

from jgdv._interfaces.decorator import DejaVuDecorator_i

def singleton(orig_cls:Any) -> Any:
    """ From:
    https://igeorgiev.eu/python/design-patterns/python-singleton-pattern-decorator/
    """
    raise DeprecationWarning("use meta classes instead")
    orig_new = orig_cls.__new__
    instance = None

    @wraps(orig_cls.__new__)
    def __new__(cls, *args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = orig_new(cls, *args, **kwargs)
        return instance

    orig_cls.__new__ = __new__
    return orig_cls


