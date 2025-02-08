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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

NON_ASSIGN_PREFIX : Final[str] = "-"
ASSIGN_PREFIX     : Final[str] = "--"
END_SEP           : Final[str] = "--"

class AssignParam(ParamSpecBase):
    """ TODO a joined --key=val param """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("prefix", "--")
        super().__init__(*args, **kwargs)

    def next_value(self, args:list) -> tuple[str, list, int]:
        """ get the value for a --key=val """
        logging.debug("Getting Key Assignment: %s : %s", self.name, args)
        if self.separator not in args[0]:
            raise ArgParseError("Assignment param has no assignment", self.separator, args[0])
        key,val = self._split_assignment(args[0])
        return self.name, [val], 1

class WildcardParam(AssignParam):
    """ TODO a wildcard param that matches any --{key}={val} """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("type", str)
        kwargs['name'] = "*"
        super().__init__(**kwargs)

    def matches_head(self, val) -> bool:
        return (self.prefix == ASSIGN_PREFIX
                and val.startswith(self.prefix)
                and self.separator in val)

    def next_value(self, args:list) -> tuple[str, list, int]:
        logging.debug("Getting Wildcard Key Assingment: %s", args)
        assert(self.separator in args[0]), (self.separator, args[0])
        key,val = self._split_assignment(args[0])
        return key.removeprefix(self.prefix), [val], 1

