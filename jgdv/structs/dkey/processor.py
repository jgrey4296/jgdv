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
from ._interface import DKeyMark_e, ExpInst_d, Key_p
# ##-- end 1st party imports

from jgdv._abstract.pre_processable import PreProcessor_p, InstanceData, PostInstanceData
from jgdv.structs.strang import _interface as StrangAPI  # noqa: N812
from jgdv.structs.strang.processor import StrangBasicProcessor

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

if TYPE_CHECKING:
   from jgdv import Maybe, Ident, Ctor
   import enum
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Sized
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   from string import Formatter

   from jgdv._abstract.pre_processable import PreProcessResult
   from ._interface import KeyMark

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

StrMeta : Final[type] = type(str)

##--| Body:

class DKeyRegistry:
    type KeyCtor = type[API.Key_p]
    type KeyDict = dict[KeyMark, KeyCtor]
    ##--|
    single           : KeyDict
    multi            : KeyDict
    core             : set[KeyCtor]
    convert          : dict[str, KeyMark]
    expected_kwargs  : Final[list[str]]  = API.DEFAULT_DKEY_KWARGS

    def __init__(self) -> None:
        self.single   = {}
        self.multi    = {}
        self.convert  = {}
        self.core     = set()

    def get_subtype(self, mark:KeyMark, *, multi=False) -> type[API.Key_p]:
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
                ctor = self.multi.get(x, None)
                ctor = ctor or self.single.get(x, None)
            case str()|DKeyMark_e() as x:
                ctor = self.single.get(x, None)

        if ctor is None:
            raise ValueError(API.MarkLacksACtor, mark)

        return ctor

    def register_key_type(self, ctor:type, mark:KeyMark, convert:Maybe[str]=None, *, multi:bool=False, core:bool=False) -> None:  # noqa: PLR0912
        """ Register a DKeyBase implementation to a mark

        Can be a single key, or a multi key,
        and can map a conversion char to the mark

        eg: "p" -> DKeyMark_e.Path -> Path[Single/Multi]Key
        """
        logging.debug("Registering: %s : %s", mark, ctor)
        match core:
            case True:
                self.core.add(ctor)
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
                target = self.multi
            case False if ((multi_ctor:=self.multi.get(DKeyMark_e.MULTI, None))
                           and issubclass(ctor, multi_ctor)):
                target = self.multi
            case False:
                target = self.single

        match target.get(mark, None):
            case type() as curr if not issubclass(ctor, curr):
                raise ValueError(API.RegistryConflict, curr, ctor, mark)
            case _:
                target[mark] = ctor

        match convert:
            case None:
                pass
            case str() as x if len(x) > 1:
                raise ValueError(API.ConvParamTooLong, x)
            case str() as x if self.convert.get(x, mark) != mark :
                raise ValueError(API.ConvParamConflict, x, self.convert[x])
            case str() as x:
                self.convert[x] = mark

    def validate_init_kwargs(self, ctor:type[Key_p], kwargs:dict) -> None:
        """ returns any keys not expected by a dkey or dkey subclass """
        assert(ctor is not None)
        result = set(kwargs.keys() - self.expected_kwargs - ctor._extra_kwargs)
        if bool(result):
            raise ValueError(API.UnexpectedKwargs, result)

