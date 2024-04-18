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

class JGDVMultiKey(JGDVBaseKey):
    """ A string or path of multiple keys """

    def __init__(self, val:str|pl.Path):
        self.value : str|pl.Path        = val
        self._keys : set[JGDVSimpleKey] = set(JGDVSimpleKey(x) for x in PATTERN.findall(str(val)))

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "<JGDVMultiKey: {}>".format(str(self))

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        match other:
            case JGDVBaseKey() | str() | pl.Path():
                return str(self) == str(other)
            case _:
                return False

    def keys(self) -> set(JGDVSimpleKey):
        return self._keys

    @property
    def form(self):
        """ Return the key in its use form """
        return str(self)

    def expand(self, spec=None, state=None, *, rec=False, insist=False, chain:list[JGDVBaseKey]=None, on_fail=Any, locs=None, **kwargs) -> str:
        try:
            return DootFormatter.fmt(self.value, _spec=spec, _state=state, _rec=rec, _insist=insist, _locs=locs)
        except (KeyError, TypeError) as err:
            if bool(chain):
                return chain[0].expand(spec, state, rec=rec, chain=chain[1:], on_fail=on_fail)
            elif on_fail != Any:
                return on_fail
            else:
                raise err

    def within(self, other:str|dict|TomlGuard) -> bool:
        return str(self) in other

    def to_type(self, spec, state, type_=Any, chain:list[JGDVBaseKey]=None, on_fail=Any) -> Any:
        raise TypeError("Converting a MultiKey to a type doesn't build sense", self)
