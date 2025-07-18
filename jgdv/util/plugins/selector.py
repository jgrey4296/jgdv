#!/usr/bin/env python3
"""
A function to select an appropriate plugin by passed in name or names

"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
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
import weakref
from importlib.metadata import EntryPoint
from uuid import UUID, uuid1

# ##-- end stdlib imports

from jgdv.structs.strang import CodeReference

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
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   from jgdv.structs.chainguard import ChainGuard

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

def plugin_selector(plugins:ChainGuard, *,
                    target:str="default",
                    fallback:Maybe[type|str|CodeReference]=None) -> Maybe[type]:
    """ Selects and loads a plugin from a chainguard,
    based on a target,
    with an available fallback constructor

    if the target is a suitable coderef, it is coerced and loaded instead,
    bypassing the plugins
    """
    logging.debug("Selecting plugin for target: %s", target)

    match target:
        case "default":
            pass
        case str() as x:
            try:
                name = CodeReference(target)
                return name()
            except ImportError as err:
                pass
            except (AttributeError, KeyError) as err:
                pass

    match plugins:
        case []:
            pass
        case [EntryPoint() as l]: # if theres only one, use that
            return l.load()
        case [EntryPoint() as l, *_] if target == "default": # If the preference is the default, use the first
            return l.load()
        case [*_] as loaders: # Otherwise, use the loader that matches the preferred's name
            matching = [x for x in loaders if x.name == target]
            if bool(matching):
                return matching[0].load()
            else:
                raise ValueError("No matching plugin for target", target)
        case type():
            return x
        case _:
            msg = "Unknown type passed to plugin selector"
            raise TypeError(msg, plugins)

    match fallback:
        case str():
            coderef = CodeReference(fallback)
            return coderef()
        case CodeReference():
            return fallback()
        case type():
            return fallback
        case _:
            msg = "No Available Plugin, and no fallback constructor"
            raise ValueError(msg, target, fallback, plugins)
