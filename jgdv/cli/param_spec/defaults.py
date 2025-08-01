#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import builtins
import datetime
import enum
import functools as ftz
import importlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import typing
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv.mixins.annotate.annotate import SubAnnotate_m
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from jgdv.cli.errors import ArgParseError
from .param_spec import ParamSpec
from .core import ToggleParam
from .extra import RepeatToggleParam, LiteralParam
from .._interface import ParamSpec_p

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
# isort: on
# ##-- end types
##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class HelpParam(ToggleParam): #[bool]):
    """ The --help flag that is always available """

    desc : str = "The Default Help Param"

    def __init__(self, **kwargs:Any) -> None:  # noqa: ANN401
        kwargs.update({"name":"--help", "default":False, "implicit":True})
        super().__init__(**kwargs)

class VerboseParam(RepeatToggleParam): #[int]):
    """ The implicit -verbose flag """

    desc : str = "The Default Verbosity Param"

    def __init__(self, **kwargs:Any) -> None:  # noqa: ANN401
        kwargs.update({"name":"--verbose", "default":0, "implicit":True})
        super().__init__(**kwargs)

class SeparatorParam(LiteralParam):
    """ A Parameter to separate subcmds """

    desc : str = "The Default Separator Param"

    def __init__(self, **kwargs:Any) -> None:  # noqa: ANN401
        kwargs.update({"name":"--", "implicit":True})
        super().__init__(**kwargs)
