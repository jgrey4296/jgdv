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
import urllib
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

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
# from dataclasses import InitVar, dataclass, field
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
    from jgdv import Maybe, Rx
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    type UrlParseResult = urllib.parse.ParseResult

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class Bookmark(BaseModel):
    url              : str
    tags             : set[str]              = set()
    name             : str                   = "No Name"
    _tag_sep         : ClassVar[str]         = " : "
    _tag_norm_re     : ClassVar[Rx]          = re.compile(" +")

    @staticmethod
    def build(line:str, sep=None):
        """
        Build a bookmark from a line of a bookmark file
        """
        sep  = sep or Bookmark._tag_sep
        tags = []
        match [x.strip() for x in line.split(sep)]:
            case []:
                raise TypeError("Bad line passed to Bookmark")
            case [url]:
                logging.warning("No Tags for: %s", url)
            case [url, *tags]:
                pass

        return Bookmark(url=url,
                        tags=set(tags),
                        sep=sep)

    @field_validator("tags", mode="before")
    def _validate_tags(cls, val):
        match val:
            case list()|set():
                return { Bookmark._tag_norm_re.sub("_", x.strip()) for x in val }
            case str():
                return { Bookmark._tag_norm_re.sub("_", x.strip()) for x in val.split(Bookmark._tag_sep) }
            case _:
                raise ValueError("Unrecognized tags base", val)

    def __eq__(self, other):
        return self.url == other.url

    def __lt__(self, other):
        return self.url < other.url

    def __str__(self):
        sep = Bookmark._tag_sep
        tags = sep.join(sorted(self.tags))
        return f"{self.url}{sep}{tags}"

    @property
    def url_comps(self) -> UrlParseResult:
        return urllib.parse.urlparse(self.url)

    def merge(self, other) -> Self:
        """ Merge two bookmarks' tags together,
        creating a new bookmark
        """
        assert(self == other)
        merged = Bookmark(url=self.url,
                          tags=self.tags.union(other.tags),
                          name=self.name)
        return merged

    def clean(self, subs):
        """
        run tag substitutions on all tags in the bookmark
        """
        cleaned_tags = set()
        for tag in self.tags:
            cleaned_tags.add(subs.sub(tag))

        self.tags = cleaned_tags
