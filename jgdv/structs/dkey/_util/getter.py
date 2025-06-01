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

# ##-- 1st party imports
from jgdv._abstract.protocols import SpecStruct_p
from .._interface import ExpInst_d, Key_p
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   from jgdv.structs.locator import JGDVLocator

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class ChainGetter:
    """ The core logic to turn a key into a value.

    | Doesn't perform repeated expansions.
    | Tries sources in order.

    TODO replace this with collections.ChainMap ?
    """

    @staticmethod
    def get(key:str, *sources:dict|SpecStruct_p|JGDVLocator, fallback:Maybe=None) -> Maybe[Any]:
        """ Get a key's value from an ordered sequence of potential sources.

        | Try to get {key} then {key\\_} in order of sources passed in.
        """
        replacement = fallback
        for source in sources:
            match source:
                case None | []:
                    continue
                case list():
                    replacement = source.pop()
                case _ if hasattr(source, "get"):
                    if key not in source:
                        continue
                    replacement = source.get(key, fallback)
                case SpecStruct_p():
                    params      = source.params
                    replacement = params.get(key, fallback)
                case _:
                    msg = "Unknown Type in get"
                    raise TypeError(msg, key, source)

            if replacement is not fallback:
                return replacement

        return fallback



    @staticmethod
    def lookup(target:list[ExpInst_d], sources:list, *, ctor:type[Key_p])-> Maybe[ExpInst_d]:  # noqa: PLR0911, PLR0912
        """ Handle lookup instructions

        | pass through DKeys and (DKey, ..)
        | lift (str(), True, fallback)
        | don't lift (str(), False, fallback)

        """
        assert(ctor is not None)
        for spec in target:
            match spec:
                case ExpInst_d(value=Key_p()):
                    return spec
                case ExpInst_d(literal=True):
                    return spec
                case ExpInst_d(value=str() as key, lift=lift, fallback=fallback):
                    pass
                case x:
                    msg = "Unrecognized lookup spec"
                    raise TypeError(msg, x)

            match ChainGetter.get(key, *sources):
                case None:
                    pass
                case str() as x if lift:
                    logging.debug("Lifting Result to Key: %r", x)
                    lifted = ctor(x, implicit=True, fallback=fallback)
                    return ExpInst_d(value=lifted, fallback=lifted, lift=False)
                case pl.Path() as x:
                    match ctor(str(x)):
                        case Key_p(nonkey=True) as y:
                            return ExpInst_d(value=y, rec=0)
                        case y:
                            return ExpInst_d(value=y, fallback=fallback)
                case str() as x:
                    match ctor(x):
                        case Key_p(nonkey=True) as y:
                            return ExpInst_d(value=y, rec=0)
                        case y:
                            return ExpInst_d(value=y, fallback=fallback)
                case x:
                    return ExpInst_d(value=x, fallback=fallback)

        else:
            return None
