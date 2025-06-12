#!/usr/bin/env python3
"""

"""
# ruff: noqa:

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import builtins
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

from .param_spec import ParamSpec
from .param_spec.core import ToggleParam, LiteralParam, KeyParam, AssignParam
from .param_spec.defaults import HelpParam, VerboseParam, SeparatorParam
from .param_spec.positional import PositionalParam

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

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

def _remap_type(data:dict) -> type:
    """
    Get a specific type of parameter, using provided dat

    needs to handle:
    - using separator to select between toggle, key, assign, and positional params
    - using type to select toggle, literal
    - using count to select repeatable
    - using choice to select choice params
    """

    match data:
        case {"separator": str() as x } if bool(x):
            return AssignParam
        case {"prefix" : int() }:
            return PositionalParam
        case {"type": x } if x is not bool:
            return KeyParam
        case _:
            return ToggleParam

##--|

class ParamSpecMaker_m:
    __slots__ = ()

    @staticmethod
    def build_param(**kwargs:Any) -> ParamSpec:
        """ Utility method for easily making paramspecs """
        data = dict(kwargs)
        # Parse the name
        match ParamSpec._processor.parse_name(data['name']):
            case None:
                pass
            case dict() as parsed:
                data.update(parsed)

        # remap to a specific paramspec type
        refined = _remap_type(data)
        # build it
        return refined.build(kwargs)
