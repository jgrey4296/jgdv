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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from pydantic import BaseModel, field_validator, model_validator

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Mixin
from jgdv._abstract.protocols import Buildable_p, Location_p, ProtocolModelMeta
from jgdv.structs.dkey import DKey, DKeyFormatter
from jgdv.mixins.path_manip import PathManip_m
from jgdv.mixins.enum_builders import FlagsBuilder_m
from jgdv.structs.strang import Strang
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
TimeDelta = datetime.timedelta
if TYPE_CHECKING:
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class WildCard_e(enum.StrEnum):
    """ Ways a path can have a wildcard. """
    glob       = "*"
    rec_glob   = "**"
    select     = "?"
    key        = "{"

class LocationMeta_e(enum.StrEnum):
    """ Available metadata attachable to a location """

    location     = "location"
    directory    = "directory"
    file         = "file"

    abstract     = "abstract"
    artifact     = "artifact"
    clean        = "clean"
    earlycwd     = "earlycwd"
    protect      = "protect"
    expand       = "expand"
    remote       = "remote"
    partial      = "partial"

    # Aliases
    dir          = directory
    loc          = location

    default      = loc

@Mixin(PathManip_m)
class Location(Strang):
    """ A Location is an abstraction higher than a path.
      ie: a path, with metadata.

    Doesn't expand on its own, requires a JGDVLocator store

    A Strang subclass, of {meta}+::a/path/location
    eg: file/clean::.temp/docs/blah.rst

    TODO use annotations to require certain metaflags.
    eg: ProtectedLoc = Location['protect']
        Cleanable    = Location['clean']
        FileLoc      = Location['file']

    TODO add an ExpandedLoc subclass that holds the expanded path,
    and removes the need for much of PathManip_m?

    TODO add a ShadowLoc subclass using annotations
    eg: BackupTo                               = ShadowLoc[root='/vols/BackupSD']
        a_loc                                  = BackupTo('file::a/b/c.mp3')
        a_loc.path_pair() -> ('/vols/BackupSD/a/b/c.mp3', '~/a/b/c.mp3')
    """
    _separator          : ClassVar[str]        = "::>"
    _subseparator       : ClassVar[str]        = "/"
    _body_types         : ClassVar[Any]        = str|WildCard_e
    gmark_e             : ClassVar[enum.Enum]  = LocationMeta_e
    bmark_e             : ClassVar[enum.Enum]  = WildCard_e

    @classmethod
    def pre_process(cls, data:str|pl.Path, *, strict=False):
        match data:
            case Strang():
                pass
            case pl.Path() if not strict and data.suffix != "":
                data = f"{cls.gmark_e.file}{cls._separator}{data}"
            case pl.Path() if not strict:
                data = f"{cls.gmark_e.default}{cls._separator}{data}"
            case str() if cls._separator not in data:
                return cls.pre_process(pl.Path(data), strict=strict)
            case str():
                pass
            case _:
                pass
        return super().pre_process(data, strict=strict)

    def _post_process(self):
        max_body         = len(self._body)
        self._body_meta  = [None for x in range(max_body)]
        self._group_meta = set()

        # Group metadata
        for elem in self.group:
            self._group_meta.add(self.gmark_e[elem])

        # Body wildycards
        for i, elem in enumerate(self.body()):
            match elem:
                case self.bmark_e.glob:
                    self._group_meta.add(self.gmark_e.abstract)
                    self._body_meta[i] = self.bmark_e.glob
                case self.bmark_e.rec_glob:
                    self._group_meta.add(self.gmark_e.abstract)
                    self._body_meta[i] = self.bmark_e.rec_glob
                case self.bmark_e.select:
                    self._group_meta.add(self.gmark_e.abstract)
                    self._body_meta[i] = self.bmark_e.select
                case str() if self.bmark_e.key in elem:
                    self._group_meta.add(self.gmark_e.abstract)
                    self._body_meta[i] = self.bmark_e.key
        else:
            match self.stem:
                case (self.bmark_e(), _):
                    self._group_meta.add(self.gmark_e.abstract)
                    self._group_meta.add(self.gmark_e.expand)
                case _:
                    pass

            match self.ext():
                case (self.bmark_e(), _):
                    self._group_meta.add(self.gmark_e.abstract)
                case _:
                    pass

        return self

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._group_meta = None

    def __repr__(self):
        body = self[1:]
        cls = self.__class__.__name__
        return f"<{cls}: {self[0:]}{self._separator}{body}>"

    def __contains__(self, other:Location.gmark_e|Location.bmark_e|Location|pl.Path) -> bool:
        """ whether a definite artifact is matched by self, an abstract artifact
          other    ∈ self
          a/b/c.py ∈ a/b/*.py
          ________ ∈ a/*/c.py
          ________ ∈ a/b/c.*
          ________ ∈ a/*/c.*
          ________ ∈ **/c.py
          ________ ∈ a/b ie: self < other

        """
        match other:
            case self.gmark_e():
                return super().__contains__(other)
            case Location() if self.gmark_e.abstract in self._group_meta:
                return self.check_wildcards(other)
            case Location():
                return self < other
            case pl.Path() | str():
                return self.check_wildcards(Location(other))
            case _:
                return super().__contains__(other)

    def is_concrete(self) -> bool:
        return self.gmark_e.abstract not in self._group_meta

    def check_wildcards(self, other:Location) -> bool:
        """  """
        logging.debug("Checking %s < %s", self, other)
        if self.is_concrete():
            return self < other

        # Compare path
        for x,y in zip(self.body_parent, other.body_parent, strict=False):
            match x, y:
                case _, _ if x == y:
                    pass
                case self.bmark_e.rec_glob, _:
                    break
                case self.bmark_e(), str():
                    pass
                case str(), self.bmark_e():
                    pass
                case str(), str():
                    return False

        if self.gmark_e.file not in self._group_meta:
            return True

        logging.debug("%s and %s match on path", self, other)
        # Compare the stem/ext
        match self.stem, other.stem:
            case x, y if x == y:
                pass
            case (xa, ya), (xb, yb) if xa == xb and ya == yb:
                pass
            case (xa, ya), str():
                pass
            case _, _:
                return False

        logging.debug("%s and %s match on stem", self, other)
        match self.ext(), other.ext():
            case None, None:
                pass
            case x, y if x == y:
                pass
            case (xa, ya), (xb, yb) if xa == xb and ya == yb:
                pass
            case (x, y), _:
                pass
            case _, _:
                return False

        logging.debug("%s and %s match", self, other)
        return True

    @ftz.cached_property
    def path(self) -> pl.Path:
        return pl.Path(self[1:])

    @ftz.cached_property
    def body_parent(self) -> list[Location._body_type]:
        if self.gmark_e.file in self:
            return self.body()[:-1]

        return self.body()

    @ftz.cached_property
    def stem(self) -> Maybe[str|tuple[Location.bmark_e, str]]:
        """ Return the stem, or a tuple describing how it is a wildcard """
        if self.gmark_e.file not in self._group_meta:
            return None

        elem = self[1:-1].split(".")[0]
        if elem == "":
            return None
        if (wc:=self.bmark_e.glob) in elem:
            return (wc, elem)
        if (wc:=self.bmark_e.select) in elem:
            return (wc, elem)
        if (wc:=self.bmark_e.key) in elem:
            return (wc, elem)

        return elem

    def ext(self, *, last=False) -> Maybe[str|tuple[Location.bmark_e, str]]:
        """ return the ext, or a tuple of how it is a wildcard.
        returns nothing if theres no extension,
        returns all suffixes if there are multiple, or just the last if last=True
        """
        if self.gmark_e.file not in self._group_meta:
            return None

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

    @ftz.cached_property
    def keys(self):
        raise NotImplementedError()

    def __lt__(self, other:TimeDelta|str|pl.Path|Location) -> bool:
        """ self < path|location
            self < delta : self.modtime < (now - delta)
        """
        match other:
            case TimeDelta() if self.is_concrete():
                pass
            case TimeDelta():
                raise NotImplementedError()
            case _:
                return super().__lt__(other)
