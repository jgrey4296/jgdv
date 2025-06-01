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

from jgdv._abstract.pre_processable import PreProcessor_p
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

##--| Body:

class DKeyRegistry:
    """ Register {mark} -> DKeyType """
    type KeyCtor = type[API.Key_p]
    type KeyDict = dict[KeyMark, KeyCtor]
    ##--|
    single           : KeyDict
    multi            : KeyDict
    core             : set[KeyCtor]
    convert          : dict[str, KeyMark]

    def __init__(self) -> None:
        self.single   = {}
        self.multi    = {}
        self.convert  = {}
        self.core     = set()

    def get_subtype(self, mark:KeyMark) -> KeyCtor:
        """
        Get the Ctor for a given mark from those registered.
        """
        match mark:
            case None:
                raise ValueError(API.NoMark)
            case str()|API.DKeyMarkAbstract_e()|type() as x if x in self.multi:
                return self.multi[x]
            case str()|API.DKeyMarkAbstract_e()|type() as x:
                return self.single[x]
            case _:
                raise KeyError(API.MarkLacksACtor, mark)

    def register_key_type(self, ctor:KeyCtor, mark:KeyMark, *, convert:Maybe[str]=None, core:bool=False) -> None:
        """ Register a DKeyBase implementation to a mark

        Can be a single key, or a multi key,
        and can map a conversion char to the mark

        eg: "p" -> DKeyMark_e.Path -> Path[Single/Multi]Key
        """
        if not mark:
            raise ValueError(API.RegistryLacksMark, ctor)

        logging.debug("Registering DKey: %s : %s", ctor, mark)
        try:
            curr = self.get_subtype(mark)
        except KeyError:
            pass
        else:
            raise ValueError(API.RegistryConflict, curr, ctor, mark)

        if core:
            self.core.add(ctor)

        match ctor:
            case API.MultiKey_p():
                self.multi[mark] = ctor
            case _:
                self.single[mark] = ctor

        match convert:
            case None:
                pass
            case str() as x if len(x) > 1:
                raise ValueError(API.ConvParamTooLong, x)
            case str() as x if self.convert.get(x, mark) != mark :
                raise ValueError(API.ConvParamConflict, x, self.convert[x])
            case str() as x:
                self.convert[x] = mark


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

    expected_kwargs      : Final[list[str]]        = API.DEFAULT_DKEY_KWARGS
   ##--|

    @override
    def pre_process(self, cls:type[T], input:Any, *args:Any, strict:bool=False, **kwargs:Any) -> PreProcessResult[T]: # type: ignore[override]
        """ Pre-process the Key text,

        Extracts subkeys, and refines the type of key to build
        """
        text       : str
        ctor       : Ctor[T]
        mark       : API.KeyMark
        inst_data  : dict = {}
        post_data  : dict = {}
        is_multi   : bool              = kwargs.pop("multi", False)
        force      : Maybe[Ctor[T]]    = kwargs.pop('force', None)
        implicit   : bool              = kwargs.pop("implicit", False)  # is key wrapped? ie: {key}
        insist     : bool              = kwargs.pop("insist", False)    # must produce key, not nullkey

        match force, kwargs.pop('mark', None):
            case type(), _:
                mark = force.MarkOf(force)
                is_multi = isinstance(force, API.MultiKey_p)
            case None, None:
                mark = API.DKeyMark_e.default()
            case None, x:
                mark = x

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
        match kwargs.pop(API.RAWKEY_ID, None) or self.extract_raw_keys(text, implicit=implicit):
            case [x]:
                inst_data[API.RAWKEY_ID] = [x]
            case [*xs]:
                inst_data[API.RAWKEY_ID] = xs
            case []:
                inst_data[API.RAWKEY_ID] = []
            case x:
                raise TypeError(type(x))

        ##--| discriminate on raw keys
        match self.discriminate_raw(inst_data[API.RAWKEY_ID], kwargs, mark=mark, is_multi=is_multi):
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
        ctor = self.select_ctor(cls, insist=insist, mark=mark, force=force)
        self.validate_init_kwargs(ctor, kwargs)
        ##--| return
        return text, inst_data, post_data, ctor

    @override
    def process(self, obj:T, *, data:Maybe[dict]=None) -> Maybe[T]:
        """ The key constructed, build slices """
        # TODO use class hook if it exists
        full        : str
        wrapped     : bool
        start       : int
        stop        : int
        key_slices  : list[slice]
        raw_keys    : list[API.RawKey_d]
        if not bool(obj.data.raw):  # Nothing to do
            return None

        key_slices  = []
        raw_keys    = []
        wrapped     = API.OBRACE in obj[:]
        if wrapped and 1 < len(obj.data.raw):
            raw_keys += obj.data.raw

        for key in raw_keys:
            if not key.key:
                continue

            full = key.joined()
            if wrapped:
                full = f"{{{full}}}"

            start = obj.index(full)
            stop  = start + len(full)
            key_slices.append(slice(start, stop))

        else:
            # TODO Add a word slice for each sub key
            obj.data.sec_words  = (tuple(range(len(obj.data.raw))),) # tuple[tuple[slice, ...]]
            obj.data.words      = tuple(key_slices)
            obj.data.flat_idx   = tuple((i,j) for i,x in enumerate(obj.data.sec_words) for j in range(len(x)))
            obj.data.sections   = (slice(0, len(obj)),) # a single, whole str slice

            return None

    @override
    def post_process(self, obj:T, data:Maybe[dict]=None) -> Maybe[T]:
        """ Build subkeys if necessary

        """
        # TODO use class hook if it exists

        # for each subkey, build it...
        key_meta : list[Maybe[str|API.Key_p]] = []
        raw : list[API.RawKey_d] = []
        if isinstance(obj, API.MultiKey_p):
            raw = obj.data.raw

        for x in raw:
            key_meta.append(x.joined())
        else:
            obj.data.meta = tuple(key_meta)
            return None

    ##--| Utils

    def discriminate_raw(self, raw_keys:Iterable[API.RawKey_d], kdata:dict, *, mark:Maybe[API.KeyMark]=None, is_multi:bool=False) -> dict:  # noqa: ARG002
        """ Take extracted keys of the text,
        and determine features of them, returning a dict,

        """
        assert(all(isinstance(x, API.RawKey_d) for x in raw_keys))
        multi_compatible  : bool  = True
        data                = {
            'mark'         : mark or DKeyMark_e.default(),
            'multi'        : is_multi,
            API.RAWKEY_ID  : raw_keys,
        }
        match raw_keys:
            case [x] if not bool(x) and bool(x.prefix) and not is_multi: # No keys found, use NullDKey
                data['mark'] = DKeyMark_e.NULL
            case [x] if is_multi and not multi_compatible: # One key, declared as a multi key, coerce to multi
                data['mark'] = DKeyMark_e.MULTI
            case [x] if is_multi: # One Key, able to be multi
                pass
            case [x] if not bool(x.prefix): # One key, no non-key text. not multi. trim it.
                data['text'] = x.direct()
                if x.is_indirect():
                    data['mark'] = DKeyMark_e.INDIRECT
                conv_mark = self.registry.convert.get(x.convert, None) # type: ignore[arg-type]
                if mark is not DKeyMark_e.default() and conv_mark and (mark != conv_mark):
                    raise ValueError(API.MarkConversionConflict, mark, conv_mark)
                elif conv_mark:
                    data['mark'] = conv_mark
            case [_, *_] if is_multi and multi_compatible: # Keys, multi compatible
                pass
            case [_, *_]: # Multiple keys found, coerce to multi
                data['mark']   = DKeyMark_e.MULTI
                data['multi']  = True
            case x:
                raise TypeError(type(x))
        ##--|
        return data

    def select_ctor(self, cls:Ctor[T], *, mark:KeyMark, force:Maybe[Ctor[T]], insist:bool) -> Ctor[T]:
        """ Select the appropriate key ctor,
        which can be forced if necessary,
        otherwise uses the mark and multi params

        """
        # Choose the sub-ctor
        if force is not None:
            assert(isinstance(force, type))
            return force

        try:
            match cls[mark]:
                case types.GenericAlias():
                    raise TypeError()
                case type() as ctor if insist and ctor.MarkOf(ctor) is DKeyMark_e.NULL:
                    raise TypeError(API.InsistentKeyFailure)
                case type() as x:
                    return cast("type[T]", x)
        except KeyError:
            return cls
        else:
            return cls

    def extract_raw_keys(self, data:str, *, implicit=False) -> tuple[API.RawKey_d, ...]:
        """ Calls the Python format string parser to extract
        keys and their formatting/conversion specs,
        then wraps them in jgdv.structs.dkey._util.parser.API.RawKey_d's for convenience

        if 'implicit' then will parse the entire string as {str}
        """
        return tuple(self.parser.parse(data, implicit=implicit))

    def mark_alias(self, val:Any) -> Maybe[KeyMark]:  # noqa: ANN401
        """ Translate an alias of a mark into the actual mark """
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


    def consume_format_params(self, spec:str) -> tuple[str, bool, bool]:
        """
          return (remaining, wrap, direct)
        """
        wrap     = 'w' in spec
        indirect = 'i' in spec
        direct   = 'd' in spec
        remaining = API.FMT_PATTERN.sub("", spec)
        assert(not (direct and indirect))
        return remaining, wrap, (direct or (not indirect))


    def validate_init_kwargs(self, ctor:type[Key_p], kwargs:dict) -> None:
        """ returns any keys not expected by a dkey or dkey subclass """
        assert(ctor is not None)
        result = set(kwargs.keys() - self.expected_kwargs - ctor._extra_kwargs)
        if bool(result):
            raise ValueError(API.UnexpectedKwargs, result)
