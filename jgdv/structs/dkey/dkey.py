#!/usr/bin/env python3
"""

"""
# ruff: noqa:

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

from jgdv import Proto, Mixin, M_
from jgdv.mixins.annotate import SubAnnotate_m
from ._meta import DKeyMeta
from ._util.expander import Expander
from ._util.format import DKeyFormatting_m

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

@Proto(API.Key_i, check=False, mod_mro=False)
class DKey(DKeyFormatting_m, SubAnnotate_m, str, metaclass=DKeyMeta, annotate_to="_mark", core=True):
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
      `_expansion_type`
      `_typecheck`

      plus some util methods

    init takes kwargs:
    fmt, mark, check, ctor, help, fallback, max_exp

    on class definition, can register a 'mark', 'multi', and a conversion parameter str
    """
    __slots__     = ("data",)
    __match_args  = ("_mark",)
    data            : API.DKey_d
    Marks           : ClassVar[type[API.KeyMark]]    = API.DKeyMark_e
    ExpInst         : ClassVar[type[API.ExpInst_d]]  = API.ExpInst_d
    _mark           : ClassVar[Maybe[API.KeyMark]]   = API.DKeyMark_e.default()
    _extra_kwargs   : ClassVar[set[str]]             = set()
    _extra_sources  : ClassVar[list[dict]]           = []
    __expander      : ClassVar[Expander]             = Expander()
    __hash__        : Callable                       = str.__hash__

    ##--| Class Utils

    @override
    def __class_getitem__[T:API.Key_p](cls:type[T], *params:Any) -> type[T]: # type: ignore[override]
        return DKeyMeta.get_subtype(*params, multi=True)

    def __init_subclass__(cls, *, mark:M_[API.KeyMark]=None, conv:M_[str]=None, multi:bool=False, force:bool=False, core:bool=False) -> None:
        """ Registered the subclass as a DKey and sets the Mark enum this class associates with """
        logging.debug("Registering DKey Subclass: %s : %s", cls, mark)
        cls._mark = mark or cls._mark
        match cls._mark:
            case str() | type() | API.DKeyMarkAbstract_e() as x:
                DKeyMeta.register_key_type(cls, x, conv=conv, multi=multi, force=force, core=core)
            case _:
                logging.info("No Mark to Register Key Subtype: %s", cls)

    @staticmethod
    def MarkOf[T:API.Key_p](target:type[T]|T) -> API.KeyMark:  # noqa: N802
        """ Get the mark of the key type or instance """
        match target:
            case DKey():
                return target._mark # type: ignore
            case type() if issubclass(target, DKey):
                return target._mark
            case _:
                msg = "Tried to retrieve a mark from an unknown type"
                raise TypeError(msg)

    @classmethod
    def add_sources(cls, *sources:dict) -> None:
        """ register additional sources that are always included """
        cls._extra_sources += sources

    def __new__(cls, *args:Any, **kwargs:Any) -> Never:  # noqa: ANN401, ARG004
        """ Blocks creation of DKey's except through DKey itself,
          unless 'force=True' kwarg (for testing).

        (this can work because key's are str's with an extended init)
        """
        msg = "Don't build DKey subclasses directly. use DKey(..., force=CLS) if you must"
        raise RuntimeError(msg)

    ##--| Class Main

    def __init__(self, data:str, **kwargs:Any) -> None:  # noqa: ANN401
        assert(data == str(self))
        super().__init__()
        self.data = API.DKey_d(**kwargs)

    def __call__(self, *args:Any, **kwargs:Any) -> Any:  # noqa: ANN401
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

    ##--| Utils

    def var_name(self) -> str:
        """ When testing the dkey for its inclusion in a decorated functions signature,
        this gives the 'named' val if its not None, otherwise the str of the key
        """
        return self.data.name or str(self)

    def keys(self) -> list[API.Key_i]:
        """ Get subkeys of this key. by default, an empty list.
        (named 'keys' to be in keeping with dict)
        """
        return []

    def expand(self, *args:Any, **kwargs:Any) -> Maybe:  # noqa: ANN401
        kwargs.setdefault("limit", self.data.max_expansions)
        match self.__expander.expand(self, *args, **kwargs):
            case API.ExpInst_d(val=val, literal=True):
                return val
            case _:
                return None

    def redirect(self, *args:Any, **kwargs:Any) -> list[API.Key_p]:  # noqa: ANN401
        return self.__expander.redirect(self, *args, **kwargs)

    ##--| Expansion Hooks

    def exp_extra_sources_h(self) -> list:
        return DKey._extra_sources

    def exp_pre_lookup_h(self, sources, opts) -> Maybe[API.LookupList]:
        return None

    def exp_pre_recurse_h(self, vals:list[API.ExpInst_d], sources, opts) -> Maybe[list[API.ExpInst_d]]:
        return None

    def exp_flatten_h(self, vals:list[API.ExpInst_d], opts) -> Maybe[API.LitFalse|API.ExpInst_d]:
        return None

    def exp_coerce_h(self, val:API.ExpInst_d, opts) -> Maybe[API.ExpInst_d]:
        return None

    def exp_final_h(self, val:API.ExpInst_d, opts) -> Maybe[API.LitFalse|API.ExpInst_d]:
        return None

    def exp_check_result_h(self, val:API.ExpInst_d, opts) -> None:
        return None

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
      `_expansion_type`
      `_typecheck`

      plus some util methods

    init takes kwargs:
    fmt, mark, check, ctor, help, fallback, max_exp

    on class definition, can register a 'mark', 'multi', and a conversion parameter str
    """
    __slots__     = ("data",)
    __match_args  = ("_mark",)
    data            : API.DKey_d
    Marks           : ClassVar[type[API.KeyMark]]    = API.DKeyMark_e
    ExpInst         : ClassVar[type[API.ExpInst_d]]  = API.ExpInst_d
    _mark           : ClassVar[Maybe[API.KeyMark]]   = API.DKeyMark_e.default()
    _extra_kwargs   : ClassVar[set[str]]             = set()
    _extra_sources  : ClassVar[list[dict]]           = []
    __expander      : ClassVar[Expander]             = Expander()
    __hash__        : Callable                       = str.__hash__

    ##--| Class Utils

    @override
    def __class_getitem__[T:API.Key_p](cls:type[T], *params:Any) -> type[T]: # type: ignore[override]
        return DKeyMeta.get_subtype(*params, multi=True)

    def __init_subclass__(cls, *, mark:M_[API.KeyMark]=None, conv:M_[str]=None, multi:bool=False, force:bool=False, core:bool=False) -> None:
        """ Registered the subclass as a DKey and sets the Mark enum this class associates with """
        logging.debug("Registering DKey Subclass: %s : %s", cls, mark)
        cls._mark = mark or cls._mark
        match cls._mark:
            case str() | type() | API.DKeyMarkAbstract_e() as x:
                DKeyMeta.register_key_type(cls, x, conv=conv, multi=multi, force=force, core=core)
            case _:
                logging.info("No Mark to Register Key Subtype: %s", cls)

    @staticmethod
    def MarkOf[T:API.Key_p](target:type[T]|T) -> API.KeyMark:  # noqa: N802
        """ Get the mark of the key type or instance """
        match target:
            case DKey():
                return target._mark # type: ignore
            case type() if issubclass(target, DKey):
                return target._mark
            case _:
                msg = "Tried to retrieve a mark from an unknown type"
                raise TypeError(msg)

    @classmethod
    def add_sources(cls, *sources:dict) -> None:
        """ register additional sources that are always included """
        cls._extra_sources += sources

    def __new__(cls, *args:Any, **kwargs:Any) -> Never:  # noqa: ANN401, ARG004
        """ Blocks creation of DKey's except through DKey itself,
          unless 'force=True' kwarg (for testing).

        (this can work because key's are str's with an extended init)
        """
        msg = "Don't build DKey subclasses directly. use DKey(..., force=CLS) if you must"
        raise RuntimeError(msg)

    ##--| Class Main

    def __init__(self, data:str, **kwargs:Any) -> None:  # noqa: ANN401
        assert(data == str(self))
        super().__init__()
        self.data = API.DKey_d(**kwargs)

    def __call__(self, *args:Any, **kwargs:Any) -> Any:  # noqa: ANN401
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

    ##--| Utils

    def var_name(self) -> str:
        """ When testing the dkey for its inclusion in a decorated functions signature,
        this gives the 'named' val if its not None, otherwise the str of the key
        """
        return self.data.name or str(self)

    def keys(self) -> list[API.Key_i]:
        """ Get subkeys of this key. by default, an empty list.
        (named 'keys' to be in keeping with dict)
        """
        return []

    def expand(self, *args:Any, **kwargs:Any) -> Maybe:  # noqa: ANN401
        kwargs.setdefault("limit", self.data.max_expansions)
        match self.__expander.expand(self, *args, **kwargs):
            case API.ExpInst_d(val=val, literal=True):
                return val
            case _:
                return None

    def redirect(self, *args:Any, **kwargs:Any) -> list[API.Key_p]:  # noqa: ANN401
        return self.__expander.redirect(self, *args, **kwargs)

    ##--| Expansion Hooks

    def exp_extra_sources_h(self) -> list:
        return DKey._extra_sources

    def exp_pre_lookup_h(self, sources, opts) -> Maybe[API.LookupList]:
        return None

    def exp_pre_recurse_h(self, vals:list[API.ExpInst_d], sources, opts) -> Maybe[list[API.ExpInst_d]]:
        return None

    def exp_flatten_h(self, vals:list[API.ExpInst_d], opts) -> Maybe[API.LitFalse|API.ExpInst_d]:
        return None

    def exp_coerce_h(self, val:API.ExpInst_d, opts) -> Maybe[API.ExpInst_d]:
        return None

    def exp_final_h(self, val:API.ExpInst_d, opts) -> Maybe[API.LitFalse|API.ExpInst_d]:
        return None

    def exp_check_result_h(self, val:API.ExpInst_d, opts) -> None:
        return None

