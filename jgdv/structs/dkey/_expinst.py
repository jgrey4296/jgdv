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
    from jgdv.structs.dkey import DKey
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

# Vars:

# Body:
class ExpInst:
    """ simple holder of expansion instructions"""
    __slots__ = "val", "rec", "fallback", "lift", "literal", "convert", "total_recs"

    def __init__(self, val:DKey|str, **kwargs):
        if isinstance(val, ExpInst):
            raise TypeError("Nested ExpInst", val)
        object.__setattr__(self, "val", val)
        object.__setattr__(self, "rec", kwargs.get("rec", -1))
        object.__setattr__(self, "fallback", kwargs.get("fallback", None))
        object.__setattr__(self, "lift", kwargs.get("lift", False))
        object.__setattr__(self, "literal", kwargs.get("literal", False))
        object.__setattr__(self, "convert", kwargs.get("convert", None))
        object.__setattr__(self, "total_recs", kwargs.get("total_recs", 1))

    def __repr__(self) -> str:
        lit = "(Lit)" if self.literal else ""
        return f"<ExpInst:{lit} {self.val!r} / {self.fallback!r} (R:{self.rec},L:{self.lift},C:{self.convert})>"
