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
import _string
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
    from jgdv import Ident
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
    """ Utility class for parsed {}-format string parameters.
    see: https://peps.python.org/pep-3101/
    and: https://docs.python.org/3/library/string.html#format-string-syntax

    Provides the data from string.Formatter.parse, but in a structure
    instead of a tuple.
    """

    prefix : Maybe[str] = ""
    key    : Maybe[str] = None
    format : Maybe[str] = None
    conv   : Maybe[str] = None

    @field_validator("format")
    def _validate_format(cls, val:str) -> str:
        """ Ensure the format params are valid """
        return val

    @field_validator("conv")
    def _validate_conv(cls, val):
        """ Ensure the conv params are valid """
        return val

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

    def joined(self) -> str:
        """ return the key and params as one string
        eg: blah, fmt=5, conv=p -> blah:5!p

        """
        if not bool(self.key):
            return ""

        args = [self.key]
        if bool(self.format):
            args += [":", self.format]
        if bool(self.conv):
            args += ["!", self.conv]

        return "".join(args)

    def wrapped(self) -> str:
        """ return this key in simple wrapped form
        (it ignores format, conv params and prefix)
        eg: blah -> {blah}
        """
        return "{%s}" % self.key

    def anon(self) -> str:
        """ Make a format str of this key, with anon variables.
        eg: blah {key:f!p} -> blah {}
        """
        if bool(self.key):
            return "%s{}" % self.prefix

        return self.prefix

    def direct(self) -> str:
        """ return this key in direct form
        eg: blah -> blah
        ... blah_ -> blah
        """
        return self.key.removesuffix(INDIRECT_SUFFIX)

    def indirect(self) -> str:
        """ return this key in indirect form
        eg: blah -> blah_
        ... blah_ -> blah_
        """
        if self.key.endswith(INDIRECT_SUFFIX):
            return self.key

        return f"{self.key}{INDIRECT_SUFFIX}"

    def is_indirect(self) -> bool:
        return self.key.endswith(INDIRECT_SUFFIX)

class DKeyParser:
    """ Parser for extracting {}-format params from strings.
    see: https://peps.python.org/pep-3101/
    and: https://docs.python.org/3/library/string.html#format-string-syntax
    """

    def parse(self, format_string, *, implicit=False) -> Iterator[RawKey]:
        if implicit and "{" in format_string:
            raise ValueError("Implicit key already has braces", format_string)

        if implicit:
            format_string = "".join(["{", format_string, "}"])

        for x in _string.formatter_parser(format_string):
            yield self.make_param(*x)

    def make_param(self, *args):
        return RawKey(prefix=args[0],
                                      key=args[1] or "",
                                      format=args[2] or "",
                                      conv=args[3] or "")
