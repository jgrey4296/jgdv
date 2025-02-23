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
import string
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import sh

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv._abstract.protocols import SpecStruct_p
from jgdv.util.chain_get import ChainedKeyGetter
from jgdv.structs.chainguard import ChainGuard
from .expander import _DKeyFormatter_Expansion_m
from .meta import DKey
from .parser import RawKey
from .._interface import Key_p, DKeyMark_e, INDIRECT_SUFFIX, FMT_PATTERN
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
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
from jgdv import Maybe

if TYPE_CHECKING:
    from jgdv import Ident, FmtStr, Rx, RxStr, Func
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__file__)
##-- end logging

chained_get         : Func                         = ChainedKeyGetter.chained_get

class DKeyFormatting_m:
    """ General formatting for dkeys """

    def __format__(self, spec:str) -> str:
        """
          Extends standard string format spec language:
            [[fill]align][sign][z][#][0][width][grouping_option][. precision][type]
            (https://docs.python.org/3/library/string.html#format-specification-mini-language)

          Using the # alt form to declare keys are wrapped.
          eg: for key = DKey('test'), ikey = DKey('test_')
          f'{key}'   -> 'test'
          f'{key:w}' -> '{test}'
          f'{key:i}  ->  'test_'
          f'{key:wi} -> '{test_}'

          f'{ikey:d} -> 'test'

        """
        if not bool(spec):
            return str(self)
        rem, wrap, direct = self._consume_format_params(spec)

        # format
        result = str(self)
        if direct:
            result = result.removesuffix(INDIRECT_SUFFIX)
        elif not result.endswith(INDIRECT_SUFFIX):
            result = f"{result}{INDIRECT_SUFFIX}"

        if wrap:
            result = "".join(["{", result, "}"])

        return format(result, rem)

    def _consume_format_params(self, spec:str) -> tuple(str, bool, bool):
        """
          return (remaining, wrap, direct)
        """
        wrap     = 'w' in spec
        indirect = 'i' in spec
        direct   = 'd' in spec
        remaining = FMT_PATTERN.sub("", spec)
        assert(not (direct and indirect))
        return remaining, wrap, (direct or (not indirect))

    def format(self, *args, **kwargs) -> str:
        match kwargs.get("state", None):
            case dict() | ChainGuard() as x:
                state = x
                del kwargs['state']
            case _:
                state = kwargs

        return super().format(*args, **state)
