#!/usr/bin/env python3
"""

"""

# Imports:
##-- builtin imports
from __future__ import annotations

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
from uuid import UUID, uuid1

##-- end builtin imports

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

if TYPE_CHECKING:
    from .._interface import TomlTypes
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard, TypeVar
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from .._interface import ChainGuard_i
    T = TypeVar('T')

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


LoadFailMsg           : Final[str] = "ChainGuard Failed to Load: "
TomlLoadFailMsg       : Final[str] = "Failed to Load Toml"
DirectoryLoadFailMsg  : Final[str] = "ChainGuard Failed to load Directory: "

##--|
class TomlLoader_m:
    """ Mixin for loading toml files """

    @classmethod
    def read(cls:type[ChainGuard_i], text:str) -> ChainGuard_i:
        logging.debug("Reading ChainGuard for text")
        try:
            return cls(tomllib.loads(text)) # type: ignore[call-arg]
        except Exception as err:
            raise OSError(LoadFailMsg, text, err.args) from err

    @classmethod
    def from_dict(cls:type[ChainGuard_i], data:dict[str, TomlTypes]) -> ChainGuard_i:
        logging.debug("Making ChainGuard from dict")
        try:
            return cls(data)
        except Exception as err:
            raise OSError(LoadFailMsg, data, err.args) from err

    @classmethod
    def load(cls:type[ChainGuard_i], *paths:str|pl.Path) -> ChainGuard_i:
        logging.debug("Creating ChainGuard for %s", paths)
        texts = []
        for path in paths:
            texts.append(pl.Path(path).read_text())
        else:
            try:
                return cls(tomllib.loads("\n".join(texts)))
            except tomllib.TOMLDecodeError as err:
                raise OSError(TomlLoadFailMsg, *err.args, paths) from err

    @classmethod
    def load_dir(cls:type[ChainGuard_i], dirp:str|pl.Path) -> ChainGuard_i:
        logging.debug("Creating ChainGuard for directory: %s", str(dirp))
        try:
            texts = []
            for path in pl.Path(dirp).glob("*.toml"):
                texts.append(path.read_text())

            return cls(tomllib.loads("\n".join(texts)))
        except Exception as err:
            raise OSError(DirectoryLoadFailMsg, dirp, err.args) from err
