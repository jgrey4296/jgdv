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
class Leaf:

    data : List[Any] = field(default_factory=list)

    __repr__ = __str__

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return "Leaf Group({})".format(len(self))

    def get_tuple_list(self):
        return [x.to_tuple() for x in self.data]

    def insert(self, name, url, tags, query_dict, full_path):
        new_leaf = LeafComponent(name, url, tags, full_path, query_dict)
        if new_leaf in self.data:
            logging.info("Merging tags")
            existing = self.data.index(new_leaf)
            existing.tags.update(tags)
            return existing
        else:
            self.data.append(new_leaf)
            return new_leaf

    def filter_queries(self, query_set):
        for x in self.data:
            x.filter_queries(query_set)

@dataclass
class LeafComponent:

    name      : str            = field()
    url       : str            = field()
    tags      : List[str]      = field()
    full_path : str            = field()
    query     : Dict[Any, Any] = field(default_factory=dict)

    __repr__ = __str__

    def __eq__(self, other):
        if not isinstance(other, LeafComponent):
            return False
        if self.full_path != other.full_path:
            return False
        return True

    def __str__(self):
        return "Leaf({})".format(self.full_path)

    def filter_queries(self, query_set):
        for k in list(self.query.keys()):
            if k in query_set:
                del self.query[k]

    def reconstruct(self, key=None):
        copied = {}
        copied.update(self.query)
        if key in copied:
            del copied[key]
        query_str = urlencode(copied, True)
        full_path = urlunparse((self.url.scheme,
                                self.url.netloc,
                                self.url.path,
                                self.url.params,
                                query_str,
                                self.url.fragment))
        return full_path

    def to_tuple(self):
        return Bookmark(self.reconstruct(),
                        self.tags,
                        name=self.name)
