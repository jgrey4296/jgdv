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

    from ._interface import Strang_i, PreProcessor_p
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

    _forms : ClassVar[list[type[Strang_i]]] = []

    @staticmethod
    def register(new_cls:type[Strang_i]) -> None:
        StrangMeta._forms.append(new_cls)

    def __call__(cls:type[Strang_i], text:str|pl.Path, *args:Any, **kwargs:Any) -> Strang_i:  # noqa: ANN401, N805
        """ Overrides normal str creation to allow passing args to init """
        match text:
            case pl.Path():
                text = str(text)
            case str():
                text = str(text)
            case _:
                pass

        processor  : PreProcessor_p  = cls._processor
        stage      : str               = "Pre-Process"

        try:
            text, data = processor.pre_process(cls,
                                               text,
                                               strict=kwargs.get("strict", False))
            data.update({x:y for x,y in kwargs.items() if y is not None})
            stage = "__new__"
            obj = str.__new__(cls, text)
            obj.__class__ = cls
            stage = "__init__"
            cls.__init__(obj, *args, **data)
            stage = "Process"
            obj = processor.process(obj) or obj
            stage = "Post-Process"
            obj = processor.post_process(obj) or obj
        except ValueError as err:
            raise errors.StrangError(errors.StrangCtorFailure.format(cls=cls.__name__, stage=stage),
                                     err, text, cls, processor) from None
        else:
            return obj
