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
from jgdv._abstract.protocols import Key_p
from jgdv.mixins.enum_builders import EnumBuilder_m
from jgdv.mixins.annotate import SubAnnotate_m
from ._parser import DKeyParser
from ._expinst import ExpInst
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
# from dataclasses import InitVar, dataclass, field
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
from jgdv import Maybe

if TYPE_CHECKING:
   from jgdv import Ident
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, Mapping, MutableMapping, Hashable
   from string import Formatter

   type KeyMark = DKeyMark_e|str
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class DKeyMark_e(EnumBuilder_m, enum.StrEnum):
    """
      Enums for how to use/build a dkey

    """
    FREE     = "free"
    PATH     = enum.auto() # -> pl.Path
    INDIRECT = "indirect"
    STR      = enum.auto() # -> str
    CODE     = enum.auto() # -> coderef
    IDENT    = enum.auto() # -> taskname
    ARGS     = enum.auto() # -> list
    KWARGS   = enum.auto() # -> dict
    POSTBOX  = enum.auto() # -> list
    NULL     = enum.auto() # -> None
    MULTI    = enum.auto()

    default  = FREE

class DKeyMeta(type(str)):
    """
      The Metaclass for keys, which ensures that subclasses of DKeyBase
      are DKey's, despite there not being an actual subclass relation between them.

    This allows DKeyBase to actually bottom out at str
    """

    _single_registry    : ClassVar[dict[KeyMark,type]] = {}
    _multi_registry     : ClassVar[dict[KeyMark,type]] = {}
    _conv_registry      : ClassVar[dict[str, KeyMark]] = {}
    _parser             : ClassVar[Formatter]             = DKeyParser()

    # Use the default str hash method
    _rawkey_id          : ClassVar[str]                = "_rawkeys"
    _force_type_id      : ClassVar[str]                = "force"
    _expected_init_keys : ClassVar[list[str]]          = ["ctor", "check", "mark", "fallback",
                                                          "max_exp", "fmt", "help", "force",
                                                          "implicit", "conv", _rawkey_id,
                                                          ]

    def __call__(cls, *args, **kwargs):
        """ Runs on class instance creation
        skips running cls.__init__, allowing cls.__new__ control
        (ie: Allows The DKey accessor t
        """
        match kwargs:
            case {"insist": bool() as insist}:
                del kwargs['insist']
            case _:
                insist = False
                
        # TODO maybe move dkey discrimination from dkey.__new__ to here
        new_key = None
        match args:
            case [DKey() as x] if kwargs.get("mark", None) is None:
                new_key = x
            case [str()|DKey() as x]:
                new_key = cls.__new__(cls, *args, **kwargs)
            case x:
                raise TypeError("Unknown type passed to construct dkey", x)
            
        match new_key:
            case DKey() as x if insist and DKey.MarkOf(x) is DKeyMark_e.NULL:
                raise TypeError("An insistent key was not built", x)
            case DKey():
                return new_key
            case _:
                raise TypeError("No key was built", args)

    def __instancecheck__(cls, instance):
        return any(x.__instancecheck__(instance) for x in {Key_p})

    def __subclasscheck__(cls, sub):
        if cls is DKey:
            bases = [DKeyMeta.get_subtype(DKeyMark_e.NULL),
                     DKeyMeta.get_subtype(DKeyMark_e.FREE),
                     DKeyMeta.get_subtype(DKeyMark_e.INDIRECT),
                     DKeyMeta.get_subtype(DKeyMark_e.MULTI, multi=True),
                     ]
            for x in bases:
                 if issubclass(sub, x):
                     return True
            else:
                return False
        return any(sub in x for x in cls.mro())

    @staticmethod
    def extract_raw_keys(data:str, *, implicit=False) -> list:
        """ Calls the Python format string parser to extract
        keys and their formatting/conversion specs.

        if 'implicit' then will parse the entire string as {str}
        """
        return list(DKeyMeta._parser.parse(data, implicit=implicit))

    @staticmethod
    def get_subtype(mark:KeyMark, *, multi=False) -> type:
        """
        Get the Ctor for a given mark from those registered.
        """
        ctor = None
        match mark:
            case None:
                raise ValueError("Mark has to be a value")
            case DKeyMark_e() as x if x is DKeyMark_e.MULTI and not multi:
                raise ValueError("Mark is MULTI but multi=False")
            case str()|DKeyMark_e() as x if multi:
                ctor = DKeyMeta._multi_registry.get(x, None)
                ctor = ctor or DKeyMeta._single_registry.get(x, None)
            case str()|DKeyMark_e() as x:
                ctor = DKeyMeta._single_registry.get(x, None)

        if ctor is None:
            raise ValueError("Couldn't find a ctor for mark", mark)

        return ctor

    @staticmethod
    def register_key_type(ctor:type, mark:KeyMark, conv:Maybe[str]=None, multi:bool=False) -> None:
        """ Register a DKeyBase implementation to a mark

        Can be a single key, or a multi key,
        and can map a conversion char to the mark

        eg: "p" -> DKeyMark_e.Path -> Path[Single/Multi]Key
        """
        logging.debug("Registering: %s : %s", mark, ctor)
        match mark:
            case None:
                raise ValueError("Can't register when the mark is None", ctor)
            case DKeyMark_e():
                pass
            case str():
                pass


        match multi:
            case True:
                target = DKeyMeta._multi_registry
            case False if ((multi_ctor:=DKeyMeta._multi_registry.get(DKeyMark_e.MULTI, None))
                           and issubclass(ctor, multi_ctor)):
                target = DKeyMeta._multi_registry
            case False:
                target = DKeyMeta._single_registry

        match target.get(mark, None):
            case type() as curr if not issubclass(ctor, curr):
                raise ValueError("DKey Registry conflict", curr, ctor, mark)
            case _:
                target[mark] = ctor

        match conv:
            case None:
                return
            case str() if len(conv) > 1:
                raise ValueError("conversion parameters for DKey's can't be more than a single char")
            case str():
                DKeyMeta._conv_registry[conv] = mark