class DKeyProcessor[T:API.Key_p](PreProcessor_p):
    """
      The Metaclass for keys, which ensures that subclasses of DKeyBase
      are API.Key_p's, despite there not being an actual subclass relation between them.

    This allows DKeyBase to actually bottom out at str
    """

    parser               : ClassVar[DKeyParser]    = DKeyParser()
    registry             : ClassVar[DKeyRegistry]  = DKeyRegistry()
    # Use the default str hash method

    _expected_init_keys  : ClassVar[list[str]]     = API.DEFAULT_DKEY_KWARGS[:]

   ##--| Registry Access

    def get_subtype(self, *args, **kwargs) -> type[T]:
        return cast("type[T]", self.registry.get_subtype(*args, **kwargs))

    def register_key_type(self, *args, **kwargs) -> None:
        self.registry.register_key_type(*args, **kwargs)

    ##--|

    @override
    def pre_process(self, cls:type[T], input:Any, *args:Any, strict:bool=False, **kwargs:Any) -> PreProcessResult[T]: # type: ignore[override]
        """ Pre-process the Key text,

        Extracts subkeys, and refines the type of key to build
        """
        raw        : tuple[API.RawKey_d, ...]
        text       : str
        ctor       : Ctor[T]
        inst_data  : InstanceData      = InstanceData({})
        post_data  : PostInstanceData  = PostInstanceData({})
        is_multi   : bool              = False
        implicit   : bool              = kwargs.pop("implicit", False)  # is key wrapped? ie: {key}
        insist     : bool              = kwargs.pop("insist", False)    # must produce key, not nullkey
        mark       : API.KeyMark       = kwargs.pop("mark", API.DKeyMark_e.default())

        # TODO use class hook if it exists

        ##--| Pre-clean text
        match input:
            case str():
                text = input.strip()
            case pl.Path():
                text = str(input)
            case _:
                text = str(input)

        ##--| Get pre-parsed keys
        match kwargs.pop(API.RAWKEY_ID, None):
            case tuple() as xs:
                raw = xs
            case None:
                raw = self.extract_raw_keys(text, implicit=implicit)

        inst_data['raw'] = raw
        ##--| discriminate raw keys
        match self.discriminate_raw(raw, kwargs, mark=mark):
            case dict() as extra:
                # use overrides
                is_multi  = extra.pop("multi", is_multi)
                mark      = extra.pop("mark",  mark)
                text      = extra.pop('text', text)
                inst_data.update(extra)
            case _:
                raise ValueError()
        ##--|
        assert(bool(text))
        assert(bool(inst_data))
        ctor = self.select_ctor(cls, insist=insist, mark=mark, multi=is_multi, force=kwargs.pop('force', None))
        self.registry.validate_init_kwargs(ctor, kwargs)
        ##--| return
        return text, inst_data, post_data, ctor

    @override
    def process(self, obj:T, *, data:Maybe[dict]=None) -> Maybe[T]:
        """ The key constructed, build slices """
        # TODO use class hook if it exists

        if not bool(obj.data.raw): # Nothing to do
            return None

        # TODO Add a word slice for each sub key
        obj.data.sec_words  = () # tuple[tuple[slice, ...]]
        obj.data.flat_idx   = tuple((i,j) for i,x in enumerate(obj.data.sec_words) for j in range(len(x)))
        obj.data.sections   = (slice(0, len(obj)),) # a single, whole str slice
        obj.data.words      = ()

        return None

    @override
    def post_process(self, obj:T, data:Maybe[dict]=None) -> Maybe[T]:
        """
        Set metadata for each subkey
        """
        # TODO use class hook if it exists

        # for each subkey...

        return None
    ##--| Utils

    def discriminate_raw(self, raw_keys:Iterable[API.RawKey_d], kdata:dict, *, mark:Maybe[API.KeyMark]=None) -> dict:
        """ Take extracted keys of the text,
        and determine features of them, returning a dict,

        """
        assert(all(isinstance(x, API.RawKey_d) for x in raw_keys))
        is_multi          : bool  = kdata.pop("multi", False)
        multi_compatible  : bool  = mark is None or mark in self.registry.multi
        data                = {
            'mark'         : mark or DKeyMark_e.default(),
            'multi'        : is_multi,
            API.RAWKEY_ID  : raw_keys,
        }
        match raw_keys:
            case [x] if not bool(x) and bool(x.prefix) and not is_multi: # No keys found, use NullDKey
                data['mark'] = DKeyMark_e.NULL
            case [x] if is_multi and not multi_compatible: # One key, declared as a multi key
                data['mark'] = DKeyMark_e.MULTI
            case [x] if is_multi: # One Key, able to be multi
                pass
            case [x] if not bool(x.prefix) and x.is_indirect(): # One Key_ found with no extra text
                # so truncate to just the exact key
                data['mark'] = DKeyMark_e.INDIRECT
                data['text'] = x.indirect()
            case [x] if not bool(x.prefix): # one key, no extra text
                conv_mark = self.registry.convert.get(x.conv, None) # type: ignore[arg-type]
                if conv_mark and (mark != conv_mark):
                    raise ValueError(API.MarkConversionConflict, mark, conv_mark)
                elif conv_mark:
                    data['mark'] = conv_mark

                # so truncate to just the exact key
                data['text'] = x.direct()
            case [_, *_] if is_multi and multi_compatible: # Keys, multi compatible
                pass
            case [_, *_]: # Multiple keys found
                data['mark']   = DKeyMark_e.MULTI
                data['multi']  = True
            case x:
                raise TypeError(type(x))
        ##--|
        return data

    def select_ctor(self, cls:Maybe[Ctor[T]], *, mark:KeyMark, multi:bool, force:Maybe[Ctor[T]], insist:bool) -> Ctor[T]:
        """ Select the appropriate key ctor,
        which can be forced if necessary,
        otherwise uses the mark and multi params

        """
        # Choose the sub-ctor
        if force is not None:
            assert(isinstance(force, type))
            return force

        match self.registry.get_subtype(mark, multi=multi):
            case type() as ctor if insist and ctor.MarkOf() is DKeyMark_e.NULL:
                raise TypeError(API.InsistentKeyFailure)
            case type() as x:
                return cast("type[T]", x)

        return cls

    def extract_raw_keys(self, data:str, *, implicit=False) -> tuple[API.RawKey_d, ...]:
        """ Calls the Python format string parser to extract
        keys and their formatting/conversion specs,
        then wraps them in jgdv.structs.dkey._util.parser.API.RawKey_d's for convenience

        if 'implicit' then will parse the entire string as {str}
        """
        return tuple(self.parser.parse(data, implicit=implicit))

    def mark_alias(self, val:Any) -> Maybe[KeyMark]:  # noqa: ANN401
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
