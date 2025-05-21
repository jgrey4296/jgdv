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

from .. import _interface as API # noqa: N812

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

# Body:

class DKeyParser:
    """ Parser for extracting {}-format params from strings.

    ::

        see: https://peps.python.org/pep-3101/
        and: https://docs.python.org/3/library/string.html#format-string-syntax
    """

    def parse(self, format_string, *, implicit=False) -> Iterator[API.RawKey_d]:
        if implicit and "{" in format_string:
            raise ValueError("Implicit key already has braces", format_string)

        if implicit:
            format_string = "".join(["{", format_string, "}"])

        try:
            for x in _string.formatter_parser(format_string):
                yield self.make_param(*x)
        except ValueError as err:
            yield self.make_param(format_string, "","","")

    def make_param(self, *args):
        return API.RawKey_d(prefix=args[0],
                            key=args[1] or "",
                            format=args[2] or "",
                            conv=args[3] or "")
