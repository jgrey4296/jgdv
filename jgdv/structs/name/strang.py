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

from jgdv.structs.name import strang_mixins as mixins

FMT_PATTERN    : Final[re.Pattern]         = re.compile("^(h?)(t?)(p?)")
SEP_DEFAULT    : Final[str]                = ":"
SUBSEP_DEFAULT : Final[str]                = "."

STRGET = str.__getitem__

class Strang(mixins.Strang_m, str):
    """
      A Structured String Baseclass.
      A Normal str, but is parsed on construction to extract and validate
      certain form and metadata.
    """

    _separator       : ClassVar[str] = SEP_DEFAULT
    _subseparator    : ClassVar[str] = SUBSEP_DEFAULT

    @staticmethod
    def build(val:str) -> Self:
        return Strang(val)

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
        group, body, params = self._process()
        self._group : list[slice] = group
        self._body  : list[slice] = body

    def __iter__(self):
        for x in self.group + self.body:
            yield x

    def __getitem__(self, i):
        match i:
            case slice(start=0, stop=x):
                return super().__getitem__(self._group[x])
            case slice(start=1, stop=x):
                return super().__getitem__(self._body[x])

    @property
    def base(self):
        return self

    @property
    def group(self) -> list[str]:
        return [STRGET(self, x) for x in self._group]

    @property
    def body(self) -> iter[str]:
        return [STRGET(self, x) for x in self._body]

    @property
    def sgroup(self) -> str:
        return STRGET(self, slice(self._group[0].start, self._group[-1].stop))

    @property
    def sbody(self) -> str:
        return STRGET(self, slice(self._body[0].start, self._body[-1].stop))

    def __format__(self, spec) -> str:
        """ format additions for structured strings:
          {:h} = print only the group_str
          {:t} = print only the body_str
          {:p} = print only the params_str

          """
        relevant   = FMT_PATTERN.search(spec)
        remaining  = FMT_PATTERN.sub("", spec)
        result     = []
        if bool(relevant[1]):
            result.append(self.group_str())
        if bool(relevant[2]):
            result.append(self.body_str())
        if bool(relevant[3]) and bool(self.params):
            result.append(str(self.params))

        return format(self._sep.join(result), remaining)
