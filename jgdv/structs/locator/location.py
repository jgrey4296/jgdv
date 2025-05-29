#!/usr/bin/env python3
"""

"""
# mypy: disable-error-code="attr-defined"
# ruff: noqa: ANN002, ANN003
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
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
from jgdv import Proto
from jgdv.structs.dkey import DKey
from jgdv.mixins.path_manip import PathManip_m
from jgdv.mixins.enum_builders import FlagsBuilder_m
from jgdv.structs.strang import Strang

from jgdv.structs.strang import _interface as StrangAPI # noqa: N812
from jgdv.structs.strang._interface import Strang_p
# ##-- end 1st party imports

from . import _interface as API # noqa: N812
from .processor import LocationProcessor

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
   import enum
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

@Proto(API.Location_p)
class Location(Strang):
    """ A Location is an abstraction higher than a path.

    ie: a path, with metadata.

    Doesn't expand on its own, requires a JGDVLocator store

    It is a Strang subclass, of the form "{meta}+::a/path/location". eg::

        file/clean::.temp/docs/blah.rst

    TODO use annotations to require certain metaflags.
    eg::

        ProtectedLoc = Location['protect']
        Cleanable    = Location['clean']
        FileLoc      = Location['file']

    TODO add an ExpandedLoc subclass that holds the expanded path,
    and removes the need for much of PathManip_m?

    TODO add a ShadowLoc subclass using annotations
    eg::

        BackupTo           = ShadowLoc[root='/vols/BackupSD']
        a_loc              = BackupTo('file::a/b/c.mp3')
        a_loc.path_pair() -> ('/vols/BackupSD/a/b/c.mp3', '~/a/b/c.mp3')

    """
    __slots__              = ()

    _processor : ClassVar  = LocationProcessor()
    _sections  : ClassVar  = API.LocationSections
    Marks      : ClassVar  = API.LocationMeta_e
    Wild       : ClassVar  = API.WildCard_e

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs) # type: ignore[misc]

    def __contains__(self, other:object) -> bool: # type: ignore
        """ Whether a definite artifact is matched by self, an abstract artifact

       | other    ∈ self
       | a/b/c.py ∈ a/b/*.py
       | ________ ∈ a/*/c.py
       | ________ ∈ a/b/c.*
       | ________ ∈ a/*/c.*
       | ________ ∈ **/c.py
       | ________ ∈ a/b ie: self < other
        """
        match other:
            case self.Marks() as x:
                return x in self.data.meta
            case pl.Path() | API.Location_p() if self.Marks.abstract in self.data.meta:
                return self.check_wildcards(other)
            case API.Location_p():
                return self < other
            case _:
                return super().__contains__(other) # type: ignore[misc]

    @override
    def __lt__(self, other:TimeDelta|str|pl.Path|Location) -> bool: # type: ignore[override]
        """ self < path|location
            self < delta : self.modtime < (now - delta)
        """
        match other:
            case TimeDelta() if self.is_concrete():
                return False
            case TimeDelta():
                raise NotImplementedError()
            case _:
                return super().__lt__(str(other)) # type: ignore[misc]

    @property
    def path(self) -> pl.Path: # type: ignore
        return pl.Path(self[1,:])

    @property
    def body_parent(self) -> list[str|API.WildCard_e]:
        if self.Marks.file in self:
            return list(itz.islice(self.words(1), len(self.data.sec_words[1])-1))

        return list(self.words(1))

    @property
    def stem(self) -> Maybe[str|tuple[API.WildCard_e, str]]: # type: ignore
        """ Return the stem, or a tuple describing how it is a wildcard """
        result : Maybe[str|tuple[API.WildCard_e, str]] = None
        if self.Marks.file not in self.data.meta:
            return result

        match self[1,-1]:
            case str() as elem:
                pass
            case _:
                return None

        match elem.split(".")[0]:
            case str() as elem if (wc:=self.Wild.glob) in elem:
                result = (wc, elem)
            case str() as elem if (wc:=self.Wild.select) in elem:
                result = (wc, elem)
            case str() as elem if (wc:=self.Wild.key) in elem:
                result = (wc, elem)
            case str() as elem:
                result = elem
            case _:
                pass

        return result

    @property
    def keys(self) -> set[str]:
        raise NotImplementedError()

    @property
    def key(self) -> Maybe[str|API.Key_p]:
        raise NotImplementedError()

    def ext(self, *, last:bool=False) -> Maybe[str|tuple[API.WildCard_e, str]]: # type: ignore # noqa: PLR0911
        """ return the ext, or a tuple of how it is a wildcard.
        returns nothing if theres no extension,
        returns all suffixes if there are multiple, or just the last if last=True
        """
        if self.Marks.file not in self.data.meta:
            return None

        match self[1,-1]:
            case str() as elem:
                pass
            case _:
                return None

        match elem.rfind(".") if last else elem.find("."):
            case -1:
                return None
            case x:
                pass

        match elem[x:]:
            case ".":
                return None
            case ext if (wc:=API.WildCard_e.glob) in ext:
                return (wc, ext)
            case ext if (wc:=API.WildCard_e.select) in ext:
                return (wc, ext)
            case ext:
                return ext

    def is_concrete(self) -> bool:
        return self.Marks.abstract not in self.data.meta

    def check_wildcards(self, other:pl.Path|API.Location_p) -> bool:  # noqa: PLR0912
        """ Return True if other is within self, accounting for wildcards """
        logging.debug("Checking %s < %s", self, other)
        x            : Any
        other_ext    : Any
        other_parts  : list[str]
        wildcards    : set[str]
        if self.is_concrete():
            return self < other

        match other:
            case pl.Path() as x:
                other_parts  = list(x.parts)
                other_ext    = x.suffix
            case API.Location_p() as x:
                other_parts = other.body_parent
                other_ext = other.ext()

        wildcards = {x.value for x in self.section(1).marks}
        # Compare path up to the file
        for x,y in zip(self.body_parent, other_parts, strict=False):
            match x, y:
                case str(), str() if x == y:
                    pass
                case str(), str() if x not in self.Wild and y not in self.Wild:
                    return False
                case x, _ if self.Wild(x) is self.Wild.rec_glob:
                    break
                case x, str() if x in self.Wild:
                    pass
                case str(), y if y in self.Wild:
                    pass
                case str(), str():
                    pass

        if self.Marks.file not in self.data.meta:
            return True

        logging.debug("%s and %s match on path", self, other)
        # Compare the stem/ext
        match self.stem, other.stem:
            case (xa, ya), (xb, yb) if xa == xb and ya == yb:
                pass
            case (xa, ya), str():
                pass
            case str() as x, str() as y if x == y:
                pass
            case _, _:
                return False

        logging.debug("%s and %s match on stem", self, other)
        match self.ext(), other_ext:
            case None, None:
                pass
            case (xa, ya), (xb, yb) if xa == xb and ya == yb:
                pass
            case (x, y), _:
                pass
            case str() as x, str() as y if x == y:
                pass
            case _, _:
                return False

        logging.debug("%s and %s match", self, other)
        return True
