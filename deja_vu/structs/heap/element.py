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

@dataclass
class HeapElement:
    """ Utility to wrap an ordinal with data to use in the heap """
    ordinal : int
    data    : Any
    desc    : str = field(default=None)

    def __lt__(self, other):
        assert(isinstance(other, HeapWrapper))
        return self.ordinal < other.ordinal

    def unwrap(self):
        """ Unwrap the data """
        return (self.ordinal, self.data)

    def __repr__(self):
        if self.desc is None:
            return "{} - {}".format(self.ordinal, repr(self.data))
        else:
            return "{} - {} : {}".format(self.ordinal, self.desc, repr(self.data))
