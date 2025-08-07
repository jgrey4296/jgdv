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
import re
import time
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv.files.bookmarks.bookmark import Bookmark

# ##-- end 1st party imports

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
# isort: on
# ##-- end types

# ##-- type checking
# isort: off
if typing.TYPE_CHECKING:
    import pathlib as pl
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe
## isort: on
# ##-- end type checking


##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class BookmarkCollection(BaseModel):
    """A container of bookmarks,
    read from a file where each line is a bookmark url with tags.
    """

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

    @override
    def __str__(self) -> str:
        return "\n".join(map(str, sorted(self.entries)))

    @override
    def __repr__(self) -> str :
        return f"<{self.__class__.__name__}: {len(self)}>"

    def __iadd__(self, value:Bookmark) -> Self:
        return self.update(value)

    @override
    def __iter__(self) -> Iterator[Bookmark]: # type: ignore[override]
        return iter(self.entries)

    def __contains__(self, value:Bookmark) -> bool:
        return value in self.entries

    def __len__(self) -> int:
        return len(self.entries)

    @override
    def __hash__(self) -> int:
        return id(self)

    def update(self, *values:Bookmark|BookmarkCollection|Iterable) -> Self:
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

    def difference(self, other:Self) -> BookmarkCollection:
        result = BookmarkCollection()
        for bkmk in other:
            if bkmk not in self:
                result += bkmk

        return result

    def merge_duplicates(self) -> None:
        deduplicated = {}
        for x in self:
            if x.url not in deduplicated:
                deduplicated[x.url] = x
            else:
                deduplicated[x.url] = x.merge(deduplicated[x.url])

        self.entries = list(deduplicated.values())
