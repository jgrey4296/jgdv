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

# ##-- 1st party imports
from jgdv._abstract.protocols import Buildable_p, Key_p, SpecStruct_p
from jgdv.mixins.annotate import SubAnnotate_m
from jgdv.structs.dkey.formatter import DKeyFormatter
from jgdv.structs.dkey.meta import CONV_SEP, REDIRECT_SUFFIX, DKey, DKeyMark_e
from jgdv.structs.dkey.mixins import DKeyExpansion_m, DKeyFormatting_m, identity

from jgdv.structs.dkey.formatter_v2 import _DKeyExpander_m

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, Any, Self
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
   from jgdv import Maybe, M_, Rx, Ident, Ctor, FmtStr, CHECKTYPE
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

KEY_PATTERN        : Final[FmtStr]                = "{(.+?)}"
MAX_KEY_EXPANSIONS : Final[int]                   = 10

PATTERN            : Final[Rx]                    = re.compile(KEY_PATTERN)
FAIL_PATTERN       : Final[Rx]                    = re.compile("[^a-zA-Z_{}/0-9-]")
FMT_PATTERN        : Final[Rx]                    = re.compile("[wdi]+")
EXPANSION_HINT     : Final[Ident]                 = "_doot_expansion_hint"
HELP_HINT          : Final[Ident]                 = "_doot_help_hint"
CWD_MARKER         : Final[Ident]                 = "__cwd"

class DKeyBase(DKeyFormatting_m, DKeyExpansion_m, _DKeyExpander_m, Key_p, SubAnnotate_m, str):
    """
      Base class characteristics of DKeys.
      adds:
      `_mark`
      `_expansion_type`
      `_typecheck`

      plus some util methods

    init takes kwargs:
    fmt, mark, check, ctor, help, fallback, max_exp

    on class definition, can register a 'mark', 'multi', and a conversion parameter str
    """

    _mark               : DKeyMark_e                    = DKey.mark.default
    _expansion_type     : Ctor                          = str
    _typecheck          : CHECKTYPE                     = Any
    _fallback           : Any                           = None
    _fmt_params         : Maybe[FmtStr]                 = None
    _help               : Maybe[str]                    = None

    __expected_init_keys : ClassVar[list[str]]          = ["ctor", "check", "mark", "fallback", "max_exp", "fmt", "help", "force", "implicit", "conv"]

    # Use the default str hash method
    __hash__                                            = str.__hash__

    def __init_subclass__(cls, *, mark:M_[DKeyMark_e]=None, tparam:M_[str]=None, multi:bool=False):
        """ Registered the subclass as a DKey and sets the Mark enum this class associates with """
        super().__init_subclass__()
        cls._mark = mark
        DKey.register_key(cls, mark, tparam=tparam, multi=multi)
        DKey.register_parser(DKeyFormatter)

    def __new__(cls, *args, **kwargs):
        """ Blocks creation of DKey's except through DKey itself,
          unless 'force=True' kwarg (for testing).
        """
        match kwargs:
            case {"force": True}:
                del kwargs['force']
                obj = str.__new__(cls, *args)
                obj.__init__(*args, **kwargs)
                return obj
            case _:
                raise RuntimeError("Don't build DKey subclasses directly")

    def __init__(self, data, **kwargs):
        assert(not bool((kwkeys:=kwargs.keys() - DKeyBase.__expected_init_keys))), kwkeys
        super().__init__(data)
        self._expansion_type : Ctor          = kwargs.get("ctor", identity)
        self._typecheck      : CHECKTYPE     = kwargs.get("check", Any)
        self._mark           : DKeyMark_e    = kwargs.get("mark", self.__class__._mark)
        self._max_expansions : Maybe[int]    = kwargs.get("max_exp", None)
        self._fallback       : Maybe[Any]    = kwargs.get("fallback", None)
        if self._fallback is Self:
            self._fallback = self

        self._update_expansion_params(self._mark)
        self.set_fmt_params(kwargs.get("fmt", ""))
        self._set_help(kwargs.get("help", None))

    def __call__(self, *args, **kwargs) -> Any:
        """ call expand on the key.
        Args and kwargs are passed verbatim to expand()
        """
        return self.expand(*args, **kwargs)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"

    def __eq__(self, other):
        match other:
            case DKey() | str():
                return str.__eq__(self, other)
            case _:
                return NotImplemented

    def _set_help(self, help:Maybe[str]) -> Self:
        match help:
            case None:
                pass
            case str():
                self._help = help

        return self

    def keys(self) -> list[Key_p]:
        """ Get subkeys of this key. by default, an empty list.
        (named 'keys' to be in keeping with dict)
        """
        return []

    def extra_sources(self) -> list[Any]:
        """ An overrideable method allowing subtypes
        to add standard additional sources for expansion.

        eg: Path Keys provide the global Locations database
        """
        return []

    @property
    def multi(self) -> bool:
        """ utility property to test if they key is a multikey,
        without having to do reflection
        (to avoid some recursive import issues)
        """
        return False
