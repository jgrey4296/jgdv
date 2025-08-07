#!/usr/bin/env python3
"""

"""
# Import:
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
import weakref
from uuid import UUID, uuid1
# ##-- end stdlib imports

import stackprinter

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
# isort: on
# ##-- end types

# ##-- type checking
# isort: off
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, RxStr
## isort: on
# ##-- end type checking

# Global Vars:

# Body:

class StackFormatter_m:
    """ A Mixin Error formatter, adapted from stackprinter's docs
    Compactly Formats the error stack trace, without src.

    """

    indent_str       : ClassVar[str]         = "  |  "
    suppress         : ClassVar[list[RxStr]] = [r".*pydantic.*", r"<frozen importlib._bootstrap>"]
    source_height    : ClassVar[int]         = 10
    source_lines     : ClassVar[int|str]     = 0
    use_stackprinter : bool                  = True

    def formatException(self, exc_info:Maybe[tuple]) -> str:  # noqa: N802
        match exc_info:
            case None | (None, None, None):
                return ""
            case _ if not self.use_stackprinter:
                return cast("str", super().formatException(exc_info)) # type: ignore[misc]

        msg : str = stackprinter.format(exc_info,
                                        source_lines=self.source_lines,
                                        suppressed_paths=self.suppress)
        lines = [x for x in msg.splitlines() if bool(x)]
        indented = [f"{self.indent_str}{line}\n" for line in lines[-self.source_height:]]
        return "".join(indented)

    def formatStack(self, stack_info:str) -> str:  # noqa: N802
        return cast("str", super().formatStack(stack_info)) # type: ignore[misc]
