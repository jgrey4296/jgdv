#!/usr/bin/env python3
"""



"""

from __future__ import annotations

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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match, Self,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class AnnotateSubclass_m:
    """
    Enable ClassName[int] and ClassName['blah'] subclasses variants,
    to annotate the purpose of the Strang

    TODO maybe use an explicit cache instead of ftz.cache
    TODO replace _typevar with a controllable name
    TODO add a standard lookup method for whatever _typevar is
    """

    @classmethod
    @ftz.cache
    def __class_getitem__(cls, *params) -> Self:
        """ Auto-subclass as {cls.__name__}[param]"""
        match params[0]:
            case type() as param:
                p_str = param.__name__
            case str() as param:
                p_str = param

        sub = type(f"{cls.__name__}[{p_str}]", (cls,), {"_typevar":param})
        return sub
