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
import types
import weakref
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
# ##-- end stdlib imports

from jgdv import Maybe, RxStr
import stackprinter

# Global Vars:

# Body:

class StackFormatter_m(logmod.Formatter):
    """ A Mixin Error formatter, adapted from stackprinter's docs """

    indent_str       : ClassVar[str]         = "  |  "
    suppress         : ClassVar[list[RxStr]] = [r".*pydantic.*"]
    source_lines     : ClassVar[int|str]     = 0
    use_stackprinter : bool                  = True

    def formatException(self, exc_info):
        if not self.use_stackprinter:
            return super().formatException(exc_info)

        msg : str = stackprinter.format(exc_info,
                                        source_lines=self.source_lines,
                                        suppressed_paths=self.suppress)
        lines = msg.splitlines()
        indented = [f"{self.indent_str}{line}\n" for line in lines]
        return "".join(indented)


    def formatStack(self, stack_info):
        return super().formatStack(stack_info)
