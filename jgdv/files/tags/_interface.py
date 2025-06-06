#!/usr/bin/env python3
"""

"""
# ruff: noqa:

# Imports:
from __future__ import annotations
import re

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe, Rx
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

# Vars:
TAG_NORM         : Final[Rx]         = re.compile(" +")
SEP              : Final[str]        = " : "
ALT_SEP          : Final[str]        = " :: "
TAG_EXT          : Final[str]        = ".tags"
SUB_EXT          : Final[str]        = ".sub"
NORM_REPLACE     : Final[str]        = "_"
COMMENT          : Final[str]        = "%%"

# Body:
