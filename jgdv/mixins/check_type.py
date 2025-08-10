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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
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
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

    type CheckType    = type | types.UnionType
    type CheckCancel  = Literal[False]

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class CheckType_m:
    """ A Mixin for runtime type checking """

    def _check_type(self, value:Any, check:Maybe[CheckType|CheckCancel]=None) -> None:
        is_type      : bool
        check_target : Maybe[CheckType]

        if check is False or value is None:
            return

        check_target = check
        is_type      = isinstance(value, type)

        match check_target, value:
            case None, _:
                return
            case x, type() as val if isinstance(x, type|UnionTypes) and x is not None and issubclass(val, x):
                return
            case type() | types.UnionType(), val if isinstance(val, check_target):
                return
            case _:
                raise ImportError(errors.CodeRefImportUnknownFail, self, check_target)
