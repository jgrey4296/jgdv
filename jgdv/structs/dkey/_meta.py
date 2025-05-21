#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN001, ANN002, ANN003
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import builtins
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

# ##-- 1st party imports
from . import _interface as API  # noqa: N812
from jgdv.mixins.enum_builders import EnumBuilder_m
from jgdv.mixins.annotate import SubAnnotate_m, Subclasser
from ._util.parser import DKeyParser
from ._interface import DKeyMark_e, ExpInst_d, Key_i
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never, ClassVar
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
from ._interface import Key_p

if TYPE_CHECKING:
   from jgdv import Maybe, Ident, Ctor
   import enum
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   from string import Formatter

   from ._interface import KeyMark

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

StrMeta : Final[type] = type(str)

##--| Body:

class DKeyMeta(StrMeta):
    """
      The Metaclass for keys, which ensures that subclasses of DKeyBase
      are API.Key_p's, despite there not being an actual subclass relation between them.

    This allows DKeyBase to actually bottom out at str
    """

    single_registry      : ClassVar[dict[KeyMark,type]]    = {}
    multi_registry       : ClassVar[dict[KeyMark,type]]    = {}
    core_registry        : ClassVar[set[type[API.Key_p]]]  = set()
    _conv_registry       : ClassVar[dict[str, KeyMark]]    = {}
    _parser              : ClassVar[DKeyParser]            = DKeyParser()

    # Use the default str hash method
    _expected_init_keys  : ClassVar[list[str]]             = API.DEFAULT_DKEY_KWARGS[:]

    def __call__(cls:Ctor[API.Key_p], input_text:str|pl.Path, *args, **kwargs) -> API.Key_p:  # noqa: N805
        """ Runs on class instance creation
        skips running cls.__init__, allowing cls.__new__ control
        """
        new_key        : API.Key_p
        raw            : tuple[API.RawKey_d]
        text           : str                     = str(input_text)
        ctor           : Maybe[Ctor[API.Key_p]]  = None
        instance_data  : dict                    = {}
        is_multi       : bool                    = False
        implicit       : bool                    = kwargs.pop("implicit", False) # is key wrapped? {key}
        insist         : bool                    = kwargs.pop("insist", False) # must produce key, not nullkey
        mark           : API.KeyMark             = kwargs.pop("mark", None)

        match kwargs.pop(API.FORCE_ID, None):
            case type() as force:
                ctor                             = force
            case None:
                pass
        ##--| Get parsed keys
        match kwargs.pop(API.RAWKEY_ID, None):
            case tuple() as xs:
                raw = xs
            case None:
                raw = DKeyMeta.extract_raw_keys(input_text, implicit=implicit)

        ##--| discriminate raw keys
        match DKeyMeta._discriminate_raw(raw, kwargs, mark=mark):
            case dict() as extra:
                # use overrides
                is_multi  = extra.pop("multi", is_multi)
                mark      = extra.pop("mark",  mark)
                text      = extra.pop('text', text)
                instance_data.update(extra)
            case _:
                raise ValueError()
        ##--| select ctor -> build -> init
        assert(bool(text))
        assert(bool(instance_data))
        match DKeyMeta._select_ctor(ctor, mark=mark, multi=is_multi):
            case type() as ctor if insist and ctor.MarkOf(ctor) is DKeyMark_e.NULL:
                raise TypeError(API.InsistentKeyFailure, text)
            case type() as ctor if bool(unexpected:=DKeyMeta._validate_init_kwargs(ctor, kwargs)):
                raise ValueError(API.UnexpectedKwargs, unexpected)
            case type() as ctor:
                new_key = str.__new__(ctor, text)
                new_key.__init__(text, **instance_data, **kwargs)
            case _:
                raise TypeError()
        ##--| return
        assert(new_key is not None)
        return new_key

    ##--| Key Building

    @staticmethod
    def _discriminate_raw(raw_keys:list[API.RawKey_d], kdata:dict, *, mark:Maybe[API.KeyMark]=None) -> Maybe[dict]:
        """ Take extracted keys of the text,
        and determine features of them, returning a dict,
        used to update DKeyMeta.__call__'s state

        """
        assert(all(isinstance(x, API.RawKey_d) for x in raw_keys))
        is_multi          : bool  = kdata.pop("multi", False)
        multi_compatible  : bool  = mark is None or mark in DKeyMeta.multi_registry
        data                = {
            'mark'         : mark or DKeyMark_e.default(),
            'multi'        : is_multi,
            API.RAWKEY_ID  : raw_keys,
        }
        match raw_keys:
            case [x] if not bool(x) and bool(x.prefix) and not is_multi:
                # No keys found, use NullDKey
                data['mark'] = DKeyMark_e.NULL
            case [x] if is_multi and not multi_compatible:
                # One key, declared as a multi key
                data['mark'] = DKeyMark_e.MULTI
            case [x] if is_multi:
                pass
            case [x] if not bool(x.prefix) and x.is_indirect():
                # One Key_ found with no extra text
                # so truncate to just the exact key
                data['mark'] = DKeyMark_e.INDIRECT
                data['text'] = x.indirect()
            case [x] if not bool(x.prefix):
                # one key, no extra text
                conv_mark = DKeyMeta._conv_registry.get(x.conv, None)
                if conv_mark and (mark != conv_mark):
                    raise ValueError(API.MarkConversionConflict, kw_mark, conv_mark)
                elif conv_mark:
                    data['mark'] = conv_mark

                # so truncate to just the exact key
                data['text'] = x.direct()
            case [*xs] if is_multi and multi_compatible:
                pass
            case [*xs]:
                # Multiple keys found
                data['mark']   = DKeyMark_e.MULTI
                data['multi']  = True
            case x:
                raise TypeError(type(x))
        ##--|
        return data

    @staticmethod
    def _select_ctor(cls:Maybe[Ctor[API.Key_p]], *, mark:KeyMark, multi:bool) -> Ctor[API.Key_p]:
        """ Select the appropriate key ctor,
        which can be forced if necessary,
        otherwise uses the mark and multi params

        """
        # Choose the sub-ctor
        match cls:
            case type() as x:
                # sub type has been forced
                return x
            case _:
                return DKeyMeta.get_subtype(mark, multi=multi)

    @staticmethod
    def _validate_init_kwargs(ctor:Ctor[Key_p], kwargs:dict) -> set[str]:
        """ returns any keys not expected by a dkey or dkey subclass """
        result = set(kwargs.keys() - DKeyMeta._expected_init_keys - ctor._extra_kwargs)
        return result

    ##--| Checks

    def __instancecheck__(cls, instance) -> bool: # noqa: N805
        return any(x.__instancecheck__(instance) for x in {Key_p})

    def __subclasscheck__(cls, sub) -> bool: # noqa: N805
        return cls in sub.mro()

    ##--| Utils

    @staticmethod
    def extract_raw_keys(data:str, *, implicit=False) -> tuple[API.RawKey_d]:
        """ Calls the Python format string parser to extract
        keys and their formatting/conversion specs,
        then wraps them in jgdv.structs.dkey._util.parser.API.RawKey_d's for convenience

        if 'implicit' then will parse the entire string as {str}
        """
        return tuple(DKeyMeta._parser.parse(data, implicit=implicit))

    @staticmethod
    def get_subtype(mark:KeyMark, *, multi=False) -> type:
        """
        Get the Ctor for a given mark from those registered.
        """
        ctor = None
        match mark:
            case None:
                raise ValueError(API.NoMark)
            case DKeyMark_e() as x if x is DKeyMark_e.MULTI and not multi:
                raise ValueError(API.MarkConflictsWithMulti)
            case str()|DKeyMark_e() as x if multi:
                ctor = DKeyMeta.multi_registry.get(x, None)
                ctor = ctor or DKeyMeta.single_registry.get(x, None)
            case str()|DKeyMark_e() as x:
                ctor = DKeyMeta.single_registry.get(x, None)

        if ctor is None:
            raise ValueError(API.MarkLacksACtor, mark)

        return ctor

    @staticmethod
    def register_key_type(ctor:type, mark:KeyMark, conv:Maybe[str]=None, *, multi:bool=False, force:bool=False, core:bool=False) -> None:
        """ Register a DKeyBase implementation to a mark

        Can be a single key, or a multi key,
        and can map a conversion char to the mark

        eg: "p" -> DKeyMark_e.Path -> Path[Single/Multi]Key
        """
        logging.debug("Registering: %s : %s", mark, ctor)
        match core:
            case True:
                DKeyMeta.core_registry.add(ctor)
            case _:
                pass

        match mark:
            case None:
                raise ValueError(API.RegistryLacksMark, ctor)
            case DKeyMark_e():
                pass
            case str():
                pass

        match multi:
            case True:
                target = DKeyMeta.multi_registry
            case False if ((multi_ctor:=DKeyMeta.multi_registry.get(DKeyMark_e.MULTI, None))
                           and issubclass(ctor, multi_ctor)):
                target = DKeyMeta.multi_registry
            case False:
                target = DKeyMeta.single_registry

        match target.get(mark, None):
            case type() as curr if not issubclass(ctor, curr):
                raise ValueError(API.RegistryConflict, curr, ctor, mark)
            case _:
                target[mark] = ctor

        match conv:
            case None:
                return
            case str() if len(conv) > 1:
                raise ValueError(API.ConvParamTooLong, conv)
            case str() if DKeyMeta._conv_registry.get(conv, mark) != mark :
                raise ValueError(API.ConvParamConflict, conv, DKeyMeta._conv_registry[conv])
            case str():
                DKeyMeta._conv_registry[conv] = mark

    @staticmethod
    def mark_alias(val:Any) -> Maybe[KeyMark]:  # noqa: ANN401
        """ aliases for marks """
        match val:
            case DKeyMark_e() | str():
                return val
            case builtins.str:
                return DKeyMark_e.STR
            case builtins.list:
                return DKeyMark_e.ARGS
            case builtins.dict:
                return DKeyMark_e.KWARGS
            case None:
                return DKeyMark_e.NULL
            case _:
                return None
