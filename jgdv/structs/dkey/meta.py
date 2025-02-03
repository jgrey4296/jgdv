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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Maybe, Ident
from jgdv.mixins.enum_builders import EnumBuilder_m
from jgdv._abstract.protocols import Key_p
from jgdv.mixins.annotate import SubAnnotate_m
# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

CONV_SEP        : Final[Ident]                = "!"
REDIRECT_SUFFIX : Final[Ident]                = "_"

class DKeyMark_e(EnumBuilder_m, enum.Enum):
    """
      Enums for how to use/build a dkey

    TODO refactor this to StrEnum
    """
    FREE     = enum.auto() # -> Any
    PATH     = enum.auto() # -> pl.Path
    REDIRECT = enum.auto() # -> DKey
    STR      = enum.auto() # -> str
    CODE     = enum.auto() # -> coderef
    TASK     = enum.auto() # -> taskname
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

    def __call__(cls, *args, **kwargs):
        """ Runs on class instance creation
        skips running cls.__init__, allowing cls.__new__ control
        (ie: Allows The DKey accessor t
        """
        # TODO maybe move dkey discrimination from dkey.__new__ to here
        return cls.__new__(cls, *args, **kwargs)

    def __instancecheck__(cls, instance):
        return any(x.__instancecheck__(instance) for x in {Key_p})

    def __subclasscheck__(cls, sub):
        candidates = {Key_p}
        return any(x in candidates for x in sub.mro())

