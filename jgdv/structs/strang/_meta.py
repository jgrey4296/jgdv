#!/usr/bin/env python3
"""

"""
# ruff: noqa:

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
import types
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from . import errors

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

    from ._interface import Strang_i
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
StrMeta : Final[type] = type(str)
# Body:

class StrangMeta(StrMeta):
    """ A Metaclass for Strang
    It runs the pre-processsing and post-processing on the constructed str
    to turn it into a strang
    """

    _forms : ClassVar[list[type]] = []

    def __call__(cls:type[Strang_i], data:str|pl.Path, *args:Any, **kwargs:Any) -> Strang_i:  # noqa: ANN401, N805
        """ Overrides normal str creation to allow passing args to init """
        match data:
            case pl.Path():
                data = str(data)
            case str():
                data = str(data)
            case _:
                pass

        try:
            data = cls.pre_process(data, strict=kwargs.get("strict", False))
        except ValueError as err:
            msg = "Pre-Strang Error"
            raise errors.StrangError(msg, cls, err, data) from None

        obj = cls.__new__(cls, data)
        try:
            cls.__init__(obj, *args, **kwargs)
        except ValueError as err:
            msg = "Strang Init Error"
            raise errors.StrangError(msg, cls, err, data) from None

        try:
            # TODO don't call process and post_process if given the metadata in kwargs
            obj._process()
        except ValueError as err:
            msg = "Strang Process Error"
            raise errors.StrangError(msg, cls, err, data) from None

        try:
            # TODO allow post-process to override and return a different object?
            obj._post_process()
        except ValueError as err:
            msg = "Post-Strang Error:"
            raise errors.StrangError(msg, cls, err) from None

        return obj
