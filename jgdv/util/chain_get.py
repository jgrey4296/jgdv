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

from jgdv._abstract.protocols import SpecStruct_p

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class ChainedKeyGetter:
    """
      The core logic to turn a key into a value.
      Doesn't perform repeated expansions.

      tries sources in order.
    """

    @staticmethod
    def chained_get(key:str, *sources:dict|SpecStruct_p|JGDVLocations, fallback=None) -> None|Any:
        """
        Get a key's value from an ordered sequence of potential sources.
        Try to get {key} then {key_} in order of sources passed in
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
                    raise TypeError("Unknown Type in chained_get", source)

            if replacement is not fallback:
                return replacement

        return fallback
