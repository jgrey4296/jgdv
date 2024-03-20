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
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import heapq

class DejaVuHeap:

    def __init__(self):
        self._heap = None

    def pop_while_same(self):
        """ Pop while the head is equal to the first value poppped """
        assert(all([isinstance(x, HeapWrapper) for x in self._heap]))
        first_vert, first_edge = heapq.heappop(self._heap).unwrap()
        if first_edge is None:
            return (first_vert, [])

        collected = (first_vert, [first_edge])
        count = 1
        while bool(self._heap) and self._heap[0].ordinal == first_vert:
            data = heapq.heappop(self._heap).data
            if data is not None:
                collected[1].append(data)
                count += 1
        assert(len(collected[1]) == count)
        return collected
