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
import importlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
# from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from tomlguard import TomlGuard

# ##-- end 3rd party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv.structs.name import mixins

TailEntry      : TypeAlias                 = mixins.TailEntry
FMT_PATTERN    : Final[re.Pattern]         = re.compile("^(h?)(t?)(p?)")
SEP_DEFAULT    : Final[str]                = ":"
SUBSEP_DEFAULT : Final[str]                = "."

class _StructuredNameBase(mixins.StrStruct_m, str):
    """
      A Structured String Baseclass.
      A Normal str, but is parsed on construction to extract and validate
      certain form and metadata.
    """

    _separator       : ClassVar[str] = SEP_DEFAULT
    _subseparator    : ClassVar[str] = SUBSEP_DEFAULT

    @staticmethod
    def build(val:str) -> Self:
        return StructuredName(val)

    def __new__(cls, *args, **kwargs):
        """ Overrides normal str creation to allow passing args to init """
        result = str.__new__(cls, args[0])
        result.__init__(*args, **kwargs)
        return result

    def __init__(self, data, *, meta=None):
        super().__init__()
        self.metadata = {}
        if meta:
            self.metadata.update(meta)
        self._pre_validate({"base":self})
        head, tail, params = self._process()
        self.head = head
        self.tail = tail



    @property
    def base(self):
        return self

class StructuredName(_StructuredNameBase):

    def __format__(self, spec) -> str:
        """ format additions for structured strings:
          {:h} = print only the head_str
          {:t} = print only the tail_str
          {:p} = print only the params_str

          """
        relevant   = FMT_PATTERN.search(spec)
        remaining  = FMT_PATTERN.sub("", spec)
        result     = []
        if bool(relevant[1]):
            result.append(self.head_str())
        if bool(relevant[2]):
            result.append(self.tail_str())
        if bool(relevant[3]) and bool(self.params):
            result.append(str(self.params))

        return format(self._sep.join(result), remaining)

