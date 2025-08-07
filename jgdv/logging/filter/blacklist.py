#!/usr/bin/env python3
"""

"""

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
import weakref
# ##-- end stdlib imports

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

    from logging import LogRecord
    from jgdv import Maybe
## isort: on
# ##-- end type checking

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# True to process, False to reject

class BlacklistFilter:
    """
      A Logging filter to blacklist regexs of logger names
    """

    def __init__(self, blacklist:Maybe[list[str]]=None) -> None:
        self._blacklist   = blacklist or []
        self.blacklist_re  = re.compile("^({})".format("|".join(self._blacklist)))

    def __call__(self, record:LogRecord) -> bool:
        if record.name == "root":
            return True
        if not bool(self._blacklist):
            return True

        return not bool(self.blacklist_re.match(record.name))
