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
class TagFile:
    """ A Basic TagFile holds the counts for each tag use """

    counts : dict[str, int] = field(default_factory=lambda: defaultdict(lambda: 0))
    sep    : str            = field(default=" : ")
    ext    : str            = field(default=".tags")

    norm_regex : re.Pattern  = TAG_NORM

    @classmethod
    def read(cls, fpath:pl.Path, sep=None) -> TagFile:
        obj = cls(sep=sep or cls.sep)
        for i, line in enumerate(fpath.read_text().split("\n")):
            try:
                obj.update(tuple(x.strip() for x in line.split(obj.sep)))
            except Exception as err:
                logging.warning("Failure Tag Reading %s (l:%s) : %s : %s", fpath, i, err, line)

        return obj

    def __iter__(self):
        return iter(self.counts)

    def __str__(self):
        """
        Export the counts, 1 entry per line, as:
        `key` : `value`
        """
        all_lines = []
        for key in sorted(self.counts.keys(), key=lambda x: x.lower()):
            if not bool(self.counts[key]):
                continue
            all_lines.append(self.sep.join([key, str(self.counts[key])]))
        return "\n".join(all_lines)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {len(self)}>"

    def __iadd__(self, values):
        return self.update(values)

    def __len__(self):
        return len(self.counts)

    def __contains__(self, value):
        return self.norm_tag(value) in self.counts

    def _inc(self, key, *, amnt=1):
        norm_key = self.norm_tag(key)
        self.counts[norm_key] += amnt
        return norm_key

    def update(self, *values):
        for val in values:
            match val:
                case None | "":
                    continue
                case str():
                    self._inc(val)
                case [str() as key]:
                    self._inc(key)
                case (str() as key, str() as counts):
                    self._inc(key, amnt=int(counts))
                case TagFile():
                    self.update(*values.counts.items())
                case set():
                    self.update(*val)
        return self

    def to_set(self) -> Set[str]:
        return set(self.counts.keys())

    def get_count(self, tag):
        return self.counts[self.norm_tag(tag)]

    def norm_tag(self, tag):
        return self.norm_regex.sub("_", tag.strip())
