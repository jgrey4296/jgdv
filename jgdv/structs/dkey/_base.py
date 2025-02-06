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
from jgdv import identity_fn
from jgdv._abstract.protocols import Buildable_p, Key_p, SpecStruct_p
from jgdv.mixins.annotate import SubAnnotate_m
from jgdv.structs.dkey._meta import DKey, DKeyMark_e, DKeyMeta
from jgdv.structs.dkey._format import DKeyFormatting_m

from jgdv.structs.dkey._expander import DKeyLocalExpander_m, DKeyCentralExpander_m

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

   type KeyMark = DKeyMark_e|str

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class DKeyBase(DKeyFormatting_m, DKeyCentralExpander_m, DKeyLocalExpander_m, Key_p, SubAnnotate_m, str):
    """
      Base class for implementing actual DKeys.
      adds:
      `_mark`
      `_expansion_type`
      `_typecheck`

      plus some util methods

    init takes kwargs:
    fmt, mark, check, ctor, help, fallback, max_exp

    on class definition, can register a 'mark', 'multi', and a conversion parameter str
    """

    _mark               : KeyMark                       = DKey.mark.default
    _expansion_type     : Ctor                          = identity_fn
    _typecheck          : CHECKTYPE                     = Any
    _fallback           : Any                           = None
    _fmt_params         : Maybe[FmtStr]                 = None
    _conv_params        : Maybe[FmtStr]                 = None
    _help               : Maybe[str]                    = None

    __hash__                                            = str.__hash__

    expand                                              = DKeyLocalExpander_m.local_expand
    redirect                                            = DKeyLocalExpander_m.local_redirect

    def __init_subclass__(cls, *, mark:M_[KeyMark]=None, conv:M_[str]=None, multi:bool=False):
        """ Registered the subclass as a DKey and sets the Mark enum this class associates with """
        super().__init_subclass__()
        cls._mark = mark
        DKeyMeta.register_key_type(cls, mark, conv=conv, multi=multi)

    def __new__(cls, *args, **kwargs):
        """ Blocks creation of DKey's except through DKey itself,
          unless 'force=True' kwarg (for testing).
        """
        if kwargs.get("force", False):
            return super().__new__(*args, **kwargs)
        raise RuntimeError("Don't build DKey subclasses directly. use DKey(..., force=CLS) if you must")

    def __init__(self, data, **kwargs):
        super().__init__(data)
        self._expansion_type : Ctor          = kwargs.get("ctor", identity_fn)
        self._typecheck      : CHECKTYPE     = kwargs.get("check", Any)
        self._mark           : KeyMark       = kwargs.get("mark", self.__class__._mark)
        self._max_expansions : Maybe[int]    = kwargs.get("max_exp", None)
        self._fallback       : Maybe[Any]    = kwargs.get("fallback", None)
        if self._fallback is Self:
            self._fallback = self

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

    def _set_params(self, *, fmt:Maybe[str]=None, conv:Maybe[str]=None) -> None:
        match fmt:
            case None:
                pass
            case str() if bool(fmt):
                self._fmt_params = fmt

        match conv:
            case None:
                pass
            case str() if bool(conv):
                self._conv_params = conv

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
