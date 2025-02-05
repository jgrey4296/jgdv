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
import string
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import sh

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv.structs.dkey._meta import DKey, DKeyMark_e
from jgdv.structs.dkey._parser import RawKey
from jgdv._abstract.protocols import Key_p, SpecStruct_p
from jgdv.util.chain_get import ChainedKeyGetter
from jgdv.structs.chainguard import ChainGuard
from jgdv.structs.dkey._expander import _DKeyFormatter_Expansion_m

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
    from jgdv import Ident, FmtStr, Rx, RxStr, Func
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__file__)
##-- end logging

MAX_KEY_EXPANSIONS  : Final[int]                   = 200

FMT_PATTERN         : Final[Rx]                    = re.compile("[wdi]+")
MAX_DEPTH           : Final[int]                   = 10

chained_get         : Func                         = ChainedKeyGetter.chained_get

class _DKeyFormatterEntry_m:
    """ Mixin to make DKeyFormatter a singleton with static access

      and makes the formatter a context manager, to hold the current data sources
      """
    _instance     : ClassVar[Self]      = None

    sources       : list                = []
    fallback      : Any                 = None

    rec_remaining : int                 = MAX_KEY_EXPANSIONS

    _entered      : bool                = False
    _original_key : str|Key_p           = None

    @classmethod
    def Parse(cls, key:Key_p|pl.Path) -> tuple(bool, list[RawKey]):
        """ Use the python c formatter parser to extract keys from a string
          of form (prefix, key, format, conversion)

          Returns: (bool: non-key text), list[(key, format, conv)]

          see: cpython Lib/string.py
          and: cpython Objects/stringlib/unicode_format.h

          eg: '{test:w} :: {blah}' -> False, [('test', Any, Any), ('blah', Any, Any)]
          """
        if not cls._instance:
            cls._instance = cls()

        assert(key is not None)
        try:
            match key:
                case str() | Key_p():
                    # formatter.parse returns tuples of (literal, key, format, conversion)
                    result = list(RawKey(prefix=x[0],
                                              key=x[1] or "",
                                              format=x[2] or "",
                                              conv=x[3] or "")
                                  for x in cls._instance.parse(key))
                    non_key_text = any(bool(x.prefix) for x in result)
                    return non_key_text, [x for x in result]
                case _:
                    raise TypeError("Unknown type found", key)
        except ValueError:
            return True, []

    @classmethod
    def expand(cls, key:Key_p, *, sources=None, max=None, **kwargs) -> Maybe[Any]:
        """ static method to a singleton key formatter """
        if not cls._instance:
            cls._instance = cls()

        fallback = kwargs.get("fallback", None)
        with cls._instance(key=key, sources=sources, rec=max, intent="expand") as fmt:
            result = fmt._expand(key, fallback=fallback)
            logging.debug("Expansion Result: %s", result)
            return result

    @classmethod
    def redirect(cls, key:Key_p, *, sources=None, **kwargs) -> list[Key_p|str]:
        """ static method to a singleton key formatter """
        if not cls._instance:
            cls._instance = cls()

        assert(isinstance(key, DKey))

        if kwargs.get("fallback", None):
            raise ValueError("Fallback values for redirection should be part of key construction", key)
        with cls._instance(key=key, sources=sources, rec=1, intent="redirect") as fmt:
            result = fmt._try_redirection(key)
            logging.debug("Redirection Result: %s", result)
            return result

    @classmethod
    def fmt(cls, key:Key_p|str, /, *args, **kwargs) -> str:
        """ static method to a singleton key formatter """
        if not cls._instance:
            cls._instance = cls()

        spec                   = kwargs.get('spec',     None)
        state                  = kwargs.get('state',    None)
        fallback               = kwargs.get("fallback", None)

        with cls._instance(key=key, sources=[spec, state], fallback=fallback, intent="format") as fmt:
            return fmt.format(key, *args, **kwargs)

    def __call__(self, *, key=None, sources=None, fallback=None, rec=None, intent=None, depth=None) -> Self:
        if self._entered:
            # Create a new temporary instance
            return self.__class__()(key=key or self._original_key,
                                    sources=sources or self.sources,
                                    fallback=fallback or self.fallback,
                                    intent=intent or self._intent,
                                    depth=depth or self._depth+1)
        self._entered          = True
        self._original_key     = key
        self.sources           = list(sources)
        self.fallback          = fallback
        self.rec_remaining     = rec or MAX_KEY_EXPANSIONS
        self._intent           = intent
        self._depth            = depth or 1
        return self

    def __enter__(self) -> Self:
        logging.debug("--> (%s) Context for: %s", self._intent, self._original_key)
        logging.debug("Using Sources: %s", self.sources)
        if self._depth > MAX_DEPTH:
            raise RecursionError("Hit Max Formatter Depth", self._depth)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        logging.debug("<-- (%s) Context for: %s", self._intent, self._original_key)
        self._original_key = None
        self._entered      = False
        self.sources       = []
        self.fallback      = None
        self.rec_remaining = 0
        self._intent       = None
        return

class DKeyFormatter(string.Formatter, _DKeyFormatterEntry_m):
    """
      An Expander/Formatter to extend string formatting with options useful for dkey's
      and doot specs/state.

    """

    def format(self, key:str|Key_p, /, *args, **kwargs) -> str:
        """ format keys as strings """
        match key:
            case Key_p():
                fmt = f"{key}"
            case str():
                fmt = key
            case pl.Path():
                # result = str(ftz.reduce(pl.Path.joinpath, [self.vformat(x, args, kwargs) for x in fmt.parts], pl.Path()))
                raise NotImplementedError()
            case _:
                raise TypeError("Unrecognized expansion type", fmt)

        result = self.vformat(fmt, args, kwargs)
        return result

    def get_value(self, key, args, kwargs) -> str:
        """ lowest level handling of keys being expanded """
        # This handles when the key is something like '1968'
        if isinstance(key, int) and 0 <= key <= len(args):
            return args[key]

        return kwargs.get(key, key)

    def convert_field(self, value, conversion):
        # do any conversion on the resulting object
        match conversion:
            case None:
                return value
            case "s" | "p" | "R" | "c" | "t":
                return str(value)
            case "r":
                return repr(value)
            case "a":
                return ascii(value)
            case _:
                raise ValueError("Unknown conversion specifier {0!s}".format(conversion))

    @staticmethod
    def format_field(val, spec) -> str:
        """ Take a value and a formatting spec, and apply that formatting """
        match val:
            case Key_p():
                return format(val, spec)

        wrap     = 'w' in spec
        direct   = 'd' in spec or "i" not in spec
        remaining = FMT_PATTERN.sub("", spec)

        result = str(val)
        if direct:
            result = result.removesuffix("_")
        elif not result.endswith("_"):
            result = f"{result}_"

        if wrap:
            # result = "".join(["{", result, "}"])
            result = "{%s}" % result

        return format(result, remaining)
