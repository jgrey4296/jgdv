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
from jgdv import identity_fn, Proto, Mixin
from jgdv.mixins.annotate import SubAnnotate_m
from .meta import DKey, DKeyMark_e, DKeyMeta
from .format import DKeyFormatting_m
from .expander import Expander
from .._interface import ExpInst_d
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
from .._interface import Key_p, Expandable_p

if TYPE_CHECKING:
   from .. import _interface as API  # noqa: N812
   from jgdv import Maybe, M_, Rx, Ident, Ctor, FmtStr, CHECKTYPE
   from typing import Final
   from typing import ClassVar, LiteralString
   from typing import Never, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   from jgdv._abstract.protocols import SpecStruct_p

   type KeyMark    = API.KeyMark
   type LookupList = API.LookupList
   type LitFalse   = API.LitFalse

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(Key_p, Expandable_p, check=False)
@Mixin(DKeyFormatting_m)
class DKeyBase[X](SubAnnotate_m, str, annotate_to="_mark"):
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

    _mark               : KeyMark = DKey.Mark.default # type: ignore
    _expansion_type     : Ctor
    _typecheck          : CHECKTYPE
    _fallback           : Maybe[Any]
    _fmt_params         : Maybe[FmtStr]
    _conv_params        : Maybe[FmtStr]
    _help               : Maybe[str]
    _named              : Maybe[str]

    _extra_kwargs       : ClassVar[set[str]]            = set()
    __hash__            : Callable                      = str.__hash__

    def __init_subclass__(cls, *, mark:M_[KeyMark]=None, conv:M_[str]=None, multi:bool=False) -> None:
        """ Registered the subclass as a DKey and sets the Mark enum this class associates with """
        super().__init_subclass__()
        cls._mark        = mark or cls._mark
        match cls._mark:
            case None:
                logging.info("No Mark to Register Key Subtype: %s", cls)
            case x:
                DKeyMeta.register_key_type(cls, x, conv=conv, multi=multi)

    def __new__(cls, *args, **kwargs) -> Never:
        """ Blocks creation of DKey's except through DKey itself,
          unless 'force=True' kwarg (for testing).

        (this can work because key's are str's with an extended init)
        """
        msg = "Don't build DKey subclasses directly. use DKey(..., force=CLS) if you must"
        raise RuntimeError(msg)

    def __init__(self, data:str, **kwargs) -> None:
        assert(data == str(self))
        super().__init__()
        self._expansion_type = kwargs.get("ctor", identity_fn)
        self._typecheck      = kwargs.get("check", Any)
        self._mark           = kwargs.get("mark", self.__class__._mark)
        self._max_expansions = kwargs.get("max_exp", None)
        self._fallback       = kwargs.get("fallback", None)
        self._named          = kwargs.get("named", None)
        self._conv_params    = None
        self._fmt_params     = None
        if self._fallback is Self:
            self._fallback = self

        self._set_help(kwargs.get("help", None))

    def __call__(self, *args, **kwargs) -> Any:  # noqa: ANN401
        """ call expand on the key.
        Args and kwargs are passed verbatim to expand()
        """
        return self.expand(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self}>"

    def __eq__(self, other:object) -> bool:
        match other:
            case DKey() | str():
                return str.__eq__(self, other)
            case _:
                return NotImplemented

    def _set_help(self, help:Maybe[str]) -> Self:  # noqa: A002
        match help:
            case None:
                pass
            case str():
                self._help = help

        return self

    def var_name(self) -> str:
        """ When testing the dkey for its inclusion in a decorated functions signature,
        this gives the 'named' val if its not None, otherwise the str of the key
        """
        return self._named or str(self)

    def keys(self) -> list[Key_p]:
        """ Get subkeys of this key. by default, an empty list.
        (named 'keys' to be in keeping with dict)
        """
        return []

    @property
    def multi(self) -> bool:
        """ utility property to test if the key is a multikey,
        without having to do reflection
        (to avoid some recursive import issues)
        """
        return False

    def expand(self, *args, **kwargs) -> Maybe:
        kwargs.setdefault("limit", self._max_expansions)
        match Expander.expand(self, *args, **kwargs):
            case ExpInst_d(val=val, literal=True):
                return val
            case _:
                return None

    def redirect(self, *args, **kwargs) -> list[DKey]:
        return Expander.redirect(self, *args, **kwargs)

    def exp_extra_sources_h(self) -> list:
        return DKey._extra_sources

    def exp_pre_lookup_h(self, sources, opts) -> Maybe[LookupList]:
        pass

    def exp_pre_recurse_h(self, vals:list[ExpInst_d], sources, opts) -> Maybe[list[ExpInst_d]]:
        pass

    def exp_flatten_h(self, vals:list[ExpInst_d], opts) -> Maybe[LitFalse|ExpInst_d]:
        pass

    def exp_coerce_h(self, val:ExpInst_d, opts) -> Maybe[ExpInst_d]:
        pass

    def exp_final_h(self, val:ExpInst_d, opts) -> Maybe[LitFalse|ExpInst_d]:
        pass

    def exp_check_result_h(self, val:ExpInst_d, opts) -> None:
        pass
