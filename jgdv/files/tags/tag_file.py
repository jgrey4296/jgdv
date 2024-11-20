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
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

from collections import defaultdict
from pydantic import BaseModel, field_validator, model_validator

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

TAG_NORM     : Final[re.Pattern] = re.compile(" +")
SEP          : Final[str]        = " : "
EXT          : Final[str]        = ".tags"
NORM_REPLACE : Final[str]        = "_"

class TagFile(BaseModel):
    """ A Basic TagFile holds the counts for each tag use

    Tag file format is single lines of:
    ^{tag} {sep} {count}$

    cls.read can be used to change the {sep}
    """

    counts       : dict[str, int]        = defaultdict(lambda: 0)
    sep          : str                   = SEP
    ext          : str                   = EXT
    norm_replace : str                   = NORM_REPLACE
    norm_regex   : re.Pattern            = TAG_NORM

    @classmethod
    def read(cls, fpath:pl.Path, **kwargs) -> TagFile:
        obj = cls(**kwargs)
        for i, line in enumerate(fpath.read_text().split("\n")):
            try:
                obj.update(line)
            except Exception as err:
                logging.warning("Failure Tag Read: (l:%s) : %s : %s : (file: %s)", i, err, line, fpath)

        return obj

    @field_validator("norm_regex", mode="before")
    def _validate_regex(cls, val):
        match val:
            case str():
                return re.compile(val)
            case re.Pattern():
                return val
            case _:
                raise TypeError("Bad norm_regex provided")

    @field_validator("counts", mode="before")
    def _validate_counts(cls, val):
        counts = defaultdict(lambda: 0)
        match val:
            case dict():
                counts.update(val)
        return counts

    @model_validator(mode="after")
    def _normalize_counts(self):
        orig = self.counts
        self.counts = defaultdict(lambda: 0)
        self.counts.update({self.norm_tag(x):y for x,y in orig.items()})
        return self

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

    def __iadd__(self, values:TagFile|str|dict|set):
        """  merge tags, updating their counts as well. """
        return self.update(values)

    def __len__(self):
        return len(self.counts)

    def __contains__(self, value):
        return self.norm_tag(value) in self.counts

    def _inc(self, key, *, amnt=1) -> None|str:
        norm_key = self.norm_tag(key)
        if not bool(norm_key):
            return None
        self.counts[norm_key] += amnt
        return norm_key

    def update(self, *values:str|TagFile|set|dict):
        for val in values:
            match val:
                case None | "":
                    continue
                case str() if self.sep in val:
                    self.update(tuple(x.strip() for x in val.split(self.sep)))
                case str():
                    self._inc(val)
                case list() | set():
                    self.update(*val)
                case dict():
                    self.update(*val.items())
                case (str() as key, int()|str() as counts):
                    self._inc(key, amnt=int(counts))
                case TagFile():
                    self.update(*val.counts.items())
        return self

    def to_set(self) -> set[str]:
        return set(self.counts.keys())

    def get_count(self, tag):
        return self.counts[self.norm_tag(tag)]

    def norm_tag(self, tag):
        return self.norm_regex.sub(self.norm_replace, tag).strip()
