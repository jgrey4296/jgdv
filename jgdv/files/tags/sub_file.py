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
import pathlib as pl
import re
import time
import types
import weakref
from collections import defaultdict
from uuid import UUID, uuid1

# ##-- end stdlib imports

from . import _interface as API # noqa: N812
from .tag_file import TagFile

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


class SubstitutionFile(TagFile):
    """ SubstitutionFiles add a replacement tag for some tags

    Substitution file format is single lines of:
    ^{tag} {sep} {count} [{sep} {replacement}]*$

    """

    sep           : str                  = API.SEP
    ext           : str                  = API.SUB_EXT
    substitutions : dict[str, set[str]]  = defaultdict(set)  # noqa: RUF012

    def __str__(self) -> str:
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

    def __getitem__(self, key:str) -> set[str]:
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

        return {normed}

    def sub_many(self, *values:str) -> set[str]:
        result = set()
        for val in values:
            result.update(self.sub(val))
        else:
            return result

    def has_sub(self, value:str) -> bool:
        normed = self.norm_tag(value)
        if normed != value:
            return True
        return bool(self.substitutions.get(normed, None))

    def update(self, *values:str|tuple|dict|SubstitutionFile|TagFile|set) -> Self:
        """
        Overrides TagFile.update to handle tuples of (tag, count, replacements*)
        and (tag, replacements*)
        """
        for val in values:
            match val:
                case None | "": # empty line
                    continue
                case str() if val.startswith(self.comment): # comment
                    continue
                case str() if API.ALT_SEP in val: # key :: subs
                    x, *ys = val.split(API.ALT_SEP)
                    self._add_sub(x, list(ys))
                case str() if self.sep in val: # key : count : subs
                    self.update(tuple(x.strip() for x in val.split(self.sep)))
                case str(): # key
                    self._inc(val)
                case list() | set(): # keys
                    for key in val:
                        self._inc(key)
                case dict(): # { key : count }
                    for key, v in val.items():
                        self._inc(key, amnt=v)
                case (str() as key, int() | str() as counts): # (key, count)
                    self._inc(key, amnt=int(counts))
                case (str() as key, list() as subs): # (key, subs)
                    self._add_sub(key, subs)
                case (str() as key, int() | str() as counts, *subs): # key, count, subs
                    self._add_sub(key, list(subs), count=counts)
                case SubstitutionFile():
                    self.update(val.counts)
                    for tag, subs in val.substitutions.items():
                        self._add_sub(tag, subs)
                case TagFile():
                    self.update(val.counts.items())

        return self

    def _add_sub(self, key:str, subs:list[str], *, count:str|int=1) -> None:
        match subs:
            case [str() as x] if self.sep in x:
                subs = x.split(self.sep)
            case _:
                pass
        try:
            count = int(count)
        except ValueError:
            count = 1

        norm_key  = self._inc(key, amnt=count)
        norm_subs = [normed for x in subs if (normed:=self.norm_tag(x)) is not None]
        self.update({x:1 for x in norm_subs}) # Add to normal counts too
        self.substitutions[norm_key].update(norm_subs)
