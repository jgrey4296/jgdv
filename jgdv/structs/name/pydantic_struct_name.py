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
from pydantic import BaseModel, Field, field_validator, model_validator
from tomlguard import TomlGuard

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv._abstract.protocols import Buildable_p, Nameable_p, ProtocolModelMeta

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv.structs.name import mixins
PAD           : Final[int] = 15
TailEntry                  = mixins.TailEntry

class StructuredName(mixins.StrStruct_m, BaseModel, Nameable_p, Buildable_p,  metaclass=ProtocolModelMeta):
    """ A Complex name class for identifying tasks and classes.

      Classes are the standard form used in importlib: "module.path:ClassName"
      Tasks use a double colon to separate head from tail name: "group.name::TaskName"

    """
    base             : str
    head             : list[str]              = []
    tail             : list[TailEntry]        = []

    _separator       : ClassVar[str]          = ":"
    _subseparator    : ClassVar[str]          = "."

    @classmethod
    def build(cls, val:str) -> StructuredName:
        return cls(base=val)

    @model_validator(mode="before")
    def _validate_structure (cls, data:dict) -> dict:
        cls._pre_validate(data)
        return data

    @model_validator(mode="after")
    def _extract_metadata(self):
        head, tail, params = self._process()
        self.head += head
        self.tail += tail
