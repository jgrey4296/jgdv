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

from dejavu.files.org.base import OrgBuilderBase

@dataclass
class OrgDrawerBuilder(OrgBuilderBase):
    """
    A lazily build org drawer container,
    which aligns values in the block
    """

    owner               : OrgBuilderBase = field(default=None)
    name                : str           = field(default="")

    _contents     : List[Tuple[str, str]] = field(default_factory=list)
    _prop_pattern : str                   = ":{}:"
    _end          : str                   = ":END:"
    _max_key      : int                   = 0

    def add(self, *args):
        for name, contents in zip(args[::2], args[1::2]):
            self._contents.append((name, contents))
            self._max_key = max(len(name), self._max_key)

    def add_keyless(self, *args):
        for arg in args:
            self._contents.append(("", arg))

    def add_file_links(self, *args):
        as_links = [OrgDrawerBuilder.named_file_pattern.format(x, pl.Path(x).name) for x in args]
        self.add_keyless(*as_links)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return None

    def __str__(self):
        """
        Write the drawer, while padding appropriately
        """
        output = []
        output.append(f":{self.name.upper()}:")
        for key, val in self._contents:
            if bool(key):
                key_f   = self._prop_pattern.format(key)
                pad_amt = 5 + max(0, (2 + self._max_key) - len(key_f))
                output.append(f"{key_f}{pad_amt*' '}{val}")
            else:
                output.append(val)

        output.append(self._end)
        output.append("")
        return "\n".join(map(str, output))
