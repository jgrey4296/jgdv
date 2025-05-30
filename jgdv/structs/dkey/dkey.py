#!/usr/bin/env python3
"""

"""
# ruff: noqa: ARG002

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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
# ##-- end stdlib imports

from jgdv import Proto, Mixin
from jgdv.mixins.annotate import SubAnnotate_m
from jgdv.structs.strang import Strang
from ._util.expander import DKeyExpander
from .processor import DKeyProcessor

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol
from . import _interface as API # noqa: N812

if typing.TYPE_CHECKING:
    from jgdv import M_
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

@Proto(API.Key_p, check=False, mod_mro=False)
class DKey(Strang):
    """ A facade for DKeys and variants.
      Implements __new__ to create the correct key type, from a string, dynamically.

      kwargs:
      explicit = insists that keys in the string are wrapped in braces '{akey} {anotherkey}'.
      mark     = pre-register expansion parameters / type etc
      check    = dictate a type that expanding this key must match
      fparams  = str formatting instructions for the key

      Eg:
      DKey('blah')
      -> SingleDKey('blah')
      -> SingleDKey('blah').format('w')
      -> '{blah}'
      -> [toml] aValue = '{blah}'

      Because cls.__new__ calls __init__ automatically for return values of type cls,
      DKey is the factory, but all DKeys are subclasses of DKeyBase,
      to allow control over __init__.

      Base class for implementing actual DKeys.
      adds:
      `_mark`

      plus some util methods

    init takes kwargs:
    fmt, mark, check, ctor, help, fallback, max_exp

    on class definition, can register a 'mark', 'multi', and a conversion parameter str
    """
    __slots__                                           = ("data",)
    __match_args                                        = ()
    _annotate_to    : ClassVar[str]                     = "_mark"
    _processor      : ClassVar                          = DKeyProcessor()
    _sections       : ClassVar                          = API.DKEY_SECTIONS
    _expander       : ClassVar[DKeyExpander]            = DKeyExpander()
    _typevar        : ClassVar                          = None
    _mark           : ClassVar                          = "dkey"

    _extra_kwargs   : ClassVar[set[str]]                = set()
    _extra_sources  : ClassVar[list[dict]]              = []
    Marks           : ClassVar[API.DKeyMarkAbstract_e]  = API.DKeyMark_e # type: ignore[assignment]
    data            : API.DKey_d

    ##--| Class Utils

    @override
    def __class_getitem__(cls:type[API.Key_p], *params:Any) -> type[API.Key_p]: # type: ignore[override]
        assert(isinstance(cls._processor, DKeyProcessor))
        try:
            return cls._processor.get_subtype(*params)
        except ValueError:
            assert(hasattr(Strang, "__class_getitem__"))
            return super(Strang, cls).__class_getitem__(*params) # type: ignore[misc]

    def __init_subclass__(cls:type[API.Key_p], *, mark:M_[API.KeyMark]=None, conv:M_[str]=None, multi:bool=False, core:bool=False) -> None:
        """ Registered the subclass as a DKey and sets the Mark enum this class associates with """
        assert(isinstance(cls._processor, DKeyProcessor))
        logging.debug("Registering DKey Subclass: %s : %s", cls, mark)
        super().__init_subclass__()
        cls._mark = mark or cls._mark
        cls._expander.set_ctor(DKey)
        match cls._mark:
            case str() | type() | API.DKeyMarkAbstract_e() as x:
                cls._processor.register_key_type(cls, x, convert=conv, multi=multi, core=core)
            case _:
                logging.info("No Mark to Register Key Subtype: %s", cls)


    @classmethod
    def MarkOf[T:API.Key_p](cls) -> API.KeyMark: # noqa: N802
        """ Get the mark of the key type or instance """
        return cls._mark

    @classmethod
    def add_sources(cls, *sources:dict) -> None:
        """ register additional sources that are always included """
        cls._extra_sources += sources

    ##--| Class Main

    def __init__(self, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        assert(not self.endswith(API.INDIRECT_SUFFIX)), self[:]
        super().__init__(*args, **kwargs)
        self.data = API.DKey_d(**kwargs)

    def __call__(self, *args:Any, **kwargs:Any) -> Any:  # noqa: ANN401
        """ call expand on the key.
        Args and kwargs are passed verbatim to expand()
        """
        return self.expand(*args, **kwargs)

    def __eq__(self, other:object) -> bool:
        match other:
            case DKey() | str():
                return str.__eq__(self, other)
            case _:
                return NotImplemented


    def __hash__(self) -> int:
        return hash(self[:])
    ##--| Utils

    def var_name(self) -> str:
        """ When testing the dkey for its inclusion in a decorated functions signature,
        this gives the 'named' val if its not None, otherwise the str of the key
        """
        return self.data.name or str(self)

    def keys(self) -> list[API.Key_p]:
        """ Get subkeys of this key. by default, an empty list.
        (named 'keys' to be in keeping with dict)
        """
        return []

    def expand(self, *args:Any, **kwargs:Any) -> Maybe:  # noqa: ANN401
        kwargs.setdefault("limit", self.data.max_expansions)
        assert(isinstance(self, API.Key_p))
        match self._expander.expand(self, *args, **kwargs):
            case API.ExpInst_d(value=val, literal=True):
                return val
            case _:
                return None

    def redirect(self, *args:Any, **kwargs:Any) -> list[API.Key_p]:  # noqa: ANN401
        assert(isinstance(self, API.Key_p))
        result = [DKey(x.value) for x in self._expander.redirect(self, *args, **kwargs) if x is not None]
        return result


    def exp_extra_sources_h(self) -> list:
        return DKey._extra_sources

    def exp_pre_lookup_h(self, sources:list[dict], opts:dict) -> Maybe[API.LookupList]:
        return None

    def exp_pre_recurse_h(self, vals:list[API.ExpInst_d], sources:list[dict], opts:dict) -> Maybe[list[API.ExpInst_d]]:
        return None

    def exp_flatten_h(self, vals:list[API.ExpInst_d], opts:dict) -> Maybe[API.LitFalse|API.ExpInst_d]:
        return None

    def exp_coerce_h(self, val:API.ExpInst_d, opts:dict) -> Maybe[API.ExpInst_d]:
        return None

    def exp_final_h(self, val:API.ExpInst_d, opts:dict) -> Maybe[API.LitFalse|API.ExpInst_d]:
        return None

    def exp_check_result_h(self, val:API.ExpInst_d, opts:dict) -> None:
        return None
