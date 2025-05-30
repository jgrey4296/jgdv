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

    from jgdv import Maybe, MaybeT

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
InstanceData              = NewType("InstanceData", dict)
PostInstanceData          = NewType("PostInstanceData", dict)

type HookOverride         = bool
type PreProcessResult[T]  = tuple[str, InstanceData, PostInstanceData, Maybe[type[T]]]
# Body:

class PreProcessor_p[T](Protocol):
    """ Protocol for things like Strang,
    whose metaclass preprocess the initialisation data before even __new__ is called.

    Is used in a metatype.__call__ as::

        cls._pre_process(...)
        obj = cls.__new__(...)
        obj.__init__(...)
        obj._process()
        obj._post_process()
        return obj

    """

    def pre_process(self, cls:type[T], input:Any, *args:Any, strict:bool=False, **kwargs:Any) -> PreProcessResult[T]: ...  # noqa: A002, ANN401

    def process(self, obj:T, *, data:PostInstanceData) -> Maybe[T]: ...

    def post_process(self, obj:T, *, data:PostInstanceData) -> Maybe[T]: ...

class ProcessorHooks[T](Protocol):
    """ Hooks a PreProcessor_p recognizes.

    returning True as the first result value means the processor's logic is *not* to be used.
    otherwise it *is* used, with the results from the hook
    """

    @classmethod
    def _pre_process_h(cls:type[T], input:Any, *args:Any, strict:bool=False, **kwargs:Any) -> MaybeT[bool, PreProcessResult[T]]: ...  # noqa: A002, ANN401

    def _process_h(self, *, data:PostInstanceData) -> Maybe[tuple[HookOverride, Maybe[T]]]: ...

    def _post_process_h(self, *, data:PostInstanceData) -> Maybe[tuple[HookOverride, Maybe[T]]]: ...
