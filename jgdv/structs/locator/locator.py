#!/usr/bin/env python3
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
import os
import pathlib as pl
import re
import typing
from copy import deepcopy
from dataclasses import InitVar, dataclass, field, replace
from re import Pattern
from collections import defaultdict, deque
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv.mixins.path_manip import PathManip_m
from jgdv.structs.chainguard import ChainGuard
from jgdv.structs.dkey import DKey, DKeyFormatter, MultiDKey, NonDKey, SingleDKey

from .location import Location, LocationMeta_e
from .errors import DirAbsent, LocationError, LocationExpansionError
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, Any
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
   from jgdv import Maybe, Stack, Queue
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   type FmtStr = str
   type JGDVLocator = Any
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
# If CLI:
# logging = logmod.root
# logging.setLevel(logmod.NOTSET)
##-- end logging

class _LocatorGlobal:
    """ A program global stack of locations.
    Provides the enter/exit store for JGDVLocator objects
    """

    _global_locs : ClassVar[list[JGDVLocator]] = []
    _startup_cwd : ClassVar[pl.Path] = pl.Path.cwd()

    @staticmethod
    def stacklen() -> int:
        return len(_LocatorGlobal._global_locs)

    @staticmethod
    def peek() -> None|"JGDVLocator":
        match _LocatorGlobal._global_locs:
            case []:
                return None
            case [*_, x]:
                return x

    @staticmethod
    def push(locs):
        _LocatorGlobal._global_locs.append(locs)

    @staticmethod
    def pop() -> None|"JGDVLocator":
        match _LocatorGlobal._global_locs:
            case []:
                return None
            case [*xs, x]:
                _LocatorGlobal._global_locs = xs
                return x

    def __get__(self, obj, objtype=None):
        """ use the descriptor protocol to make a pseudo static-variable
        https://docs.python.org/3/howto/descriptor.html
        """
        return _LocatorGlobal.peek()

class _LocatorUtil_m:

    def update(self, extra:dict|ChainGuard|Location|JGDVLocator, strict=True) -> Self:
        """
          Update the registered locations with a dict, chainguard, or other dootlocations obj.

        when strict=True (default), don't allow overwriting existing locations
        """
        match extra: # unwrap to just a dict
            case dict():
                pass
            case Location():
                extra = {extra.name : extra}
            case ChainGuard():
                return self.update(dict(extra), strict=strict)
            case JGDVLocator():
                return self.update(extra._data, strict=strict)
            case _:
                raise TypeError("Tried to update locations with unknown type", extra)

        raw          = dict(self._data.items())
        base_keys    = set(raw.keys())
        new_keys     = set(extra.keys())
        conflicts    = (base_keys & new_keys)
        if strict and bool(conflicts):
            raise LocationError("Strict Location Update conflicts", conflicts)

        for k,v in extra.items():
            match Location(v):
                case Location() as loc:
                    raw[k] = loc
                case _:
                    raise LocationError("Couldn't build a Location", k, v)

        logging.debug("Registered New Locations: %s", ", ".join(new_keys))
        self._data = raw
        return self

    def metacheck(self, key:str|DKey, *meta:LocationMeta_e) -> bool:
        """ return True if key provided has the applicable metadata"""
        match key:
            case NonDKey():
                return False
            case DKey() if key in self._data:
                data = self._data[key]
                return all(x in data for x in meta)
            case MultiDKey():
                 for k in key:
                     if k not in self._data:
                         continue
                     data = self._data[key]
                     if not all(x in data for x in meta):
                         return False
            case str():
                return self.metacheck(DKey(key, implicit=True), meta)
        return False

    def registered(self, *values, task="doot", strict=True) -> set:
        """ Ensure the values passed in are registered locations,
          error with DirAbsent if they aren't
        """
        missing = set(x for x in values if x not in self)

        if strict and bool(missing):
            raise DirAbsent("Ensured Locations are missing for %s : %s", task, missing)

        return missing

    def normalize(self, path:pl.Path|Location, symlinks:bool=False) -> pl.Path:
        """
          Expand a path to be absolute, taking into account the set doot root.
          resolves symlinks unless symlinks=True
        """
        match path:
            case Location() if Location.gmark_e.earlycwd in path:
                the_path = path.path
                return self._normalize(the_path, root=_LocatorGlobal._startup_cwd)
            case Location():
                the_path = path.path
                return self._normalize(the_path, root=self.root)
            case pl.Path():
                return self._normalize(path, root=self.root)
            case _:
                raise TypeError("Bad type to normalize", path)

    def norm(self, path) -> pl.Path:
        return self.normalize(path)

