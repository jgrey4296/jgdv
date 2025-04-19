#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
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
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Maybe

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# True to process, False to reject

class BlacklistFilter:
    """
      A Logging filter to blacklist regexs of logger names
    """

    def __init__(self, blacklist:list[str]=None):
        self._blacklist   = blacklist or []
        self.blacklist_re  = re.compile("^({})".format("|".join(self._blacklist)))

    def __call__(self, record) -> bool:
        if record.name == "root":
            return True
        if not bool(self._blacklist):
            return True

        return not bool(self.blacklist_re.match(record.name))
