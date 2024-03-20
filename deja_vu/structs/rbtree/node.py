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

@dataclass
class Node(Tree):
    """ The Container for RBTree Data """

    red     : bool     = field(default=True)
    eq_func : Callable = field(default=None)

    def __repr__(self):
        #pylint: disable=too-many-format-args
        if self.value is not None and hasattr(self.value, "id"):
            return "({}_{})".format(ascii_uppercase[self.value.id % 26],
                                    int(self.value.id/26), self.id)
        else:
            return "({}:{})".format(self.value, self.id)

    def get_black_height(self):
        """ Get the number of black nodes between self and the root """
        current = self
        height = 0
        while current is not None:
            if not current.red:
                height += 1
            current = current.parent
        return height
