#!/usr/bin/env python3
"""
Central store of Locations,
which expands paths and can hook into the dkey system

For a registered location ("blah": "ex/dir", "bloo": "file:>a/b/c.txt"):
Locator.blah            -> {cwd}/ex/dir
Locator['{blah}']       -> {cwd}/ex/dir
Locator['{blah}/blee']  -> {cwd}/ex/dir/blee

Locator.bloo            -> {cwd}/a/b/c.txt
Locator['{bloo}']       -> {cwd}/a/b/c.txt
Locator['{bloo}/blee']  -> Error

Locator[{blah}/{bloo}'] -> {cwd}/ex/dir/a/b/c.txt

Locator has 3 main access methods:
Locator.get    : like dict.get
Locator.access : Access the Location object
Locator.expand : Expand the location(s) into a path

Shorthands:
Locator.KEY -    > Locator.access
Locator["{KEY}"] > Locator.expand

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
from re import Pattern
from collections import defaultdict, deque
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Mixin, Proto
from jgdv.mixins.path_manip import PathManip_m
from jgdv.structs.chainguard import ChainGuard
from jgdv.structs.dkey import DKey, MultiDKey, NonDKey, SingleDKey, ExpInst_d

from .location import Location
from .errors import DirAbsent, LocationError, LocationExpansionError
from ._interface import Location_p, Locator_p, LocationMeta_e
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

if TYPE_CHECKING:
   from jgdv import Maybe, Stack, Queue
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   type FmtStr      = str
   type JGDVLocator = Any
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Vars

##--| Body

class SoftFailMultiDKey(MultiDKey["soft.fail"], multi=True):

    def exp_pre_lookup_h(self, sources, opts) -> list:
        """ Expands subkeys, to be merged into the main key"""
        targets = []
        for key in self.keys():
            targets.append([ExpInst_d(val=key, fallback=f"{key:w}")] )
        else:
            if not bool(targets):
                targets.append([ExpInst_d(val=f"{self}"),
                                ExpInst_d(val=f"{self}", literal=True)])
            return targets

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
    def peek() -> None|JGDVLocator:
        match _LocatorGlobal._global_locs:
            case []:
                return None
            case [*_, x]:
                return x

    @staticmethod
    def push(locs) -> None:
        _LocatorGlobal._global_locs.append(locs)

    @staticmethod
    def pop() -> None|JGDVLocator:
        match _LocatorGlobal._global_locs:
            case []:
                return None
            case [*xs, x]:
                _LocatorGlobal._global_locs = xs
                return x

    def __get__(self, obj, objtype=None) -> JGDVLocator:
        """ use the descriptor protocol to make a pseudo static-variable
        https://docs.python.org/3/howto/descriptor.html
        """
        return _LocatorGlobal.peek()

class _LocatorUtil_m:  # noqa: N801

    def update(self, extra:dict|ChainGuard|Location|JGDVLocator, *, strict=True) -> Self:
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
                msg = "Tried to update locations with unknown type"
                raise TypeError(msg, extra)

        raw          = dict(self._data.items())
        base_keys    = set(raw.keys())
        new_keys     = set(extra.keys())
        conflicts    = (base_keys & new_keys)
        if strict and bool(conflicts):
            msg = "Strict Location Update conflicts"
            raise LocationError(msg, conflicts)

        for k,v in extra.items():
            try:
                raw[k] = Location(v)
            except KeyError:
                msg = "Couldn't build a Location"
                raise LocationError(msg, k, v) from None

        logging.debug("Registered New Locations: %s", ", ".join(new_keys))
        self._data = raw
        return self

    def metacheck(self, key:str|DKey, *meta:LocationMeta_e) -> bool:
        """ return True if key provided has any of the metadata flags """
        match key:
            case NonDKey():
                return False
            case DKey() if key in self._data:
                data = self._data[key]
                return any(x in data for x in meta)
            case MultiDKey():
                 for k in key:
                     if k not in self._data:
                         continue
                     data = self._data[key]
                     if not any(x in data for x in meta):
                         return False
            case str():
                return self.metacheck(DKey(key, implicit=True), meta)
        return False

    def registered(self, *values, task="doot", strict=True) -> set:
        """ Ensure the values passed in are registered locations,
          error with DirAbsent if they aren't
        """
        missing = {x for x in values if x not in self}

        if strict and bool(missing):
            msg = "Ensured Locations are missing for %s : %s"
            raise DirAbsent(msg, task, missing)

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
                msg = "Bad type to normalize"
                raise TypeError(msg, path)

    def norm(self, path) -> pl.Path:
        return self.normalize(path)

    def pre_expand(self) -> None:
        """
        Called after updating the Locator,
        it pre-expands any registered keys found in registered Locations
        """
        # TODO
        pass

class _LocatorAccess_m:  # noqa: N801

    def get(self, key, fallback:Maybe[pl.Path]=None) -> Maybe[pl.Path]:
        """
        Behavinng like a dict.get,
        uses Locator.access, but coerces to an unexpanded path

        raises a KeyError when fallback is None
        """
        match fallback:
            case pl.Path() | None:
                pass
            case str() as x:
                fallback =  pl.Path(x)
            case x:
                msg = "Fallback needs to be a path"
                raise TypeError(msg, x)

        match self.access(key):
            case Location() as x:
                return x.path
            case None if fallback is None:
                msg = "Failed to Access"
                raise KeyError(msg, key)
            case None if fallback:
                return fallback
            case None:
                return None

    def access(self, key:DKey|str) -> Maybe[Location]:
        """
          Access the registered Location associated with 'key'
        """
        match key:
            case str() if key in self:
                return self._data[key]
            case _:
                return None

    def expand(self, key:Location|pl.Path|DKey|str, strict=True, norm=True) -> Maybe[pl.Path]:
        """
        Access the locations mentioned in 'key',
        join them together, and normalize it
        """
        coerced : DKey = self._coerce_key(key, strict=strict)
        match coerced.expand(self):
            case None if strict:
                msg = "Strict Expansion of Location failed"
                raise KeyError(msg, key)
            case None:
                return None
            case pl.Path() as x if norm:
                return self.normalize(x)
            case pl.Path() as x:
                return x
            case x:
                msg = "Unknown Response When Expanding Location"
                raise TypeError(msg, key, x)

    def _coerce_key(self, key:Location|DKey|str|pl.Path, *, strict=False) -> DKey:
        """ Coerces a key to a MultiDKey for expansion using DKey's expansion mechanism,
        using self as the source
        """
        match key:
            case Location():
                current = key[1:]
            case DKey():
                current = f"{key:w}"
            case str():
                current = key
            case pl.Path():
                current = str(key)
            case _:
                msg = "Can't perform initial coercion of key"
                raise TypeError(msg, key)

        match strict:
            case False:
                return DKey(current, ctor=pl.Path, mark="soft.fail")
            case True:
                return DKey(current, ctor=pl.Path, mark=DKey.Mark.MULTI)

##--|

@Proto(Locator_p)
@Mixin(_LocatorAccess_m, _LocatorUtil_m, PathManip_m)
class JGDVLocator:
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
        self._data    : dict[str, Location]       = {}
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
        return f"<JGDVLocator ({_LocatorGlobal.stacklen()}) : {self.root!s} : ({keys})>"

    def __getattr__(self, key:str) -> Location:
        """
          retrieve the raw named location
          eg: locs.temp
          """
        if key.startswith("__") or key.endswith("__"):
            msg = "Location Access Fail"
            raise AttributeError(msg, key)

        match self.access(key):
            case Location() as x:
                return x
            case _:
                raise AttributeError(key)

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

    def __bool__(self) -> bool:
        return bool(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Generator[str]:
        """ Iterate over the registered location names """
        return iter(self._data.keys())

    def __call__(self, new_root=None) -> JGDVLocator:
        """ Create a copied locations object, with a different root """
        new_obj = JGDVLocator(new_root or self._root)
        return new_obj.update(self)

    def __enter__(self) -> JGDVLocator:
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
