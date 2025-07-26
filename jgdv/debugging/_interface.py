#!/usr/bin/env python3
"""

"""
# ruff: noqa:

# Imports:
from __future__ import annotations

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

    from jgdv import Maybe, Frame
## isort: on
# ##-- end type checking

# Vars:
DEL_LOG_K         : Final[str] = "_log_del_active"
DEFAULT_LOG_LEVEL : Final[int] = 40
DEFAULT_REPORT    : Final[str] = "traceback"
CHANGE_PREFIX     : Final[str] = "+-:"
DEFAULT_PREFIX    : Final[str] = "--"

type TraceEvent = (
    Literal["call"]
    | Literal["line"]
    | Literal["return"]
    | Literal["exception"]
    | Literal["opcode"]
)
# Body:

class TraceFn_p(Protocol):
    """ The protocol for functions for sys.settrace """

    def __call__(self, frame:Frame, event:TraceEvent, arg:Any) -> Maybe[TraceFn_p]: ... # noqa: ANN401
