#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import builtins
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
import typing
import weakref
from dataclasses import InitVar, dataclass, field
from types import GenericAlias
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
    Self,
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

# ##-- 3rd party imports
from pydantic import BaseModel, Field, InstanceOf, field_validator, model_validator

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv._abstract.protocols import Buildable_p, ParamStruct_p, ProtocolModelMeta
from jgdv.mixins.annotate import SubAnnotate_m
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from jgdv.cli.errors import ArgParseError
from ._base import ParamSpecBase
from . import core
from . import assignment
from . import defaults
from . import positional

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

NON_ASSIGN_PREFIX : Final[str] = "-"
ASSIGN_PREFIX     : Final[str] = "--"
END_SEP           : Final[str] = "--"

class ParamSpec(ParamSpecBase):
    """ A Top Level Access point for building param specs """

    @classmethod
    def build(cls:BaseModel, data:dict) -> ParamSpecBase:
        match data:
            case {"implicit":True}:
                return core.ImplicitParam.model_validate(data)
            case {"prefix":int()|None|""}:
                return positional.PositionalParam.model_validate(data)
            case {"prefix":x, "type":y} if x == ASSIGN_PREFIX and y in [bool, "bool"]:
                return core.ToggleParam.model_validate(data)
            case {"prefix":x} if x == ASSIGN_PREFIX:
                return assignment.AssignParam.model_validate(data)
            case {"type":"list"|"set"}:
                return core.RepeatableParam.model_validate(data)
            case {"type":"bool"}:
                return core.ToggleParam.model_validate(data)
            case _:
                return core.KeyParam.model_validate(data)
