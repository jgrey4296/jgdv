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
    import pathlib as pl
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from ._interface import Strang_p
    from jgdv._abstract.pre_processable import PreProcessor_p, PreProcessResult, InstanceData, PostInstanceData
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
StrMeta      : Final[type]  = type(str)
HasDictFail  : Final[str]   = "The resulting strang has a __dict__. Set the subclass to have __slots__=()"
# Body:

class StrangMeta(StrMeta):
    """ A Metaclass for Strang
    It runs the pre-processsing and post-processing on the constructed str
    to turn it into a strang
    """

    def __call__[T:Strang_p](cls:type[T], text:str|pl.Path, *args:Any, **kwargs:Any) -> Strang_p:  # noqa: ANN401, N805
        """ Overrides normal str creation to allow passing args to init """
        ctor       : type[T]
        obj        : T
        processor  : PreProcessor_p[T]  = cls._processor
        stage      : str                = "Pre-Process"

        try:
            text, inst_data, post_data, new_ctor = processor.pre_process(cls,
                                                                         text,
                                                                         *args,
                                                                         strict=kwargs.pop("strict", False),
                                                                         **kwargs,
                                                                         )
            ctor   = new_ctor or cls
            stage  = "__new__"
            obj    = ctor.__new__(ctor, text)
            stage  = "__init__"
            obj.__init__(*args, **collections.ChainMap(inst_data, kwargs)) # type: ignore[misc]
            stage  = "Process"
            obj    = processor.process(obj, data=post_data) or obj
            stage  = "Post-Process"
            obj    = processor.post_process(obj, data=post_data) or obj
        except ValueError as err:
            raise errors.StrangError(errors.StrangCtorFailure.format(cls=cls.__name__, stage=stage),
                                     err, text, cls, processor) from None
        else:
            assert(isinstance(obj, str))
            if hasattr(obj, "__dict__"):
                raise ValueError(HasDictFail, type(obj))
            return obj

