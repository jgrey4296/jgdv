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
TailEntry     : TypeAlias  = str|int|UUID

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

    # def _process_head(cls, head):
    #     sub_split = ftz.partial(aware_splitter, sep=cls._subseparator)
    #     match head:
    #         case None | []:
    #             head = ["default"]
    #         case ["tasks", x] if x.startswith('"') and x.endswith('"'):
    #             head = ftz.reduce(lambda x, y: x + y, map(sub_split, x[1:-1]))
    #         case ["tasks", *xs]:
    #             head = ftz.reduce(lambda x, y: x + y, map(sub_split, xs))
    #         case list():
    #             head = ftz.reduce(lambda x, y: x + y, map(sub_split, head))
    #         case _:
    #             raise ValueError("Bad Head Value", head)

    #     return head

    # def _process_tail(cls, tail):
    #     sub_split = ftz.partial(aware_splitter, sep=cls._subseparator)
    #     match tail:
    #         case None | []:
    #             tail = ["default"]
    #         case list():
    #             tail = ftz.reduce(lambda x, y: x + y, map(sub_split, tail))
    #         case _:
    #             raise ValueError("Bad Tail Value", tail)
    #     return tail
