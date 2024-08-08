#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

from __future__ import annotations

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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

HOME = str(pl.Path.home())

class DPath(pl.Path):
    """ Simple py312 Path subclass,
      which auto-expands '~' on creation
      """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create an expanded version, and copy over results
        exp = self.expanduser()
        self._drv = exp._drv
        self._root = exp._root
        self._tail_cached = exp._tail_cached
        self._raw_paths = exp._raw_paths
        self._rooted_at_home = self._raw_paths[0].startswith(HOME)

    def __str__(self):
        if not self._rooted_at_home:
            return super().__str__()
        else:
            temp = super().__str__()
            temp.removeprefix(HOME)
            return "".join(["~", temp])
