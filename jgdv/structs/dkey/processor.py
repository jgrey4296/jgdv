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
from jgdv._abstract.pre_processable import PreProcessor_p
from jgdv.mixins.annotate import SubAlias_m
from jgdv.structs.strang import _interface as StrangAPI  # noqa: N812
from jgdv.structs.strang.processor import StrangBasicProcessor

# ##-- end 1st party imports

from . import _interface as API  # noqa: N812
from ._interface import DKeyMark_e, Key_p
from ._util._interface import ExpInst_d
from ._util.parser import DKeyParser

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
from collections.abc import Mapping

if TYPE_CHECKING:
   from jgdv import Maybe, Ident, Ctor
   import enum
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Sized
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, MutableMapping, Hashable
   from string import Formatter

   from jgdv._abstract.pre_processable import PreProcessResult
   from ._interface import KeyMark

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Body:

class DKeyProcessor[T:API.Key_p](PreProcessor_p):
    """
      The Metaclass for keys, which ensures that subclasses of DKeyBase
      are API.Key_p's, despite there not being an actual subclass relation between them.

    This allows DKeyBase to actually bottom out at str
    """

    parser               : ClassVar[DKeyParser]    = DKeyParser()
    _expected_init_keys  : ClassVar[list[str]]     = API.DEFAULT_DKEY_KWARGS[:]

    expected_kwargs      : Final[list[str]]        = API.DEFAULT_DKEY_KWARGS
    convert_mapping      : dict[str, KeyMark]
    ##--|

    def __init__(self) -> None:
        self.convert_mapping = {}

    @override
    def pre_process(self, cls:type[T], input:Any, *args:Any, strict:bool=False, **kwargs:Any) -> PreProcessResult[T]: # type: ignore[override]  # noqa: PLR0912, PLR0915
        """ Pre-process the Key text,

        Extracts subkeys, and refines the type of key to build
        """
        text         : str
        ctor         : Ctor[T]
        mark         : API.KeyMark
        spec_mark    : API.KeyMark
        format_mark  : Maybe[API.KeyMark]
        ##--|
        inst_data    : dict            = {}
        post_data    : dict            = {}
        force        : Maybe[Ctor[T]]  = kwargs.pop('force', None)
        implicit     : bool            = kwargs.pop("implicit", False)  # is key wrapped? ie: {key}
        insist       : bool            = kwargs.pop("insist", False)    # must produce key, not nullkey

        # TODO handle generic aliases by using the arg as instance expansion type
        match force, kwargs.pop('mark', None):
            case type(), _:
                spec_mark = cls.MarkOf(force)
            case None, None:
                spec_mark = cls.MarkOf(cls)
            case None, x:
                spec_mark = x
            case _:
                spec_mark = cls.MarkOf(cls)

        ##--|
        if spec_mark is None:
            spec_mark = API.DKeyMark_e.default()
        # TODO use class hook if it exists

        ##--| Pre-clean text
        match input:
            case str():
                text = input.strip()
            case pl.Path():
                text = str(input).strip()
            case _:
                text = str(input).strip()

        # Early exit if the text is empty:
        if not bool(text):
            inst_data['mark'] = None
            ctor = self.select_ctor(cls, mark=False, force=None, insist=False)
            return str(input), inst_data, post_data, ctor

        ##--| Get pre-parsed keys
        match kwargs.pop(API.RAWKEY_ID, None) or self.extract_raw_keys(text, implicit=implicit):
            case [x]:
                inst_data[API.RAWKEY_ID] = [x]
            case [*xs]:
                inst_data[API.RAWKEY_ID] = xs
            case []:
                inst_data[API.RAWKEY_ID] = []
            case x:
                msg = "No raw keys were able to be extracted"
                raise TypeError(msg, type(x))

        ##--| discriminate on raw keys
        match self.inspect_raw(inst_data[API.RAWKEY_ID], kwargs):
            case x, y:
                text = x or text
                format_mark = y
            case x:
                msg = "Inspecting raw keys failed"
                raise ValueError(msg, x)
        ##--|
        match spec_mark, format_mark:
            case type() as x, _:
                mark = x
            case x, None:
                mark = x
            case x, y if x == y:
                mark = x
            case x, y if y == DKeyMark_e.null() and x != DKeyMark_e.multi():
                assert(y is not None)
                mark = y
            case x, y if x is DKeyMark_e.default():
                assert(y is not None)
                mark = y
            case str() as x, _ if x not in DKeyMark_e:
                mark = x
            case _, y:
                assert(y is not None)
                mark = y


        assert(bool(text))
        assert(bool(inst_data))
        ctor = self.select_ctor(cls, insist=insist, mark=mark, force=force)
        self.validate_init_kwargs(ctor, kwargs)
        assert(issubclass(ctor, SubAlias_m))
        inst_data['mark'] = ctor.cls_annotation()
        if DKeyMark_e.multi() in [format_mark, spec_mark] and not issubclass(ctor, API.MultiKey_p):
            msg = "a multi key was specified by a mark, but the ctor isnt a multi key"
            raise ValueError(msg, spec_mark, format_mark)
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
        # for each subkey, build it...
        x : Any
        key_meta : list[Maybe[str|API.Key_p]] = []
        raw : list[API.RawKey_d] = []
        if isinstance(obj, API.MultiKey_p):
            raw = obj.data.raw

        for x in raw:
            key_meta.append(x.joined())
        else:
            obj.data.meta = tuple(key_meta)

        match getattr(obj, "_post_process_h", None):
            case hook if  callable(hook):
                hook(data)
            case None:
                pass
            case x:
                raise TypeError(type(x))

        return None
    ##--| Utils

    def inspect_raw(self, raw_keys:Iterable[API.RawKey_d], kdata:dict) -> tuple[Maybe[str], Maybe[API.KeyMark]]:  # noqa: ARG002
        """ Take extracted keys of the text,
        and determine features of them.
        can return modified text, and a mark

        """
        assert(all(isinstance(x, API.RawKey_d) for x in raw_keys))
        format_mark  : Maybe[API.KeyMark]  = None
        text         : Maybe[str]          = None
        match raw_keys:
            case [x] if not bool(x.key) and bool(x.prefix): # No keys found, use NullDKey
                format_mark  = False
            case [x] if not bool(x.prefix):  # One key, no non-key text. trim it.
                if x.convert and x.convert in self.convert_mapping:
                    format_mark = self.convert_mapping[x.convert]
                if x.is_indirect():
                    format_mark = Mapping
                text = x.direct()
            case [_, *_]: # Multiple keys found, coerce to multi
                format_mark = list
            case []: # No Keys
                pass
            case x:
                msg = "Unrecognised raw keys type"
                raise TypeError(msg, type(x))
        ##--|
        return text, format_mark

    def select_ctor(self, cls:Ctor[T], *, mark:KeyMark, force:Maybe[Ctor[T]], insist:bool) -> Ctor[T]:
        """ Select the appropriate key ctor,
        which can be forced if necessary,
        otherwise uses the mark and multi params

        """
        # Choose the sub-ctor
        assert(issubclass(cls, SubAlias_m))
        if force is not None:
            assert(isinstance(force, type)), force
            return force

        try:
            match cls._retrieve_subtype(mark):
                case types.GenericAlias() as x:
                    return x
                case type() as ctor if insist and ctor.MarkOf(ctor) is cls.Marks.null():
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


    def register_convert_param(self, cls:type[API.Key_p], convert:Maybe[str]) -> None:
        match convert:
            case str() as x if x in self.convert_mapping:
                msg = "Convert Mapping Already Registered"
                raise KeyError(msg, x, self.convert_mapping[x])
            case str() as x:
                self.convert_mapping[x] = cls.MarkOf(cls) # type: ignore[arg-type]
            case _:
                pass
