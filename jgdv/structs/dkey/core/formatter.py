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
from jgdv import Mixin
from jgdv._abstract.protocols import SpecStruct_p
from jgdv.structs.chainguard import ChainGuard
from ._getter import ChainGetter as CG  # noqa: N817
from .meta import DKey
from .parser import RawKey

from .._interface import Key_p, MAX_DEPTH, MAX_KEY_EXPANSIONS, FMT_PATTERN, DEFAULT_COUNT, PAUSE_COUNT

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


class _DKeyFormatterEntry_m:  # noqa: N801
    """ Mixin to make DKeyFormatter a singleton with static access

      and makes the formatter a context manager, to hold the current data sources
      """
    _instance     : ClassVar[Self]      = None

    sources       : list                = []  # noqa: RUF012
    fallback      : Any                 = None

    rec_remaining : int                 = MAX_KEY_EXPANSIONS

    _entered      : bool                = False
    _original_key : str|Key_p           = None

    @classmethod
    def Parse(cls, key:Key_p|pl.Path) -> tuple(bool, list[RawKey]):  # noqa: N802
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
                    result = [RawKey(prefix=x[0],
                                     key=x[1] or "",
                                     format=x[2] or "",
                                     conv=x[3] or "")
                              for x in cls._instance.parse(key)]
                    non_key_text = any(bool(x.prefix) for x in result)
                    return non_key_text, result
                case _:
                    msg = "Unknown type found"
                    raise TypeError(msg, key)
        except ValueError:
            return True, []

    @classmethod
    def expand(cls, key:Key_p, *, sources=None, max=None, **kwargs) -> Maybe[Any]:  # noqa: A002
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
            msg = "Fallback values for redirection should be part of key construction"
            raise ValueError(msg, key)
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
            msg = "Hit Max Formatter Depth"
            raise RecursionError(msg, self._depth)
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


class _DKeyFormatter_Expansion_m:  # noqa: N801
    """
    A Mixin for  DKeyFormatter, to expand keys without recursion
    """

    def _expand(self, key:Key_p, *, fallback=None, count=DEFAULT_COUNT) -> Maybe[Any]:
        """
          Expand the key, returning fallback if it fails,
          counting each loop as `count` attempts

        """
        if not isinstance(key, Key_p):
            msg = "Key needs to be a jgdv.protocols.Key_p"
            raise TypeError(msg)
        current : DKey = key
        last    : set[str] = set()

        while 0 < self.rec_remaining and str(current) not in last:
            logging.debug("--- Loop (%s:%s) [%s] : %s", self._depth, MAX_KEY_EXPANSIONS - self.rec_remaining, key, repr(current))
            self.rec_remaining -= count
            last.add(str(current))
            match current:
                case sh.Command():
                    break
                case Key_p() if current._mark is DKey.Mark.NULL:
                     continue
                case Key_p() if current.multi:
                    current = self._multi_expand(current)
                case Key_p():
                    redirected = self._try_redirection(current)[0]
                    current    = self._single_expand(redirected) or current
                case _:
                    break

        match current:
            case None:
                current = fallback or key._fallback
            case x if str(x) == str(key):
                current = fallback or key._fallback
            case _:
                pass

        if current is not None:
            logging.debug("Running Expansion Hook: (%s) -> (%s)", key, current)
            exp_val = key._expansion_type(current)
            key.cent_check_expansion(exp_val)
            current = key._expansion_hook(exp_val)

        logging.debug("Expanded (%s) -> (%s)", key, current)
        return current

    def _multi_expand(self, key:Key_p) -> str:
        """
        expand a multi key,
        by formatting the anon key version using a sequence of expanded subkeys,
        this allows for duplicate keys to be used differenly in a single multikey
        """
        logging.debug("multi(%s)", key)
        logging.debug("----> %s", key.keys())
        expanded_keys   = [ str(self._expand(x, fallback=f"{x:w}", count=PAUSE_COUNT)) for x in key.keys() ]
        expanded        = self.format(key._anon, *expanded_keys)
        logging.debug("<---- %s", key.keys())
        return DKey(expanded)

    def _try_redirection(self, key:Key_p) -> list[Key_p]:
        """ Try to redirect a key if necessary,
          if theres no redirection, return the key as a direct key
          """
        key_str = f"{key:i}"
        match CG.get(key_str, *self.sources, *[x for x in key.extra_sources() if x not in self.sources]):
            case list() as ks:
                logging.debug("(%s -> %s -> %s)", key, key_str, ks)
                return [DKey(x, implicit=True) for x in ks]
            case Key_p() as k:
                logging.debug("(%s -> %s -> %s)", key, key_str, k)
                return [k]
            case str() as k:
                logging.debug("(%s -> %s -> %s)", key, key_str, k)
                return [DKey(k, implicit=True)]
            case None if key._mark is DKey.Mark.INDIRECT and isinstance(key._fallback, str|DKey):
                logging.debug("%s -> %s -> %s (fallback)", key, key_str, key._fallback)
                return [DKey(key._fallback, implicit=True)]
            case None:
                logging.debug("(%s -> %s -> Ø)", key, key_str)
                return [key]
            case _:
                msg = "Reached an unknown response path for redirection"
                raise TypeError(msg, key)

    def _single_expand(self, key:Key_p, fallback=None) -> Maybe[Any]:
        """
          Expand a single key up to {rec_remaining} times
        """
        assert(isinstance(key, Key_p))
        logging.debug("solo(%s)", key)
        match CG.get(key, *self.sources, *[x for x in key.extra_sources() if x not in self.sources], fallback=fallback):
            case None:
                return None
            case Key_p() as x:
                return x
            case x if self.rec_remaining == 0:
                return x
            case str() as x if key._mark is DKey.Mark.PATH:
                return DKey(x, mark=DKey.Mark.PATH)
            case str() as x if x == key:
                # Got the key back, wrap it and don't expand it any more
                return "{%s}" % x  # noqa: UP031
            case str() | pl.Path() as x:
                return DKey(x)
            case x:
                return x

##--|
@Mixin(_DKeyFormatter_Expansion_m, _DKeyFormatterEntry_m)
class DKeyFormatter(string.Formatter):
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
                raise NotImplementedError()
            case _:
                msg = "Unrecognized expansion type"
                raise TypeError(msg, fmt)

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
                msg = f"Unknown conversion specifier {conversion!s}"
                raise ValueError(msg)

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
            result = "{%s}" % result  # noqa: UP031

        return format(result, remaining)
