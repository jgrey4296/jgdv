#!/usr/bin/env python3
"""

"""

# Imports:
##-- builtin imports
from __future__ import annotations

# ##-- stdlib imports
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
import tomllib
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    Self,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

##-- end builtin imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv.structs.chainguard import GuardedAccessError, TomlTypes

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class TomlLoader_m:
    """ Mixin for loading toml files """

    @classmethod
    def read(cls:T, text:str) -> T:
        logging.debug("Reading ChainGuard for text")
        try:
            return cls(tomllib.loads(text))
        except Exception as err:
            raise IOError("ChainGuard Failed to Load: ", text, err.args) from err

    @classmethod
    def from_dict(cls, data:dict[str, TomlTypes]) -> Self:
        logging.debug("Making ChainGuard from dict")
        try:
            return cls(data)
        except Exception as err:
            raise IOError("ChainGuard Failed to Load: ", data, err.args) from err

    @classmethod
    def load(cls, *paths:str|pl.Path) -> Self:
        logging.debug("Creating ChainGuard for %s", paths)
        try:
            texts = []
            for path in paths:
                texts.append(pl.Path(path).read_text())

            return cls(tomllib.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("ChainGuard Failed to Load: ", paths, err.args) from err

    @classmethod
    def load_dir(cls, dirp:str|pl.Path) -> Self:
        logging.debug("Creating ChainGuard for directory: %s", str(dirp))
        try:
            texts = []
            for path in pl.Path(dirp).glob("*.toml"):
                texts.append(path.read_text())

            return cls(tomllib.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("ChainGuard Failed to Directory: ", dirp, err.args) from err
