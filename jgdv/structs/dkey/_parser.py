#!/usr/bin/env python3
"""

"""
# ruff: noqa:

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
from string import Formatter
# ##-- end stdlib imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
# from dataclasses import InitVar, dataclass, field
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
from jgdv import Maybe

if TYPE_CHECKING:
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
INDIRECT_SUFFIX : Final[Ident]                = "_"
# Body:

class RawKey(BaseModel):
    """ Utility class for parsed string parameters

    Provides the data from string.Formatter.parse, but in a structure
    instead of a tuple
    """

    prefix : Maybe[str] = ""
    key    : Maybe[str] = ""
    format : Maybe[str] = ""
    conv   : Maybe[str] = ""

    def __getitem__(self, i):
        match i:
            case 0:
                return self.prefix
            case 1:
                return self.key
            case 2:
                return self.format
            case 3:
                return self.conv
            case _:
                raise ValueError("Tried to access a bad element of DKeyParams", i)

    def __bool__(self):
        return bool(self.key)

    def joined(self):
        args = [self.key]
        if bool(self.format):
            args += [":", self.format]
        if bool(self.conv):
            args += ["!", self.conv]

        return "".join(args)

    def wrapped(self) -> str:
        return "{%s}" % self.key

    def direct(self) -> str:
        return self.key.removesuffix(INDIRECT_SUFFIX)

    def indirect(self) -> str:
        if self.key.endswith(INDIRECT_SUFFIX):
            return self.key

        return f"{self.key}{INDIRECT_SUFFIX}"

    def is_indirect(self) -> bool:
        return self.key.endswith(INDIRECT_SUFFIX)

    def anon(self) -> list[str]:
        return [self.prefix, "{}"]

class DKeyParser(Formatter):
    """ parser for extracting {keys:params} from strings, """

    def parse(self, *args, implicit=False, **kwargs) -> Iterator[RawKey]:
        if implicit and "{" in args[0]:
            breakpoint()
            pass
            raise ValueError("Implicit key already has braces", args[0])

        if implicit:
            args = [
                "".join(["{", args[0], "}"]),
                *args[1:]
            ]

        for x in super().parse(*args, **kwargs):
            yield self.make_param(*x)

    def make_param(self, *args):
        return RawKey(prefix=args[0],
                                      key=args[1] or "",
                                      format=args[2] or "",
                                      conv=args[3] or "")
