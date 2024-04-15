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
class SubstitutionFile(TagFile):
    """ SubstitutionFiles add a replacement tag for some tags """

    ext           : str                  = field(default=".sub")
    substitutions : Dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    def __str__(self):
        """
        Export the substitutions, 1 entry per line, as:
        `key` : `counts` : `substitution`
        """
        all_lines = []
        for key in sorted(self.counts.keys()):
            if not bool(self.substitutions[key]):
                continue
            line = [key, str(self.counts[key])]
            line += sorted(self.substitutions[key])
            all_lines.append(self.sep.join(line))

        return "\n".join(all_lines)

    def sub(self, value:str) -> set[str]:
        """ apply a substitution if it exists """
        normed = self.norm_tag(value)
        if normed in self.substitutions:
            return self.substitutions[normed]

        return set([normed])

    def has_sub(self, value):
        return value in self.substitutions

    def update(self, *values):
        for val in values:
            match val:
                case None | "":
                    continue
                case str():
                    self._inc(val)
                case (str() as key, str() as counts):
                    self._inc(key, amnt=int(counts))
                case (str() as key, str() as counts, *subs):
                    norm_key  = self._inc(key, amnt=int(counts))
                    norm_subs = [ self.norm_tag(x) for x in subs]
                    self.substitutions[norm_key].update([x for x in norm_subs if bool(x)])
                case dict():
                    for key, val in val.items():
                        self._inc(key, amnt=val)
                case SubstitutionFile():
                    self.update(val.counts)
                    for tag, subs in val.substitutions.items():
                        self.substitutions[tag].update(subs)
                case TagFile():
                    self.update(val.counts.items())

        return self
