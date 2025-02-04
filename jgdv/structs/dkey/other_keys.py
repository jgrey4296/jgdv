#!/usr/bin/env python2
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
import string
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv._abstract.protocols import Key_p, SpecStruct_p, Buildable_p
from jgdv.structs.strang import CodeReference

from jgdv.structs.dkey._base import DKeyBase
from jgdv.structs.dkey._core import SingleDKey, MultiDKey, NonDKey
from jgdv.structs.dkey._meta import DKey, DKeyMark_e

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
    from jgdv import Maybe, Ident, RxStr, Rx
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

KEY_PATTERN        : Final[RxStr]                = "{(.+?)}"
MAX_KEY_EXPANSIONS : Final[int]                  = 10

PATTERN            : Final[Rx]                   = re.compile(KEY_PATTERN)
FAIL_PATTERN       : Final[Rx]                   = re.compile("[^a-zA-Z_{}/0-9-]")
FMT_PATTERN        : Final[Rx]                   = re.compile("[wdi]+")
EXPANSION_HINT     : Final[Ident]                = "_doot_expansion_hint"
HELP_HINT          : Final[Ident]                = "_doot_help_hint"
FORMAT_SEP         : Final[Ident]                = ":"
CWD_MARKER         : Final[Ident]                = "__cwd"

class ArgsDKey(SingleDKey, mark=DKeyMark_e.ARGS):
    """ A Key representing the action spec's args """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._expansion_type  = list
        self._typecheck = list

    def expand(self, *sources, **kwargs) -> list:
        for source in sources:
            if not isinstance(source, SpecStruct_p):
                continue

            return source.args

        return []

class KwargsDKey(SingleDKey, mark=DKeyMark_e.KWARGS):
    """ A Key representing all of an action spec's kwargs """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._expansion_type  = dict
        self._typecheck = dict

    def expand(self, *sources, fallback=None, **kwargs) -> dict:
        for source in sources:
            if not isinstance(source, SpecStruct_p):
                continue

            return source.kwargs

        return fallback or dict()
