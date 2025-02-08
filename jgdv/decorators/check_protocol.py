#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
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
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

from .core import DecoratorBase

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

def check_protocol(cls):
    """ Decorator. Check the class implements all its methods / has no abstractmethods """
    abstracts      = getattr(cls, "__abstractmethods__", dir(cls))
    def _test_method(cls, name) -> bool:
        if name == "__abstractmethods__":
            return False
        meth = getattr(cls, name)
        if not hasattr(meth,  "__isabstractmethod__"):
            return False

        return meth.__isabstractmethod__

    still_abstract = [x for x in abstracts if _test_method(cls, x)]
    if bool(still_abstract):
        raise NotImplementedError("Class has Abstract Methods", cls.__module__, cls.__name__, still_abstract)

    return cls

# --------------------------------------------------

class CheckProtocol(DecoratorBase):
    """ A Class Decorator to ensure a class has no abc.abstractmethod's
    or unimplemented protocol members

    pass additional protocols when making the decorator,
    eg:
    @CheckProtocol(Proto1_p, Proto2_p, AbsClass...)
    class MyClass:
    pass
    """

    def __init__(self, *args):
        super().__init__()

    def _test_method(self, cls:type, name:str) -> bool:
        if name == "__abstractmethods__":
            return False
        meth = getattr(cls, name)
        if not hasattr(meth,  "__isabstractmethod__"):
            return False

        return meth.__isabstractmethod__

    def _get_protos(self, cls) -> list[Protocol]:
        return [x for x in cls.__mro__
                if issubclass(x, Protocol)
                and x is not cls
                and x is not Protocol]


    
    def _test_protocol(self, proto:Protocol, cls) -> list[str]:
        result = []
        for member in proto.__protocol_attrs__:
            meth = getattr(cls, member)
            if proto.__qualname__ in meth.__qualname__:
                result.append(member)
        else:
            return result

    def _mod_class(self, cls:type) -> None:
        abstracts      = getattr(cls, "__abstractmethods__", dir(cls))
        still_abstract = {x for x in abstracts if self._test_method(cls, x)}
        for proto in self._get_protos(cls):
            still_abstract.update(self._test_protocol(proto, cls))

        if not bool(still_abstract):
            return

        raise NotImplementedError("Class has Abstract Methods", cls.__module__, cls.__name__, still_abstract)
