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

TAG_NORM : Final[re.Pattern] = re.compile(" +")

@dataclass
class Bookmark:
    url     : str      = field()
    tags    : Set[str] = field(default_factory=set)
    name    : str      = field(default="No Name")
    sep     : str      = field(default=" : ")

    @staticmethod
    def build(line:str, sep=None):
        """
        Build a bookmark from a line of a bookmark file
        """
        sep  = sep or Bookmark.sep
        tags = []
        match [x.strip() for x in line.split(sep)]:
            case []:
                raise TypeException("Bad line passed to Bookmark")
            case [url]:
                logging.warning("No Tags for: %s", url)
            case [url, *tags]:
                pass

        return Bookmark(url,
                        set(tags),
                        sep=sep)

    def __post_init__(self):
        self.tags = {TAG_NORM.sub("_", x.strip()) for x in self.tags}

    def __eq__(self, other):
        return self.url == other.url

    def __lt__(self, other):
        return self.url < other.url

    def __str__(self):
        tags = self.sep.join(sorted(self.tags))
        return f"{self.url}{self.sep}{tags}"

    @property
    def url_comps(self) -> url_parse.ParseResult:
        return url_parse.urlparse(self.url)

    def merge(self, other) -> 'Bookmark':
        """ Merge two bookmarks' tags together,
        creating a new bookmark
        """
        assert(self == other)
        merged = Bookmark(self.url,
                          self.tags.union(other.tags),
                          self.name,
                          sep=self.sep)
        return merged

    def clean(self, subs):
        """
        run tag substitutions on all tags in the bookmark
        """
        cleaned_tags = set()
        for tag in self.tags:
            cleaned_tags.add(subs.sub(tag))

        self.tags = cleaned_tags
