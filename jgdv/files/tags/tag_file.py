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
import types
import weakref
from collections import defaultdict
from uuid import UUID, uuid1

# ##-- end stdlib imports

from . import _interface as API  # noqa: N812
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
from jgdv import Rx  # noqa: TC001

if TYPE_CHECKING:
    import pathlib as pl
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

class TagFile(BaseModel):
    """ A Basic TagFile holds the counts for each tag use

    Tag file format is single lines of:
    ^{tag} {sep} {count}$

    cls.read can be used to change the {sep}

    # TODO use a collections.Counter
    """

    counts       : dict[str, int]        = defaultdict(lambda: 0)
    sep          : str                   = API.SEP
    ext          : str                   = API.EXT
    norm_replace : str                   = API.NORM_REPLACE
    norm_regex   : Rx                    = API.TAG_NORM
    comment      : str                   = API.COMMENT

    @classmethod
    def read(cls, fpath:pl.Path, **kwargs:dict) -> TagFile:
        obj = cls(**{x:y for x,y in kwargs.items() if y is not None})
        for i, line in enumerate(fpath.read_text().split("\n")):
            try:
                obj.update(line)
            except Exception as err:
                logging.warning("Failure Tag Read: (l:%s) : %s : %s : (file: %s)", i, err, line, fpath)
                raise

        return obj

    @field_validator("norm_regex", mode="before")
    def _validate_regex(cls, val:str|Rx) -> Rx:  # noqa: N805
        match val:
            case str():
                return re.compile(val)
            case re.Pattern():
                return val
            case _:
                msg = "Bad norm_regex provided"
                raise TypeError(msg)

    @field_validator("counts", mode="before")
    def _validate_counts(cls, val:dict) -> dict:  # noqa: N805
        counts = defaultdict(lambda: 0)
        match val:
            case dict():
                counts.update(val)
            case x:
                raise TypeError(type(x))
        return counts

    @model_validator(mode="after")
    def _normalize_counts(self) -> Self:
        orig = self.counts
        self.counts = defaultdict(lambda: 0)
        self.counts.update({self.norm_tag(x):y for x,y in orig.items()})
        return self

    def __iter__(self) -> Iterator:
        return iter(self.counts)

    def __str__(self) -> str:
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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {len(self)}>"

    def __iadd__(self, values:TagFile|str|dict|set) -> Self:
        """  merge tags, updating their counts as well. """
        return self.update(values)

    def __len__(self) -> int:
        return len(self.counts)

    def __contains__(self, value:str) -> bool:
        return self.norm_tag(value) in self.counts

    def _inc(self, key:str, *, amnt:int=1) -> Maybe[str]:
        norm_key = self.norm_tag(key)
        if not bool(norm_key):
            return None
        self.counts[norm_key] += amnt
        return norm_key

    def update(self, *values:str|TagFile|set|dict) -> Self:
        for val in values:
            match val:
                case None | "":
                    continue
                case str() if val.startswith(self.comment):
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

    def get_count(self, tag:str) -> int:
        return self.counts[self.norm_tag(tag)]

    def norm_tag(self, tag:str) -> str:
        stripped = tag.strip()
        return self.norm_regex.sub(self.norm_replace, stripped).strip()
