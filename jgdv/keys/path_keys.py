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


class JGDVPathSimpleKey(JGDVSimpleKey):
    """ A Key that always expands as a path """

    def expand(self, spec=None, state=None, *, rec=False, insist=False, chain:list[JGDVBaseKey]=None, on_fail=Any, locs=None, **kwargs):
        return str(self.to_path(spec, state, chain=chain, on_fail=on_fail, locs=locs))

    def __repr__(self):
        return "<JGDVPathSimpleKey: {}>".format(str(self))

    def __call__(self, spec, state):
        """ Expand the key using the registered expansion hint """
        match getattr(self, EXPANSION_HINT, False):
            case False:
                return self.to_path(spec, state)
            case {"expansion": "str", "kwargs": kwargs}:
                return self.expand(spec, state, **kwargs)
            case {"expansion": "path", "kwargs": kwargs}:
                return self.to_path(spec, state, **kwargs)
            case {"expansion": "redirect"}:
                return self.redirect(spec)
            case {"expansion": "redirect_multi"}:
                return self.redirect_multi(spec)
            case x:
                raise doot.errors.DootKeyError("Key Called with Bad Key Expansion Type", self, x)


class JGDVPathMultiKey(JGDVMultiKey):
    """ A MultiKey that always expands as a path """

    def expand(self, spec=None, state=None, *, rec=False, insist=False, chain:list[JGDVBaseKey]=None, on_fail=Any, locs=None, **kwargs):
        return str(self.to_path(spec, state, chain=chain, on_fail=on_fail, locs=locs))

    def __repr__(self):
        return "<JGDVPathMultiKey: {}>".format(str(self))

    def __call__(self, spec, state):
        """ Expand the key using the registered expansion hint """
        match getattr(self, EXPANSION_HINT, False):
            case False:
                return self.to_path(spec, state)
            case {"expansion": "str", "kwargs": kwargs}:
                return self.expand(spec, state, **kwargs)
            case {"expansion": "path", "kwargs": kwargs}:
                return self.to_path(spec, state, **kwargs)
            case {"expansion": "redirect"}:
                return self.redirect(spec)
            case {"expansion": "redirect_multi"}:
                return self.redirect_multi(spec)
            case x:
                raise doot.errors.DootKeyError("Key Called with Bad Key Expansion Type", self, x)