class _LocatorAccess_m:

    def get(self, key, fallback=Any) -> pl.Path:
        """

        """
        try:
            return self.expand(key, norm=True, strict=True)
        except KeyError as err:
            match fallback:
                case x if x is Any:
                    raise err
                case x:
                    return x

    def access(self, key:Maybe[DKey|str], fallback:Maybe[False|str|DKey]=Any) -> Maybe[Location]:
        """
          convert a *simple* str name of *one* toml location to a path.
          does *not* recursively expand returned paths
          More complex expansion is handled in DKey, or using item access of Locator
        """
        match key:
            case None:
                return None
            case str() if key in self:
                return self._data[key]
            case _ if fallback is False:
                raise KeyError("Key Not found", key)
            case _ if isinstance(fallback, (str, DKey)):
                return self.access(fallback) or fallback
            case _ if fallback is None:
                return None
            case _:
                return None

    def expand(self, key:Maybe[Location|pl.Path|DKey|str], strict=True, norm=True) -> Maybe[pl.Path]:
        """

        """
        coerced = self._coerce_key(key)
        try:
            expanded = self._expand_key(coerced, strict=strict)
        except KeyError as err:
            raise KeyError(err.args[0]) from None

        match expanded:
            case None if strict:
                raise KeyError("Location Not Found", key)
            case None:
                return None
            case x if norm:
                return self.normalize(pl.Path(x))
            case x:
                return pl.Path(x)

    def _coerce_key(self, key:Location|DKey|str|pl.Path) -> FmtStr:
        """ Initial coercion of a key to a format string,
        prior to expanding and converting to a path """
        match key:
            case Location():
                current = key[1:]
            # case str() if key in self:
            #     return self._data[key][1:]
            case DKey():
                current = f"{key:w}"
            case str() if "{" in key:
                current = key
            case str():
                current = f"{{{key}}}"
            case pl.Path():
                current = str(key)
            case _:
                raise TypeError("Can't perform initial coercion of key", key)

        return current

    def _expand_key(self, key:FmtStr, strict=True) -> Maybe[str]:
        """ Givena fmtstr, expand any matching keys until theres nothing more to expand """
        assert(isinstance(key, str))
        memo               = {}
        sources            = defaultdict(list)
        incomplete : deque = deque([(None, key)])
        complete   : deque = deque()

        def key_exp(key, source) -> list:
            if bool(key.prefix):
                yield (None, key.prefix)

            if not bool(key.key):
                return

            match memo.get(key.key, None):
                case None:
                    pass
                case [*xs]:
                    yield from ((source, x) for x in xs)
                    return

            match self.access(key.key, fallback=None):
                case None if strict:
                    raise KeyError(key.key)
                case None:
                    yield (source, key.key)
                case Location() as x if x[1:] in memo:
                    yield from ((source, x) for x in memo[x[1:]])
                case Location() as x:
                    yield (source, x[1:])

            return

        # loop until theres no more changes
        count = 0
        while bool(incomplete):
            source, key = incomplete.pop()
            logging.debug("--(%s): [%s] -> '%s' -> [%s] (%s)",
                          count,
                          ", ".join(x[1] for x in incomplete),
                          key,
                          ",".join(complete),
                          ", ".join(memo.keys()) )
            count += 1

            if source in sources[key] and key in sources[source]:
                raise RecursionError("Recursion", key, source)
            sources[key].append(source)

            match DKeyFormatter.Parse(key):
                case _, []:
                    complete.appendleft(key)
                case _, [x] if not bool(x.key) and bool(x.prefix):
                    complete.appendleft(x.prefix)
                case _, [x] if bool(x.key) and not bool(x.prefix) and x.key not in self:
                    if strict:
                        raise KeyError(x.key)
                    complete.appendleft(format(DKey(key), "w"))
                case _, [*xs]:
                    expansion = [y for x in xs for y in key_exp(x, source=key)]
                    logging.debug("Memo: %s : [%s] -> [%s]", key, "".join(memo.get(key, [])), "".join(x[1] for x in expansion))
                    memo[key] = [x[1] for x in expansion]
                    incomplete.extend(expansion)
        else:
            logging.debug("Complete: %s", complete)
            return "".join(complete)

