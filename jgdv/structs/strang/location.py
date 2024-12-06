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
import pathlib as pl
import re
import time
import types
import weakref
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload, NamedTuple, Self,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from pydantic import BaseModel, field_validator, model_validator

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv._abstract.protocols import Buildable_p, Location_p, ProtocolModelMeta
from jgdv.structs.dkey import DKey, DKeyFormatter
from jgdv.mixins.path_manip import PathManip_m
from jgdv.enums.util import FlagsBuilder_m

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from .strang import Strang

class WildCard_e(enum.StrEnum):
    """ Ways a path can have a wildcard. """
    glob       = "*"
    rec_glob   = "**"
    select     = "?"

class LocationMeta_f(FlagsBuilder_m, enum.Flag):
    """ Available metadata attachable to a location """

    abstract     = enum.auto()
    artifact     = enum.auto()
    directory    = enum.auto()
    clean        = enum.auto()
    earlycwd     = enum.auto()
    protect      = enum.auto()
    expand       = enum.auto()
    remote       = enum.auto()
    partial      = enum.auto()

    # Aliases
    file         = artifact
    dir          = directory
    location     = directory

    default      = directory

class Location(Strang, PathManip_m):
    """ A Location is an abstraction higher than a path.
      ie: a path, with metadata.

    Doesn't expand on its own, requires a JGDVLocations store

    A Strang subclass, of {meta}+::a/path/location
    eg: file/clean::.temp/docs/blah.rst

    TODO use annotations to require certain metaflags.
    eg: ProtectedLoc = Location['protect']
        Cleanable    = Location['clean']
        FileLoc      = Location['file']

    TODO add an ExpandedLoc subclass that holds the expanded path,
    and removes the need for much of PathManip_m?

    TODO add a ShadowLoc subclass using annotations
    eg: BackupTo = ShadowLoc[root='/vols/BackupSD']
        a_loc = BackupTo('file::a/b/c.mp3')
        a_loc.path_pair() -> ('/vols/BackupSD/a/b/c.mp3', '~/a/b/c.mp3')
    """
    _subseparator       : ClassVar[str]        = "/"
    _body_types         : ClassVar[Any]        = str|WildCard_e
    mark_e              : ClassVar[enum.Enum]  = LocationMeta_f
    wild_e              : ClassVar[enum.Enum]  = WildCard_e

    def __init__(self):
        super().__init__()
        self.flags               : LocationMeta_f  = LocationMeta_f.default


    @classmethod
    def pre_process(cls, data):
        match data:
            case pl.Path():
                data = f"dir::{data}"
            case _:
                pass
        return super().pre_process(data)

    def _post_process(self):
        max_body        = len(self._body)
        self._body_objs = [None for x in range(max_body)]
        self.flags      = LocationMeta_f.build(self.group)

        parent_bound    = max(len(self._body) - 0, 0)

        for i, elem in enumerate(self.body()):
            match elem:
                case WildCard_e.glob:
                    self.flags |= LocationMeta_f.abstract
                    self._body_objs[i] = WildCard_e.glob
                case WildCard_e.rec_glob:
                    self.flags |= LocationMeta_f.abstract
                    self._body_objs[i] = WildCard_e.rec_glob
                case WildCard_e.select:
                    self.flags |= LocationMeta_f.abstract
                    self._body_objs[i] = WildCard_e.select
        else:
            match self.stem:
                case (WildCard_e(), _):
                    self.flags |= LocationMeta_f.abstract
                case _:
                    pass

            match self.ext:
                case (WildCard_e(), _):
                    self.flags |= LocationMeta_f.abstract
                case _:
                    pass

        return self

    def __contains__(self, other:LocationMeta_f|Location|pl.Path) -> bool:
        """ TODO whether a definite artifact is matched by self, an abstract artifact
          a/b/c.py ∈ a/b/*.py
          ________ ∈ a/*/c.py
          ________ ∈ a/b/c.*
          ________ ∈ a/*/c.*
          ________ ∈ **/c.py

        """
        match other:
            case LocationMeta_f():
                return self.check(other)
            case Location():
                path = other.path
            case pl.Path():
                path = other
            case _:
                return False

        if not self.check(LocationMeta_f.abstract):
            return False

        for x,y in zip(self.path.parent.parts, path.parent.parts):
            if x == REC_GLOB or y == REC_GLOB:
                break
            if x == GLOB or y == GLOB:
                continue
            if x != y:
                return False

        _, abs_stem, abs_suff = self.abstracts
        suffix      = abs_suff or self.path.suffix == path.suffix
        stem        = abs_stem or self.path.stem == path.stem
        return  suffix and stem

    def is_concrete(self) -> bool:
        return LocationMeta_f.abstract not in self.flags

    def check(self, meta:Location.mark_e) -> bool:
        """ return True if this location has any of the test flags """
        return bool(self.meta & meta)

    @ftz.cached_property
    def path(self) -> pl.Path:
        return pl.Path(self[1:])

    @ftz.cached_property
    def stem(self) -> str|tuple[WildCard_e, str]:
        """ Return the stem, or a tuple describing how it is a wildcard """
        elem = self[1:-1].split(".")[0]
        if (wc:=WildCard_e.glob) in elem:
            return (wc, elem)
        if (wc:=WildCard_e.select) in elem:
            return (wc, elem)
        return elem

    @ftz.cache
    def ext(self, *, last=False) -> None|str|tuple[WildCard_e, str]:
        """ return the ext, or a tuple of how it is a wildcard.
        returns nothing if theres no extension,
        returns all suffixes if there are multiple, or just the last if last=True
        """
        elem = self[1:-1]
        match elem.rfind(".") if last else elem.find("."):
            case -1:
                return None
            case x:
                pass

        match elem[x:]:
            case ".":
                return None
            case ext if (wc:=WildCard_e.glob) in ext:
                return (wc, ext)
            case ext if (wc:=WildCard_e.select) in ext:
                return (wc, ext)
            case ext:
                return ext
