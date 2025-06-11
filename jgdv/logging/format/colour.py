#!/usr/bin/env python3
"""
see `Alexandra Zaharia <https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging/>`_

"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging
import logging as logmod
import pathlib as pl
import re
import warnings
from collections import defaultdict
from string import Formatter
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import _string
import sty
from sty import bg, ef, fg, rs

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Mixin, Proto

# ##-- end 1st party imports

from . import _interface as API # noqa: N812
from .stack_m import StackFormatter_m

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe, Rx
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from logging import LogRecord

    type StyleChar = Literal["%", "{", "$"]
##--|

# isort: on
# ##-- end types

COLOUR_RESET       : str    = rs.all
##--|


@Mixin(StackFormatter_m)
class ColourFormatter(logging.Formatter):
    """
    Stream Formatter for logging, enables use of colour sent to console

    Guarded Formatter for adding colour.
    Uses the sty module.
    If sty is missing, behaves as the default formatter class

    # Do *not* use for on filehandler
    Usage reminder:
    # Create stdout handler for logging to the console (logs all five levels)
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(ColourFormatter(fmt))
    logger.addHandler(stdout_handler)
    """

    _default_fmt      : str        = '{asctime} | {levelname:9} | {message}'
    _default_date_fmt : str        =  "%H:%M:%S"
    _default_style    : StyleChar  = '{'
    colours           : dict[int|str, str]

    def __init__(self, *, fmt:Maybe[str]=None, style:Maybe[StyleChar]=None) -> None:
        """
        Create the ColourFormatter with a given *Brace* style log format
        """
        super().__init__(fmt or self._default_fmt,
                         datefmt=self._default_date_fmt,
                         style=style or self._default_style)
        self.colours = defaultdict(lambda: rs.all)
        self.apply_colour_mapping(API.default_colour_mapping)
        self.apply_colour_mapping(API.default_log_colours)

    def format(self, record:LogRecord) -> str:
        if hasattr(record, "colour"):
            log_colour = self.colours[record.colour]
        else:
            log_colour = self.colours[record.levelno]

        return log_colour + super().format(record) + COLOUR_RESET

    def apply_colour_mapping(self, mapping:dict) -> None:
        """ applies a mapping of colours by treating each value as a pair of attrs of sty

        eg: {logging.DEBUG: ("fg", "blue"), logging.INFO: ("bg", "red")}
        """
        for x,(a,b) in mapping.items():
            accessor = getattr(sty, a)
            val      = getattr(accessor, b)
            self.colours[x] = val


@Mixin(StackFormatter_m)
class StripColourFormatter(logging.Formatter):
    """
    Force Colour Command codes to be stripped out of a string.
    Useful for when you redirect printed strings with colour
    to a file
    """

    _default_fmt      : str           = "{asctime} | {levelname:9} | {shortname:25} | {message}"
    _default_date_fmt : str           = "%Y-%m-%d %H:%M:%S"
    _default_style    : StyleChar     = '{'
    _colour_strip_re  : Rx            = re.compile(r'\x1b\[([\d;]+)m?')

    def __init__(self, *, fmt:Maybe[str]=None, style:Maybe[StyleChar]=None) -> None:
        """
        Create the StripColourFormatter with a given *Brace* style log format
        """
        super().__init__(fmt or self._default_fmt,
                         datefmt=style or self._default_date_fmt,
                         style=self._default_style)

    def format(self, record:LogRecord) -> str:
        result    = super().format(record)
        no_colour = self._colour_strip_re.sub("", result)
        return no_colour
