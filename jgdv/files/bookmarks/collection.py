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
class BookmarkCollection:

    entries : List[Bookmark] = field(default_factory=list)
    ext     : str            = field(default=".bookmarks")

    @staticmethod
    def read(fpath:pl.Path) -> BookmarkCollection:
        """ Read a file to build a bookmark collection """
        bookmarks = BookmarkCollection()
        for line in (x.strip() for x in fpath.read_text().split("\n")):
            if not bool(line):
                continue
            bookmarks += Bookmark.build(line)

        return bookmarks

    def __str__(self):
        return "\n".join(map(str, sorted(self.entries)))

    def __repr__(self):
        return f"<{self.__class__.__name__}: {len(self)}>"

    def __iadd__(self, value):
        return self.update(value)

    def __iter__(self):
        return iter(self.entries)

    def __contains__(self, value:Bookmark):
        return value in self.entries

    def __len__(self):
        return len(self.entries)

    def __hash__(self):
        return id(self)
    def update(self, *values):
        for val in values:
            match val:
                case Bookmark():
                    self.entries.append(val)
                case BookmarkCollection():
                    self.entries += val.entries
                case [*vals] | set(vals):
                    self.update(*vals)
                case _:
                    raise TypeError(type(val))
        return self

    def difference(self, other:BookmarkCollection):
        result = BookmarkCollection()
        for bkmk in other:
            if bkmk not in self:
                result += bkmk

        return result

    def merge_duplicates(self):
        deduplicated = {}
        for x in self:
            if x.url not in deduplicated:
                deduplicated[x.url] = x
            else:
                deduplicated[x.url] = x.merge(deduplicated[x.url])

        self.entries = list(deduplicated.values())
