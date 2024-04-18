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
# import more_itertools as mitz
# from boltons import
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv.keys import JGDVKey
from jgdv.utils.chain_get import ChainedKeyGetter

class JGDVFormatter(string.Formatter):
    """
      A Formatter for expanding arguments based on action spec kwargs, and task state, and cli args
    """
    _fmt                = None

    SPEC   : Final[str] = "_spec"
    INSIST : Final[str] = "_insist"
    STATE  : Final[str] = "_state"
    LOCS   : Final[str] = "_locs"
    REC    : Final[str] = "_rec"

    @staticmethod
    def fmt(fmt:str|JGDVKey|pl.Path, /, *args, **kwargs) -> str:
        if not JGDVFormatter._fmt:
            JGDVFormatter._fmt = JGDVFormatter()

        return JGDVFormatter._fmt.format(fmt, *args, **kwargs)

    def format(self, fmt:str|JGDVKey|pl.Path, /, *args, **kwargs) -> str:
        """ expand and coerce keys """
        self._depth = 0
        match kwargs.get(self.SPEC, None):
            case None:
                kwargs['_spec'] = {}
            case SpecStruct_p():
                kwargs['_spec'] = kwargs[self.SPEC].params
            case x:
                raise TypeError("Bad Spec Type in Format Call", x)

        match fmt:
            case JGDVKey():
                fmt = fmt.form
                result = self.vformat(fmt, args, kwargs)
            case str():
                result = self.vformat(fmt, args, kwargs)
            # case pl.Path():
            #     result = str(ftz.reduce(pl.Path.joinpath, [self.vformat(x, args, kwargs) for x in fmt.parts], pl.Path()))
            case _:
                raise TypeError("Unrecognized expansion type", fmt)

        return result

    def get_value(self, key, args, kwargs):
        """ lowest level handling of keys being expanded """
        logging.debug("Expanding: %s", key)
        if isinstance(key, int):
            return args[key]

        insist                = kwargs.get(self.INSIST, False)
        spec  : dict          = kwargs.get(self.SPEC, None) or {}
        state : dict          = kwargs.get(self.STATE, None) or {}
        locs  : JGDVLocations = kwargs.get(self.LOCS,  None)
        depth_check           = self._depth < MAX_KEY_EXPANSIONS
        rec_allowed           = kwargs.get(self.REC, False) and depth_check

        match (replacement:=ChainedKeyGetter.chained_get(key, spec, state, locs)):
            case None if insist:
                raise KeyError("Key Expansion Not Found")
            case None:
                return JGDVKey.build(key).form
            case JGDVKey() if depth_check:
                self._depth += 1
                return self.vformat(replacement.form, args, kwargs)
            case str() if rec_allowed:
                self._depth += 1
                return self.vformat(str(replacement), args, kwargs)
            case str():
                return replacement
            case pl.Path() if depth_check:
                self._depth += 1
                return ftz.reduce(pl.Path.joinpath, map(lambda x: self.vformat(x, args, kwargs), replacement.parts), pl.Path())
            case _:
                return str(replacement)
                # raise TypeError("Replacement Value isn't a string", args, kwargs)
