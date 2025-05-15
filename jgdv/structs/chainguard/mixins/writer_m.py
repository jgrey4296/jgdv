#!/usr/bin/env python3
"""

"""

##-- builtin imports
from __future__ import annotations

import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
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
from typing import Generic, NewType, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    import pathlib as pl
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from .._interface import ChainGuard_i

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

try:
    import tomli_w

    class TomlWriter_m:
        """ A mixin for adding toml-writing functionality """

        def __str__(self:ChainGuard_i) -> str:
            return tomli_w.dumps(self._table())

        def to_file(self:ChainGuard_i, path:pl.Path) -> None:
            path.write_text(str(self))

except ImportError:
    logging.debug("No Tomli-w found, ChainGuard will not write toml, only read it")

    class TomlWriter_m: # type: ignore[no-redef]
        """ A fallback mixin for when toml-writing isnt available"""

        def to_file(self, path:pl.Path) -> None:
            msg = "Tomli-w isn't installed, so ChainGuard can't write, only read"
            raise NotImplementedError(msg)