class DKey(SubAnnotate_m, metaclass=DKeyMeta):
    """ A facade for DKeys and variants.
      Implements __new__ to create the correct key type, from a string, dynamically.

    TODO use subclass annotation

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
    mark                                     = DKeyMark_e
    _single_registry : dict[DKeyMark_e,type] = {}
    _multi_registry  : dict[DKeyMark_e,type] = {}
    _conv_registry   : dict[str, DKeyMark_e] = {}
    _parser          : Maybe[type]           = None

    def __new__(cls, data:str|DKey|pl.Path|dict, **kwargs) -> DKey:
        """
          fmt : Format parameters. used from multi key subkey construction
          conv : Conversion parameters. used from multi key subkey construction.
          implicit: For marking a key as an implicit key, with no extra text around it
          mark     : Enum for explicitly setting the key type
        """
        assert(cls is DKey)
        implicit : bool              = kwargs.get("implicit", False)
        mark     : Maybe[DKeyMark_e] = kwargs.get("mark", None)
        conv     : Maybe[str]        = kwargs.get("conv", None)

        if not isinstance(mark, None|DKeyMark_e):
            raise TypeError("Mark must be a DKeyMark_e", mark)

        # Early escape check
        match data:
            case DKey() if mark is None or mark == data._mark:
                # Already have a dkey, not re-marking it
                return data
            case DKey() | pl.Path():
                # Got a dkey needing remarking, or a path
                data = str(data)
            case _:
                pass

        # Extract subkeys
        data, mark, fparams, is_multi = cls._extract_subkeys(data, implicit=implicit, mark=mark, conv=conv)

        # Get the initiator using the mark
        subtype_cls = DKey.get_subtype(mark, multi=is_multi)

        # Build a str with the subtype_cls and data
        # (Has to be str.__new__)
        result           = str.__new__(subtype_cls, data)
        # Update kwargs with more accurate data
        if mark:
            kwargs['mark']   = mark
        if fparams:
            kwargs['fmt']    = fparams
        # Init the key
        result.__init__(data, **kwargs)

        return result

    @classmethod
    def _extract_subkeys(cls, data, *, implicit=False, mark=None, conv=None) -> tuple[str, str, DKeyMark_e, bool]:
        """ figure out if they key is going to be a multikey """
        has_text : bool
        s_keys : list
        has_text, s_keys = DKey._parser.Parse(data)
        active_keys      = [x for x in s_keys if bool(x.key)]
        use_multi_ctor   = len(active_keys) > 0
        fparams          = None
        match len(active_keys):
            case 0 if not implicit and mark is not DKey.mark.PATH:
                # Just Text, its not a key
                mark = DKeyMark_e.NULL
            case _ if mark is DKey.mark.MULTI:
                # Explicit override
                pass
            case 0:
                # Handle Single, implicit Key variants
                data, mark     = cls._parse_single_key_params_to_mark(data, conv, fallback=mark)
            case 1 if not has_text:
                # One Key, no other text, so make a solo key
                solo           = s_keys[0]
                fparams        = solo.format
                data, mark     = cls._parse_single_key_params_to_mark(solo.key, solo.conv, fallback=mark)
                use_multi_ctor = False
            case x if not has_text and s_keys[0].conv == "p":
                mark = DKeyMark_e.PATH
            case _ if implicit:
                raise ValueError("Implicit instruction for multikey", data, s_keys, active_keys)
            case _ if has_text and mark is None:
                mark = DKey._conv_registry.get(DKeyMark_e.MULTI)
            case x if x >= 1 and mark is None:
                mark = DKeyMark_e.MULTI

        return (data, mark, fparams, use_multi_ctor)

    @classmethod
    def _parse_single_key_params_to_mark(cls, data, conv, fallback=None) -> tuple[str, Maybe[DKeyMark_e]]:
        """ Handle single, implicit key's and their parameters.
          Explicitly passed in conv take precedence

          eg:
          blah -> FREE
          blah_ -> REDIRECT
          blah!p -> PATH
          ...
        """
        key = data
        if not conv and CONV_SEP in data:
            key, conv = data.split(CONV_SEP)

        assert(conv is None or len(conv ) < 2), conv
        result = DKey._conv_registry.get(conv, DKeyMark_e.FREE)

        match fallback, result:
            case _, _ if key.endswith(REDIRECT_SUFFIX):
                return key, DKeyMark_e.REDIRECT
            case None, x:
                return (key, x)
            case x, DKeyMark_e.FREE:
                return (key, x)
            case x, y if x == y:
                return (key, x)
            case x, y:
                raise ValueError("Conflicting conversion parameters", x, y, data)

    @staticmethod
    def get_subtype(mark, *, multi:bool=False) -> type:
        """ Get the Ctor for a key, with a fallback to Multi or Free ctors"""
        match multi:
            case True:
                ctor = DKey._multi_registry.get(mark, None)
                return ctor or DKey._multi_registry[DKeyMark_e.MULTI]
            case False:
                ctor = DKey._single_registry.get(mark, None)
                return ctor or DKey._single_registry[DKeyMark_e.FREE]

    @staticmethod
    def register_key(ctor:type, mark:DKeyMark_e, tparam:Maybe[str]=None, multi:bool=False):
        """ Register a DKeyBase implementation to a mark

        Can be a single key, or a multi key,
        and can map a conversion char to the mark

        eg: "p" -> DKeyMark_e.Path -> Path[Single/Multi]Key
        """
        match mark:
            case None:
                pass
            case DKey.mark.NULL:
                DKey._multi_registry[mark]  = ctor
                DKey._single_registry[mark] = ctor
            case _ if multi:
                DKey._multi_registry[mark]  = ctor
            case _:
                DKey._single_registry[mark] = ctor

        match tparam:
            case None:
                return
            case str() if len(tparam) > 1:
                raise ValueError("conversion parameters for DKey's can't be more than a single char")
            case str():
                DKey._conv_registry[tparam] = mark

    @staticmethod
    def register_parser(fn:type, *, force:bool=False):
        """ Dependency inject a formatter capable of parsing type conversion and formatting parameters from strings,
          for DKey to use when constructing keys.
          Most likely will be DKeyFormatter.

          Expects the fn to return tuple[bool, list]
        """
        match DKey._parser:
            case None:
                DKey._parser = fn
            case _ if force:
                DKey._parser = fn
            case _:
                pass


    @staticmethod
    def MarkOf(target) -> DKeyMark_e:
        """ Get the mark of the key type or instance """
        match target:
            case DKey():
                return target._mark
            case type() if issubclass(target, DKey):
                return target._mark
            case _:
                raise TypeError("Tried to retrieve a mark from an unknown type")
