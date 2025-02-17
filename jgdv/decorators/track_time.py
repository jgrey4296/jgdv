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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv.util.time_ctx import TimeCtx
from jgdv.decorators.meta_decorator import MetaDecorator

# ##-- end 1st party imports

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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type Logger = logmod.Logger

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class TrackTime(MetaDecorator):
    """ Decorate a callable to track its timing """

    def __init__(self, logger:Maybe[Logger]=None, level:Maybe[int|str]=None, entry:Maybe[str]=None, exit:Maybe[str]=None, **kwargs):
        kwargs.setdefault("mark", "_timetrack_mark")
        kwargs.setdefault("data", "_timetrack_data")
        super().__init__([], **kwargs)
        self._logger = logger
        self._level  =  level
        self._entry  = entry
        self._exit   = exit

    def wrap_fn[T](self, fn:T) -> T:
        logger, enter, exit, level = self._logger, self._entry, self.exit, self.level

        def track_time_wrapper(*args, **kwargs):
            with TimeCtx(logger, enter, exit, level):
                return fn(*args, **kwargs)

        return track_time_wrapper

    def wrap_method(self, fn):
        return self._wrap_fn(fn)
