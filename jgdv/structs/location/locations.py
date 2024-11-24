#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import abc
import logging as logmod
import pathlib as pl
from copy import deepcopy
from dataclasses import InitVar, dataclass, field, replace
from re import Pattern
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar, Self,
                    Generator, cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref
import functools as ftz

##-- end imports

##-- logging
logging = logmod.getLogger(__name__)
# If CLI:
# logging = logmod.root
# logging.setLevel(logmod.NOTSET)
##-- end logging

import os
import re
import tomlguard
from jgdv.structs.location.errors import DirAbsent, LocationExpansionError, LocationError
from jgdv.structs.location.location import Location, LocationMeta_f
from jgdv.structs.dkey import MultiDKey, NonDKey, SingleDKey, DKey, DKeyFormatter
from jgdv.mixins.path_manip import PathManip_m

KEY_PAT        = "{(.+?)}"
MAX_EXPANSIONS = 10

class _LocationsGlobal:

    _global_locs : ClassVar[list["JGDVLocations"]] = []

    @staticmethod
    def peek() -> None|"JGDVLocations":
        match _LocationsGlobal._global_locs:
            case []:
                return None
            case [*_, x]:
                return x

    @staticmethod
    def push(locs):
        _LocationsGlobal._global_locs.append(locs)

    @staticmethod
    def pop() -> None|"JGDVLocations":
        match _LocationsGlobal._global_locs:
            case []:
                return None
            case [*xs, x]:
                _LocationsGlobal._global_locs = xs
                return x

