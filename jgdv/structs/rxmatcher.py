#!/usr/bin/env python3

"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

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
from uuid import UUID, uuid1

##-- end builtin imports

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
from dataclasses import InitVar, dataclass, field

if TYPE_CHECKING:
    from jgdv import Maybe, RxStr
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class RxMatcher(str):
    """ https://martinheinz.dev/blog/78 """
    __slots__ = ("string", "match")
    string  : str
    match   : Maybe[re.Match]  = None

    def __init__(self, val:str, match:Maybe[re.Match]=None) -> None:
        self.string  = val
        self.match   = match

    def __eq__(self, pattern:RxStr) -> bool:
        self.match = re.search(pattern, self.string)
        return self.match is not None

    def __getitem__(self, group:int) -> str: #type:ignore[override]
        return self.match[group]
