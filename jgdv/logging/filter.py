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

class JGDVAnyFilter:
    """
      A Logging filter to white and blacklist regexs of logger names
    """

    def __init__(self, names=None, reject=None):
        self.names      = names or []
        self.rejections = reject or []
        self.name_re    = re.compile("^({})".format("|".join(self.names)))

    def __call__(self, record) -> bool:
        return (record.name not in self.rejections) and (record.name == "root"
                                                         or not bool(self.names)
                                                         or self.name_re.match(record.name))
