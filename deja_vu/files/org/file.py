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
from dejavu.files.org.drawer import OrgDrawerBuilder

@dataclass
class OrgStrBuilder(OrgBuilderBase):
    """
    Utility class for building Org files
    """
    output : List[Union[str, 'OrgBuilderBase']] = field(default_factory=list)

    prop_align_len      : int = 10
    heading_char        : str = "*"

    def heading(self, level, *text):
        stars = level * self.heading_char
        self.add(" ".join([stars, *text]))

    def link(self, text, uri):
        self.add(self.named_link_pattern.format(text, uri))
        self.nl

    def links(self, links):
        converted = [self.link_pattern.format(x) for x in links]
        self.add(*converted)

    def add(self, *text):
        self.output += text

    def drawer(self, name):
        drawer = OrgDrawerBuilder(self, name)
        self.add(drawer)
        return drawer

    @property
    def nl(self):
        self.output.append("")

    def __str__(self):
        return "\n".join(map(str, self.output))
