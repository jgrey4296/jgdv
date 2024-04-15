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

class TexSections_e(enum.Enum):
    header  = enum.auto()
    footer  = enum.auto()
    meta    = enum.auto()
    preface = enum.auto()
    body    = enum.auto()


class TexBuilder_i:
    """ Utility class for creating tex files
      accumulates entries non-linearly,
      then writes them to a file in a particular order
    """

    def __init__(self):
        self._current  = []
        self._sections = {}
        pass

    def author(self):
        pass

    def header(self):
        pass

    def footer(self):
        pass

    def compile(self, section) -> str:
        """ compile a section, calling str on each element """
        pass

    def escape(self, s:str):
        return

    def commit(self, section:str|TexEnvironment_i|TexStatement_i):
        """
          commit the current state into a particular section
        """
        pass

    def add(self, *args):
        pass

class TexEnvironment_i:
    """ Utility base class for using tex environments as a context manager,
      adding state non-linearly
    """

    def __init__(self):
        self._current = []
        self._sections = {}
        self._target_section = None
        pass

    def __str__(self):
        pass

    def __enter__(self) -> Any:
        #return self
        return

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
       # return False to reraise errors
        return

    def header(self):
        pass

    def footer(self):
        pass

    def file_header(self):
        pass

class TexStatement_i:
    """ Utility class interface for building a particular type of tex statement """

    def __init__(self):
        self._target_section = None
        pass

    def __str__(self):
        pass
