#!/usr/bin/env python2
"""


"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import string
import time
import types
import weakref
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload, Self,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from pydantic import BaseModel, Field, field_validator, model_validator
from tomlguard import TomlGuard

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv._abstract.protocols import Key_p, SpecStruct_p, Buildable_p
from jgdv.structs.strang import CodeReference
from jgdv.structs.dkey.dkey import DKey, REDIRECT_SUFFIX, CONV_SEP, DKeyMark_e
from jgdv.structs.dkey.formatter import DKeyFormatter
from jgdv.structs.dkey.mixins import DKeyFormatting_m, DKeyExpansion_m, identity
from jgdv.structs.dkey.base import DKeyBase
from jgdv.structs.dkey.core import SingleDKey, MultiDKey, NonDKey

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

KEY_PATTERN                                 = "{(.+?)}"
MAX_KEY_EXPANSIONS                          = 10

PATTERN         : Final[re.Pattern]         = re.compile(KEY_PATTERN)
FAIL_PATTERN    : Final[re.Pattern]         = re.compile("[^a-zA-Z_{}/0-9-]")
FMT_PATTERN     : Final[re.Pattern]         = re.compile("[wdi]+")
EXPANSION_HINT  : Final[str]                = "_doot_expansion_hint"
HELP_HINT       : Final[str]                = "_doot_help_hint"
FORMAT_SEP      : Final[str]                = ":"
CHECKTYPE       : TypeAlias                 = None|type|types.GenericAlias|types.UnionType
CWD_MARKER      : Final[str]                = "__cwd"


class StrDKey(SingleDKey, mark=DKeyMark_e.STR, tparam="s"):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._expansion_type  = str
        self._typecheck = str

class RedirectionDKey(SingleDKey, mark=DKeyMark_e.REDIRECT, tparam="R"):
    """
      A Key for getting a redirected key.
      eg: RedirectionDKey(key_) -> SingleDKey(value)

      re_mark :
    """

    def __init__(self, data, multi=False, re_mark=None, **kwargs):
        kwargs.setdefault("fallback", Self)
        super().__init__(data, **kwargs)
        self.multi_redir      = multi
        self.re_mark          = re_mark
        self._expansion_type  = DKey
        self._typecheck       = DKey | list[DKey]

    def expand(self, *sources, max=None, full:bool=False, **kwargs) -> None|DKey:
        match super().redirect(*sources, multi=self.multi_redir, re_mark=self.re_mark, **kwargs):
            case list() as xs if self.multi_redir and full:
                return [x.expand(*sources) for x in xs]
            case list() as xs if self.multi_redir:
                return xs
            case [x, *xs] if full:
                return x.expand(*sources)
            case [x, *xs] if self._fallback == self and x < self:
                return x
            case [x, *xs] if self._fallback is None:
                return None
            case [x, *xs]:
                return x
            case []:
                return self._fallback

class ConflictDKey(SingleDKey):
    """ Like a redirection key,
      but for handling conflicts between subkeys in multikeys.

      eg: MK(--aval={blah!p}/{blah})
    """

class ArgsDKey(SingleDKey, mark=DKeyMark_e.ARGS):
    """ A Key representing the action spec's args """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._expansion_type  = list
        self._typecheck = list

    def expand(self, *sources, **kwargs) -> list:
        for source in sources:
            if not isinstance(source, SpecStruct_p):
                continue

            return source.args

        return []

class KwargsDKey(SingleDKey, mark=DKeyMark_e.KWARGS):
    """ A Key representing all of an action spec's kwargs """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._expansion_type  = dict
        self._typecheck = dict

    def expand(self, *sources, fallback=None, **kwargs) -> dict:
        for source in sources:
            if not isinstance(source, SpecStruct_p):
                continue

            return source.kwargs

        return fallback or dict()

class ImportDKey(SingleDKey, mark=DKeyMark_e.CODE, tparam="c"):
    """
      Subclass for dkey's which expand to CodeReferences
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._expansion_type  = CodeReference
        self._typecheck = CodeReference