class JGDVLocator(_LocatorAccess_m, _LocatorUtil_m, PathManip_m):
    """
      A managing context for storing and converting Locations to Paths.
      key=value pairs in [[locations]] toml blocks are integrated into it.

      It expands relative paths according to cwd(),
      (or the cwd at program start if the Location has the earlycwd flag)

      Can be used as a context manager to expand from a temp different root.
      In which case the current global loc store is at JGDVLocator.Current

      Locations are of the form:
      key = "meta/vars::path/to/dir/or/file.ext"

      simple locations can be accessed as attributes.
      eg: locs.temp

      more complex locations, with expansions, are accessed as items:
      locs['{temp}/somewhere']
      will expand 'temp' (if it is a registered location)
      """
    gmark_e = LocationMeta_e
    Current : ClassVar[_LocatorGlobal] = _LocatorGlobal()

    def __init__(self, root:pl.Path):
        self._root    : pl.Path()                 = root.expanduser().resolve()
        self._data    : dict[str, Location]       = dict()
        self._loc_ctx : Maybe[JGDVLocator]      = None
        match self.Current:
            case None:
                _LocatorGlobal.push(self)
            case JGDVLocator():
                pass

    @property
    def root(self):
        """
          the registered root location
        """
        return self._root

    def __repr__(self):
        keys = ", ".join(iter(self))
        return f"<JGDVLocator ({_LocatorGlobal.stacklen()}) : {str(self.root)} : ({keys})>"

    def __getattr__(self, key:str) -> Location:
        """
          retrieve the raw named location
          eg: locs.temp
          """
        if key.startswith("__") or key.endswith("__"):
            raise AttributeError("Location Access Fail", key)

        try:
            return self.access(key, fallback=False)
        except KeyError as err:
            raise AttributeError(err.args[0]) from err

    def __getitem__(self, val:DKey|pl.Path|Location|str) -> pl.Path:
        """
        Get the expanded path of a key or location

        eg: doot.locs['{data}/somewhere']
        or: doot.locs[pl.Path('data/{other}/somewhere')]
        or  doot.locs[Location("dir::>a/{diff}/path"]

        """
        return self.expand(val, strict=False)

    def __contains__(self, key:str|DKey|pl.Path|Location|Self):
        """ Test whether a key is a registered location """
        match key:
            case Location():
                return key in self._data.values()
            case str() | pl.Path():
                return key in self._data
            case _:
                return NotImplemented

    def __iter__(self) -> Generator[str]:
        """ Iterate over the registered location names """
        return iter(self._data.keys())

    def __call__(self, new_root=None) -> JGDVLocator:
        """ Create a copied locations object, with a different root """
        new_obj = JGDVLocator(new_root or self._root)
        return new_obj.update(self)

    def __enter__(self) -> Any:
        """ replaces the global doot.locs with this locations obj,
        and changes the system root to wherever this locations obj uses as root
        """
        _LocatorGlobal.push(self)
        os.chdir(self._root)
        return self.Current

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        """ returns the global state to its original, """
        _LocatorGlobal.pop()
        os.chdir(self.Current._root)
        return False

    def _clear(self):
        self._data.clear()
