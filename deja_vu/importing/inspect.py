#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import importlib

def init_inspect(mod_str):
    """
    Import and Inspect the passed in module for potential constructor functions
    to init with
    """
    mod = importlib.import_module(mod_str)
    try:
        not_dunders    = [getattr(mod, x) for x in dir(mod) if "__" not in x]
        not_modules    = [x for x in not_dunders if not isinstance(x, ModuleType)]
        correct_module = [x for x in not_modules if mod_str in x.__module__]
        funcs = [x for x in correct_module if isinstance(x, FunctionType)]
        engines        = [x for x in correct_module if isinstance(x, type) and issubclass(x, AcabEngine_i)]
        total = funcs + engines

        if not bool(total):
            return print(f"No Available Constructors in {mod_str}")

        print(f"Potential Constructors in {mod_str}:")
        for x in total:
            print(f"-- {x.__name__}")
    except:
        breakpoint()
