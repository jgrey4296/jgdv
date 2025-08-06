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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv.files.bookmarks.bookmark import Bookmark

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class BookmarkCollection(BaseModel):

    entries : list[Bookmark] = []
    ext     : str            = ".bookmarks"

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

    def __contains__(self, value:Bookmark) -> bool:
        return value in self.entries

    def __len__(self):
        return len(self.entries)

    def __hash__(self):
        return id(self)

    def update(self, *values) -> Self:
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

    def difference(self, other:Self) -> Self:
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
