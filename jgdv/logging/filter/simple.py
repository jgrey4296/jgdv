#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import re
import logging as logmod

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
    from jgdv import Maybe, RxStr
## isort: on
# ##-- end type checking

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# True to process, False to reject

class SimpleFilter:
    """
      A Simple filter to reject based on:
      1) a whitelist of regexs,
      2) a simple list of rejection names

    """

    def __init__(self, allow:Maybe[list[RxStr]]=None, reject:Maybe[list[str]]=None) -> None:
        self.allowed    = allow or []
        self.rejections = reject or []
        self.allowed_re    = re.compile("^({})".format("|".join(self.allowed)))
        if bool(self.allowed):
            msg = "Logging Allows are not implemented yet"
            raise NotImplementedError(msg)

    def __call__(self, record:LogRecord) -> bool:
        if record.name in ["root", "__main__"]:
            return True
        if not (bool(self.allowed) or bool(self.rejections)):
            return True

        rejected = False
        rejected |= any(x in record.name for x in self.rejections)
        return not rejected
