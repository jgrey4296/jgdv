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

if TYPE_CHECKING:
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, Ident
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
OBRACE : Final[str] = "{"
CBRACE : Final[str] = "}"
# Body:

class DKeyParser:
    """ Parser for extracting {}-format params from strings.

    ::

        see: https://peps.python.org/pep-3101/
        and: https://docs.python.org/3/library/string.html#format-string-syntax
    """

    def parse(self, format_string:str, *, implicit:bool=False) -> Generator[API.RawKey_d]:
        if implicit and OBRACE in format_string:
            msg = "Implicit key already has braces"
            raise ValueError(msg, format_string)

        if implicit: # Wrap implicit keys with braces, to extract format and conv parameters
            format_string = "".join([OBRACE, format_string, CBRACE])  # noqa: FLY002

        try:
            for x in _string.formatter_parser(format_string):
                yield self.make_param(*x)
        except ValueError:
            yield self.make_param(format_string)

    def make_param(self, prefix:str, key:Maybe[str]=None, format:Maybe[str]=None, conv:Maybe[str]=None) -> API.RawKey_d:  # noqa: A002
        return API.RawKey_d(prefix=prefix,
                            key=key       or "",
                            format=format or "",
                            conv=conv     or "")