class DKey(metaclass=DKeyMeta):
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
      """
    Mark    : ClassVar[enum.Enum] = DKeyMark_e
    ExpInst : ClassVar[type]      = ExpInst
    __match_args = ("_mark",)

    def __class_getitem__(cls, name) -> type:
        return DKeyMeta.get_subtype(name, multi=True)

    def __new__(cls, data, **kwargs) -> DKey:
        # Get Raw Key information to choose the mark
        # put the rawkey data into _rawkey_id to save on reparsing later
        multi_key = kwargs.get("mark", None) in DKeyMeta._multi_registry
        # Use passed in keys if they are there
        if not (raw_keys:=kwargs.get(DKeyMeta._rawkey_id, None)):
            raw_keys = DKeyMeta.extract_raw_keys(data, implicit=kwargs.get("implicit", False))

        match raw_keys:
            case [x] if not bool(x) and bool(x.prefix) and not multi_key:
                # No key found
                mark = DKeyMark_e.NULL
                kwargs[DKeyMeta._rawkey_id] = [x]
            case [x] if multi_key:
                mark = kwargs.get("mark", DKeyMark_e.MULTI)
                kwargs[DKeyMeta._rawkey_id ] = [x]
            case [x] if not bool(x.prefix) and x.is_indirect():
                # One Key_ found with no extra text
                mark = DKeyMark_e.INDIRECT
                # so truncate to just the exact key
                data = x.indirect()
                kwargs[DKeyMeta._rawkey_id ] = [x]
            case [x] if not bool(x.prefix):
                # one key, no extra text
                kw_mark      = kwargs.get("mark", None)
                conv_mark = DKeyMeta._conv_registry.get(x.conv, None)
                if (kw_mark and conv_mark):
                    raise ValueError("Kwd Mark/Conversion Conflict", kw_mark, conv_mark)
                mark = kw_mark or conv_mark or DKeyMark_e.FREE

                # so truncate to just the exact key
                data = x.direct()
                kwargs[DKeyMeta._rawkey_id ] = [x]
            case [*xs]:
                # Multiple keys found
                mark = kwargs.get("mark", DKeyMark_e.MULTI)
                kwargs[DKeyMeta._rawkey_id] = xs
                multi_key = True


        # Choose the sub-ctor
        match kwargs.get(DKeyMeta._force_type_id, None):
            case type() as x:
                # sub type has been forced
                del kwargs[DKeyMeta._force_type_id]
                subtype_cls = x
            case None:
                subtype_cls       : type = DKeyMeta.get_subtype(mark, multi=multi_key)

        # Build a str with the subtype_cls and data
        # (Has to be str.__new__ for reasons)
        result           = str.__new__(subtype_cls, data)
        
        match list(kwargs.keys() - DKeyMeta._expected_init_keys):
            case []:
                pass
            case [*xs]:
                raise ValueError("Key got unexpected kwargs", data, xs)
        result.__init__(data, **kwargs)

        return result

    @staticmethod
    def MarkOf(target:DKey) -> KeyMark:
        """ Get the mark of the key type or instance """
        match target:
            case DKey():
                return target._mark
            case type() if issubclass(target, DKey):
                return target._mark
            case _:
                raise TypeError("Tried to retrieve a mark from an unknown type")
