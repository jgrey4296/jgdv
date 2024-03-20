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

from dejavu.files_formats.tags.base import TagFile

@dataclass
class IndexFile(TagFile):
    """ Utility class for index file specification and writing """

    mapping : Dict[str, Set[pl.Path]] = field(default_factory=lambda: defaultdict(set))
    ext     : str                 = field(default=".index")

    def __iadd__(self, value) -> IndexFile:
        return self.update(value)

    def __str__(self):
        """
        Export the mapping, 1 key per line, as:
        `key` : `len(values)` : ":".join(`values`)
        """
        key_sort = sorted(list(self.mapping.keys()))
        total = [self.sep.join([k, str(self.counts[k])]
                               + sorted(str(y) for y in self.mapping[k]))
                 for k in key_sort]
        return "\n".join(total)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {len(self)}>"

    def update(self, *values):
        for val in values:
            match val:
                case (str() as key, maybecount, *rest):
                    paths = set(pl.Path(x) for x in rest)
                    try:
                        count = int(maybecount)
                    except ValueError:
                        paths.add(pl.Path(count))
                        count = len(paths)

                    norm_key = self._inc(key, amnt=count)
                    self.mapping[norm_key].update(paths)
                case _:
                    raise TypeError("Unexpected form in index update", val)

        return self

    def files_for(self, *values, op="union"):
        the_files = None
        match op:
            case "union":
                fn = lambda x, y: x & y
            case "diff":
                fn = lambda x, y: x | y
            case "xor":
                fn = lambda x, y: x ^ y
            case "rem":
                fn = lambda x, y: x - y
            case _:
                raise TypeError("Bad Op specified: ", op)

        for val in values:
            match the_files:
                case None if val in self.mapping:
                    the_files = self.mapping[val]
                case None:
                    continue
                case {} if op != "union":
                    return the_files
                case _:
                    the_files = fn(the_files, self.mapping[val])

        return the_files