class JGDVLocations(PathManip_m):
    """
      A Single point of truth for task access to locations.
      key=value pairs in [[locations]] toml blocks are integrated into it.

      it expands relative paths according to cwd(),
      but can be used as a context manager to expand from a temp different root

      location designations are of the form:
      key = 'location/subdirectory/file'
      simple locations can be accessed as attributes: locs.temp

      more complex locations, with expansions, are accessed as items:
      locs['{temp}/somewhere']
      will expand 'temp' (if it is a registered location)
      """
    locmeta = LocationMeta_f

    @staticmethod
    def _global_(self):
        return _LocationsGlobal.peek()

    def __init__(self, root:pl.Path):
        self._root    : pl.Path()               = root.expanduser().resolve()
        self._data    : dict[str, Location]     = dict()
        self._loc_ctx : None|JGDVLocations      = None
        match _LocationsGlobal.peek():
            case None:
                _LocationsGlobal.push(self)

    def __repr__(self):
        keys = ", ".join(iter(self))
        return f"<JGDVLocations : {str(self.root)} : ({keys})>"

    def __getattr__(self, key:str) -> pl.Path:
        """
          locs.simplename -> normalized expansion
          where 'simplename' has been registered via toml

          delegates to __getitem__
          eg: locs.temp
          """
        if key.startswith("__") and key.endswith("__"):
            return None

        return self.normalize(self.get(key, fallback=False))

    def __getitem__(self, val:pl.Path|str) -> pl.Path:
        """
          doot.locs['{data}/somewhere']
          or doot.locs[pl.Path('data/other/somewhere')]

          A public utility method to easily use toml loaded paths
          expands explicit keys in the string or path

        """
        match val: # initial coercion
            case DKey() if 0 < len(val.keys()):
                raise TypeError("Expand Multi Keys directly", val)
            case DKey():
                current = self.get(val)
            case pl.Path():
                current = str(val)
            case str():
                current = val

        last          = None
        expanded_keys = set()
        while current != last:
            last = current
            match DKeyFormatter.Parse(current):
                case _, []:
                    current = str(current)
                case _, [*xs] if bool(conflict:=expanded_keys & {x.key for x in xs}):
                    raise LocationExpansionError("Location Expansion recursion detected",val, conflict)
                case _, [*xs]:
                    expanded_keys.update(x.key for x in xs)
                    expanded = {x.key : self.get(x.key, fallback=False) for x in xs}
                    current = current.format_map(expanded)

        assert(current is not None)
        return self.normalize(pl.Path(current))

    def __contains__(self, key:str|DKey|pl.Path|Location|Self):
        """ Test whether a key is a registered location """
        match key:
            case JGDVLocations():
                return False
            case Location():
                return False
            case str() | pl.Path():
                return key in self._data

    def __iter__(self) -> Generator[str]:
        """ Iterate over the registered location names """
        return iter(self._data.keys())

    def __call__(self, new_root=None) -> Self:
        """ Create a copied locations object, with a different root """
        new_obj = JGDVLocations(new_root or self._root)
        return new_obj.update(self)

    def __enter__(self) -> Any:
        """ replaces the global doot.locs with this locations obj,
        and changes the system root to wherever this locations obj uses as root
        """
        _LocationsGlobal.push(self)
        os.chdir(self._root)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        """ returns the global state to its original, """
        _LocationsGlobal.pop()
        os.chdir(_LocationsGlobal.peek()._root)
        return False

    def get(self, key:None|DKey|str, fallback:None|False|str|pl.Path=Any) -> None|pl.Path:
        """
          convert a *simple* str name of *one* toml location to a path.
          does *not* recursively expand returned paths
          More complex expansion is handled in DKey, or using item access of Locations
        """
        match key:
            case None:
                return None
            case str() if key in self._data:
                return self._data[key].path
            case _ if fallback is False:
                raise LocationError("Key Not found", key)
            case _ if isinstance(fallback, (str, pl.Path)):
                return self.get(fallback)
            case _ if fallback is None:
                return None
            case DKey():
                return pl.Path(f"{key:w}")
            case _:
                return pl.Path(key)

    def normalize(self, path:pl.Path, symlinks:bool=False) -> pl.Path:
        """
          Expand a path to be absolute, taking into account the set doot root.
          resolves symlinks unless symlinks=True
        """
        return self._normalize(path, root=self.root)

    def metacheck(self, key:str|DKey, meta:LocationMeta_f) -> bool:
        """ return True if key provided has the applicable meta flags """
        match key:
            case NonDKey():
                return False
            case DKey() if key in self._data:
                return self._data[key].check(meta)
            case MultiDKey():
                 for k in key:
                     if k not in self._data:
                         continue
                     if self._data[k].check(meta):
                         return True
            case str():
                return self.metacheck(DKey(key, implicit=True), meta)
        return False

    @property
    def root(self):
        """
          the registered root location
        """
        return self._root

    def update(self, extra:dict|tomlguard.TomlGuard|Location|JGDVLocations, strict=True) -> Self:
        """
          Update the registered locations with a dict, tomlguard, or other dootlocations obj.
        """
        match extra: # unwrap to just a dict
            case dict():
                pass
            case Location():
                pass
            case tomlguard.TomlGuard():
                return self.update(extra._table(), strict=strict)
            case JGDVLocations():
                return self.update(extra._data, strict=strict)
            case _:
                raise LocationError("Tried to update locations with unknown type", extra)

        raw          = dict(self._data.items())
        base_keys    = set(raw.keys())
        new_keys     = set(extra.keys())
        conflicts    = (base_keys & new_keys)
        if strict and bool(conflicts):
            raise LocationError("Strict Location Update conflicts", conflicts)

        for k,v in extra.items():
            match Location.build(v, key=k):
                case Location() as l:
                    raw[l.key] = l
                case _:
                    raise LocationError("Couldn't build a Location", k, v)

        logging.debug("Registered New Locations: %s", ", ".join(new_keys))
        self._data = raw
        return self

    def registered(self, *values, task="doot", strict=True) -> set:
        """ Ensure the values passed in are registered locations,
          error with DirAbsent if they aren't
        """
        missing = set(x for x in values if x not in self)

        if strict and bool(missing):
            raise DirAbsent("Ensured Locations are missing for %s : %s", task, missing)

        return missing

    def _clear(self):
        self._data.clear()
