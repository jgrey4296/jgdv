#!/usr/bin/env python3
"""

"""

from __future__ import annotations

from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)

from jgdv import JGDVError

class StrangError(JGDVError):
    pass

class LocationError(StrangError):
    """ A Task tried to access a location that didn't existing """
    general_msg = "Location Error:"

class LocationExpansionError(LocationError):
    """ When trying to resolve a location, something went wrong. """
    general_msg = "Expansion of Location hit max value:"

class DirAbsent(LocationError):
    """ In the course of startup verification, a directory was not found """
    general_msg = "Missing Directory:"
