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
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

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
from jgdv.errors import DirAbsent, LocationExpansionError, LocationError
from jgdv.mixins.path_manip import PathManip_m
from jgdv.enums.location_meta import LocationMeta
from jgdv.keys import JGDVKey

KEY_PAT        = jgdv.constants.patterns.KEY_PATTERN
MAX_EXPANSIONS = jgdv.constants.patterns.MAX_KEY_EXPANSIONS

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
    locmeta = LocationMeta

    def __init__(self, root:Pl.Path):
        self._root    : pl.Path()               = root.expanduser().absolute()
        self._data    : dict[str, TomlLocation] = dict()
        self._loc_ctx : None|JGDVLocations      = None

    def __repr__(self):
        keys = ", ".join(iter(self))
        return f"<JGDVLocations : {str(self.root)} : ({keys})>"

    def __getattr__(self, key) -> pl.Path:
        """
          get a location by name from loaded toml
          delegates to __getitem__
          eg: locs.temp
          """
        if key == "__self__":
            return None
        return self[JGDVKey.build(key, strict=True)]

    def __getitem__(self, val:str|JGDVKey|pl.Path|JGDVArtifact) -> pl.Path:
        """
          eg: jgdv.locs['{data}/somewhere']
          A public utility method to easily convert paths.
          delegates to JGDVKey's path expansion

          Get a location using item access for extending a stored path.
          eg: locs['{temp}/imgs/blah.jpg']
        """
        match JGDVKey.build(val, explicit=True):
            case JGDVNonKey() as key:
                return key.to_path(locs=self)
            case JGDVSimpleKey() as key:
                return key.to_path(locs=self)
            case JGDVMultiKey() as key:
                return key.to_path(locs=self)
            case _:
                raise LocationExpansionError("Unrecognized location expansion argument", val)

    def __contains__(self, key:str|JGDVKey|pl.Path|JGDVArtifact):
        """ Test whether a key is a registered location """
        return key in self._data

    def __iter__(self) -> Generator[str]:
        """ Iterate over the registered location names """
        return iter(self._data.keys())

    def __call__(self, new_root=None) -> Self:
        """ Create a copied locations object, with a different root """
        new_obj = JGDVLocations(new_root or self._root)
        return new_obj.update(self)

    def __enter__(self) -> Any:
        """ replaces the global jgdv.locs with this locations obj,
        and changes the system root to wherever this locations obj uses as root
        """
        self._loc_ctx = jgdv.locs
        jgdv.locs = self
        os.chdir(jgdv.locs._root)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        """ returns the global state to its original, """
        assert(self._loc_ctx is not None)
        jgdv.locs     = self._loc_ctx
        os.chdir(jgdv.locs._root)
        self._loc_ctx = None
        return False

    def get(self, key:JGDVSimpleKey|str, on_fail:None|str|pl.Path=Any) -> None|pl.Path:
        """
          convert a *simple* key of one value to a path.
          does *not* recursively expand returned paths
          More complex expansion is handled in JGDVKey and subclasses
        """
        assert(isinstance(key,(JGDVSimpleKey,str))), (str(key), type(key))
        match key:
            case JGDVNonKey():
                return pl.Path(key.form)
            case str() | JGDVSimpleKey() if key in self._data:
                return self._data[key].base
            case _ if on_fail is None:
                return None
            case _ if on_fail != Any:
                return self.get(on_fail)
            case JGDVSimpleKey():
                return pl.Path(key.form)
            case _:
                return pl.Path(key)

    def normalize(self, path:pl.Path, symlinks:bool=False) -> pl.Path:
        """
          Expand a path to be absolute, taking into account the set jgdv root.
          resolves symlinks unless symlinks=True
        """
        return self._normalize(path, root=self.root)

    def metacheck(self, key:str|JGDVKey, meta:LocationMeta) -> bool:
        """ check if any key provided has the applicable meta flags """
        match key:
            case JGDVNonKey():
                return False
            case JGDVSimpleKey() if key in self._data:
                return self._data[key].check(meta)
            case JGDVMultiKey():
                 for k in JGDVKey.build(key):
                     if k not in self._data:
                         continue
                     if self._data[k].check(meta):
                         return True
            case str():
                return self.metacheck(JGDVKey.build(key), meta)
        return False

    @property
    def root(self):
        """
          the registered root location
        """
        return self._root

    def update(self, extra:dict|TomlGuard|JGDVLocations, strict=True) -> Self:
        """
          Update the registered locations with a dict, tomlguard, or other jgdvlocations obj.
        """
        match extra: # unwrap to just a dict
            case dict():
                pass
            case tomlguard.TomlGuard():
                return self.update(extra._table())
            case JGDVLocations():
                return self.update(extra._data)
            case _:
                raise jgdv.errors.LocationError("Tried to update locations with unknown type: %s", extra)

        raw          = dict(self._data.items())
        base_keys    = set(raw.keys())
        new_keys     = set()
        for k,v in extra.items():
            match TomlLocation.build(k, v):
                case _ if k in new_keys and v != raw[k]:
                    raise LocationError("Duplicated, non-matching Key", k)
                case _ if k in base_keys:
                    logging.debug("Skipping Location update of: %s", k)
                    pass
                case TomlLocation() as l if l.check(LocationMeta.normOnLoad):
                    raw[l.key] = TomlLocation.build(k, v, base=self.normalize(l.base))
                    new_keys.add(l.key)
                case TomlLocation() as l:
                    raw[l.key] = l
                    new_keys.add(l.key)
                case _:
                    raise LocationError("Couldn't build a TomlLocation for: (%s : %s)", k, v)

        logging.debug("Registered New Locations: %s", ", ".join(new_keys))
        self._data = raw
        return self

    def ensure(self, *values, task="jgdv"):
        """ Ensure the values passed in are registered locations,
          error with DirAbsent if they aren't
        """
        missing = set(x for x in values if x not in self)

        if bool(missing):
            raise DirAbsent("Ensured Locations are missing for %s : %s", task, missing)

    def _clear(self):
        self._data = tomlguard.TomlGuard()
