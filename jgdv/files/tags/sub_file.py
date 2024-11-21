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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from collections import defaultdict
from .tag_file import TagFile, SEP

EXT = ".sub"

class SubstitutionFile(TagFile):
    """ SubstitutionFiles add a replacement tag for some tags

    Substitution file format is single lines of:
    ^{tag} {sep} {count} [{sep} {replacement}]*$

    """

    sep           : str                  = SEP
    ext           : str                  = EXT
    substitutions : dict[str, set[str]]  = defaultdict(set)

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

    def __getitem__(self, key) -> set[str]:
        """ Gets the substitutions for a key """
        return self.sub(key)

    def canonical(self) -> TagFile:
        """ create a tagfile of just canonical tags"""
        # All substitutes are canonical
        canon = {x:1 for x in iter(self) if not self.has_sub(x)}
        return TagFile(counts=canon)

    def known(self) -> TagFile:
        """ Get a TagFile of all known tags. both canonical and not """
        canon = self.canonical()
        canon += self
        return canon

    def sub(self, value:str) -> set[str]:
        """ apply a substitution if it exists """
        normed = self.norm_tag(value)
        if bool(self.substitutions.get(normed, None)):
            return self.substitutions[normed]

        return set([normed])

    def sub_many(self, *values:str) -> set[str]:
        result = set()
        for val in values:
            result.update(self.sub(val))

        return result

    def has_sub(self, value):
        normed = self.norm_tag(value)
        if normed != value:
            return True
        return bool(self.substitutions.get(normed, None))

    def update(self, *values:str|Tuple|dict|SubstitutionFile|TagFile|set):
        """
        Overrides TagFile.update to handle tuples of (tag, count, replacements*)
        """
        for val in values:
            match val:
                case None | "": # empty line
                    continue
                case str() if val.startswith(self.comment):
                    continue
                case str() if self.sep in val:
                    self.update(tuple(x.strip() for x in val.split(self.sep)))
                case str(): # just a tag
                    self._inc(val)
                case list() | set():
                    for key in val:
                        self._inc(key)
                case dict(): # tag and count
                    for key, val in val.items():
                        self._inc(key, amnt=val)
                case (str() as key, int() | str() as counts): # tag and count
                    self._inc(key, amnt=int(counts))
                case (str() as key, int() | str() as counts, *subs): # Tag, count, subs
                    norm_key  = self._inc(key, amnt=int(counts))
                    norm_subs = [normed for x in subs if (normed:=self.norm_tag(x)) is not None]
                    self.update({x:1 for x in norm_subs}) # Add to normal counts too
                    self.substitutions[norm_key].update(norm_subs)
                case SubstitutionFile():
                    self.update(val.counts)
                    for tag, subs in val.substitutions.items():
                        self.substitutions[tag].update(subs)
                case TagFile():
                    self.update(val.counts.items())

        return self
