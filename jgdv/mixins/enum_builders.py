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
from typing import Generic, NewType, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class EnumBuilder_m:
    """ A Mixin to add a .build(str) method for the enum """

    @classmethod
    def build[T:enum.EnumMeta](cls:type[T], val:str|T, *, strict:bool=True) -> T:
        try:
            match val:
                case str():
                    return cls[val]
                case cls():
                    return val
                case _:
                    msg = "Can't create an enum"
                    raise TypeError(msg, val)
        except KeyError:
            logging.warning("Can't Create an enum of (%s):%s. Available: %s", cls, val, list(cls.__members__.keys()))
            if strict:
                raise
            return T.default

class FlagsBuilder_m:
    """ A Mixin to add a .build(vals) method for EnumFlags """

    @classmethod
    def build[T:enum.EnumMeta](cls:type[T], vals:str|list|dict, *, strict:bool=True) -> T:
        match vals:
            case str():
                vals = [vals]
            case list():
                pass
            case dict():
                vals = [x for x,y in vals.items() if bool(y)]

        base = cls.default
        for x in vals:
            try:
                match x:
                    case str():
                        base |= cls[x]
                    case cls():
                        base |= x
            except KeyError:
                logging.warning("Can't create a flag of (%s):%s. Available: %s", cls, x, list(cls.__members__.keys()))
                if strict:
                    raise
        else:
            return base
