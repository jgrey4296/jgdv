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
from jgdv.structs.strang import CodeReference

from ._meta import DKey
from ._base import DKeyBase
from ._core import SingleDKey, MultiDKey, NonDKey
from ._interface import DKeyMark_e, ExpInst_d
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

if TYPE_CHECKING:
    from jgdv import Maybe, Ident, RxStr, Rx
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
##--|
from jgdv._abstract.protocols import SpecStruct_p, Buildable_p
from ._interface import Key_p
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class PathDKey(SingleDKey, mark=DKeyMark_e.PATH, conv="p"):
    """
    A Simple key that always expands to a path, and is then normalised
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conv_params     = "p"
        self._expansion_type  = pl.Path
        self._typecheck       = pl.Path


    def exp_final_hook(self, val:ExpInst_d, opts) -> Maybe[ExpInst_d]:
        return ExpInst_d(val=pl.Path(val.val).resolve())
