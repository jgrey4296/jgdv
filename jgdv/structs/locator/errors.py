#!/usr/bin/env python3
"""


"""
# Imports:
from __future__ import annotations

from jgdv.structs.strang.errors import StrangError

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
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

# Vars:

# Body:

class LocationError(StrangError):
    """ A Task tried to access a location that didn't existing """
    general_msg = "Location Error:"

class LocationExpansionError(LocationError):
    """ When trying to resolve a location, something went wrong. """
    general_msg = "Expansion of Location hit max value:"

class DirAbsent(LocationError):
    """ In the course of startup verification, a directory was not found """
    general_msg = "Missing Directory:"
