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
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Self,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv._abstract.protocols import Buildable_p, Key_p, SpecStruct_p
from jgdv.structs.dkey.meta import CONV_SEP, REDIRECT_SUFFIX, DKey, DKeyMark_e
from jgdv.structs.dkey.formatter import DKeyFormatter
from jgdv.structs.dkey.mixins import DKeyExpansion_m, DKeyFormatting_m, identity
from jgdv.mixins.annotate import SubAnnotate_m

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

class DKeyBase(DKeyFormatting_m, DKeyExpansion_m, Key_p, SubAnnotate_m, str):
    """
      Base class characteristics of DKeys.
      adds:
      `_mark`
      `_expansion_type`
      `_typecheck`

      plus some util methods

    """

    _mark               : DKeyMark_e                  = DKey.mark.default
    _expansion_type     : type|callable               = str
    _typecheck          : CHECKTYPE                   = Any
    _fallback           : Any                         = None
    _fmt_params         : None|str                    = None
    _help               : None|str                    = None

    __hash__                                          = str.__hash__

    def __init_subclass__(cls, *, mark:None|DKeyMark_e=None, tparam:None|str=None, multi=False):
        """ Registered the subclass as a DKey and sets the Mark enum this class associates with """
        super().__init_subclass__()
        cls._mark = mark
        DKey.register_key(cls, mark, tparam=tparam, multi=multi)
        DKey.register_parser(DKeyFormatter)

    def __new__(cls, *args, **kwargs):
        """ Blocks creation of DKey's except through DKey itself,
          unless 'force=True' kwarg (for testing).
        """
        if not kwargs.get('force', False):
            raise RuntimeError("Don't build DKey subclasses directly")
        del kwargs['force']
        obj = str.__new__(cls, *args)
        obj.__init__(*args, **kwargs)
        return obj

    def __init__(self, data, fmt:None|str=None, mark:DKeyMark_e=None, check:CHECKTYPE=None, ctor:None|type|callable=None, help:None|str=None, fallback=None, max_exp=None, **kwargs):
        super().__init__(data)
        self._expansion_type       = ctor or identity
        self._typecheck            = check or Any
        self._mark                 = mark or DKeyMark_e.FREE
        self._fallback             = fallback
        self._max_expansions       = max_exp
        if self._fallback is Self:
            self._fallback = self

        self._update_expansion_params(mark)
        self.set_fmt_params(fmt)
        self.set_help(help)

    def __call__(self, *args, **kwargs) -> Any:
        """ call expand on the key """
        return self.expand(*args, **kwargs)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"

    def __and__(self, other) -> bool:
        return f"{self:w}" in other

    def __rand__(self, other):
        return self & other

    def __eq__(self, other):
        match other:
            case DKey() | str():
                return str(self) == str(other)
            case _:
                return False

    def set_help(self, help:None|str) -> Self:
        match help:
            case None:
                pass
            case str():
                self._help = help

        return self

    def keys(self) -> list[Key_p]:
        """ Get subkeys of this key. by default, an empty list """
        return []

    def extra_sources(self) -> list[Any]:
        return []

    @property
    def multi(self) -> bool:
        return False
