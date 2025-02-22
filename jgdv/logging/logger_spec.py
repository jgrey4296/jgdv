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
import logging.handlers as l_handlers
import os
import pathlib as pl
import re
import time
import types
import weakref
from sys import stderr, stdout
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Proto, Mixin
from jgdv._abstract.protocols import Buildable_p, ProtocolModelMeta
from .colour_format import ColourFormatter, StripColourFormatter
from jgdv.structs.chainguard import ChainGuard
from .filter import BlacklistFilter, WhitelistFilter
from ._interface import LogLevel_e, MAX_FILES, TARGETS

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError
if TYPE_CHECKING:
    from jgdv import Maybe, RxStr
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    from ._interface import Handler, Logger, Formatter
##--|
from jgdv import Maybe
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

env           : dict             = os.environ
IS_PRE_COMMIT : Final[bool]      = "PRE_COMMIT" in env

class HandlerBuilder_m:
    """
    Loggerspec Mixin for building handlers
    """

    def _build_streamhandler(self) -> Handler:
        return logmod.StreamHandler(stdout)

    def _build_errorhandler(self) -> Handler:
        return logmod.StreamHandler(stderr)

    def _build_filehandler(self, path:pl.Path) -> Handler:
        return logmod.FileHandler(path, mode='w')

    def _build_rotatinghandler(self, path:pl.Path) -> Handler:
        handler = l_handlers.RotatingFileHandler(path, backupCount=MAX_FILES)
        handler.doRollover()
        return handler

    def _build_formatter(self, handler) -> Formatter:
        match self.colour:
            case _ if IS_PRE_COMMIT:
                # Always strip colour when in pre-commit
                formatter = StripColourFormatter(fmt=self.format, style=self.style)
            case _ if isinstance(handler, logmod.FileHandler|l_handlers.RotatingFileHandler):
                # Always strip colour when logging to a file
                formatter = StripColourFormatter(fmt=self.format, style=self.style)
            case False:
                formatter = StripColourFormatter(fmt=self.format, style=self.style)
            case str() | True:
                formatter = ColourFormatter(fmt=self.format, style=self.style)

        return formatter

    def _build_filters(self) -> list[Callable]:
        filters = []
        if bool(self.allow):
            filters.append(WhitelistFilter(self.allow))
        if bool(self.filter):
            filters.append(BlacklistFilter(self.filter))

        return filters

    def _discriminate_handler(self, target:Maybe[str|pl.Path]) -> tuple[Maybe[Handler], Maybe[Formatter]]:
        handler, formatter = None, None

        match target:
            case "pass" | None:
                return None, None
            case "file":
                log_file_path      = self.logfile()
                handler            = self._build_filehandler(log_file_path)
            case "rotate":
                log_file_path      = self.logfile()
                handler            = self._build_rotatinghandler(log_file_path)
            case "stdout":
                handler   = self._build_streamhandler()
            case "stderr":
                handler = self._build_errorhandler()
            case _:
                raise ValueError("Unknown logger spec target", target)

        formatter = self._build_formatter(handler)

        assert(handler   is not None)
        assert(formatter is not None)
        return handler, formatter

##--|

@Proto(Buildable_p)
class LoggerSpec(HandlerBuilder_m, BaseModel, metaclass=ProtocolModelMeta):
    """
      A Spec for toml defined logging control.
      Allows user to name a logger, set its level, format,
      filters, colour, and what (cli arg) verbosity it activates on,
      and what file it logs to.

      When 'apply' is called, it gets the logger,
      and sets any relevant settings on it.
    """

    name                       : str
    disabled                   : bool                        = False
    base                       : Maybe[str]                  = None
    level                      : str|int                     = logmod._nameToLevel.get("WARNING", 0)
    format                     : str                         = "{levelname:<8} : {message}"
    filter                     : list[str]                   = []
    allow                      : list[str]                   = []
    colour                     : bool|str                    = False
    verbosity                  : int                         = 0
    target                     : Maybe[str|list[str|pl.Path]]= None # stdout | stderr | file
    filename_fmt               : Maybe[str]                  = "%Y-%m-%d::%H:%M.log"
    propagate                  : Maybe[bool]                 = False
    clear_handlers             : bool                        = False
    style                      : str                         = "{"
    nested                     : list[LoggerSpec]            = []
    prefix                     : Maybe[str]                  = None

    RootName                   : ClassVar[str]               = "root"
    levels                     : ClassVar[enum.IntEnum]      = LogLevel_e

    @staticmethod
    def build(data:bool|list|dict, **kwargs) -> LoggerSpec:
        """
          Build a single spec, or multiple logger specs targeting the same logger
        """
        match data:
            case False:
                return LoggerSpec(disabled=True, **kwargs)
            case True:
                return LoggerSpec(**kwargs)
            case list():
                nested = []
                for x in data:
                    nested.append(LoggerSpec.build(x, **kwargs))
                return LoggerSpec(nested=nested, **kwargs)
            case ChainGuard():
                as_dict = data._table().copy()
                as_dict.update(kwargs)
                return LoggerSpec.model_validate(as_dict)
            case dict():
                as_dict = data.copy()
                as_dict.update(kwargs)
                return LoggerSpec.model_validate(as_dict)
            case _:
                raise TypeError("Unknown data for logger spec", data)

    @field_validator("level")
    def _validate_level(cls, val):
        match val:
            case str() if (lvl:=logmod.getLevelNamesMapping().get(val, None)) is not None:
                return lvl
            case str() if val in LoggerSpec.levels.__members__:
                return LoggerSpec.levels[val]
            case int():
                return val
            case _:
                breakpoint()
                pass
                raise ValueError(val)

    @field_validator("format")
    def _validate_format(cls, val):
        return val

    @field_validator("target")
    def _validate_target(cls, val):
        match val:
            case [*xs] if all(x in TARGETS for x in xs):
                return val
            case str() if val in TARGETS:
                return val
            case pl.Path():
                return val
            case None:
                return "stdout"
            case _:
                raise ValueError("Unknown target value for LoggerSpec", val)

    @field_validator("style")
    def _validate_style(cls, val):
        match val:
            case "%" | "{" | "$":
                return val
            case _:
                raise ValueError("Logger Style Needs to be in [{,%,$]", val)

    @ftz.cached_property
    def fullname(self) -> str:
        if self.base is None:
            return self.name
        return "{}.{}".format(self.base, self.name)

    def apply(self, *, onto:Maybe[Logger]=None) -> Logger:
        """ Apply this spec (and nested specs) to the relevant logger """
        handler_pairs : list[tuple[logmod.Handler, logmod.Formatter]] = []
        logger           = self.get()
        logger.propagate = self.propagate
        logger.setLevel(logmod._nameToLevel.get("NOTSET", 0))
        if self.disabled:
            logger.disabled = True
            return logger

        match self.prefix:
            case None:
                pass
            case str() if hasattr(logger, "set_prefixes"):
                logger.set_prefixes(self.prefix)

        match self.colour:
            case str():
                logger.set_colour(self.colour)
            case _:
                pass

        match self.target:
            case _ if bool(self.nested):
                for subspec in self.nested:
                    subspec.apply()
                return logger
            case None | []:
                handler_pairs.append(self._discriminate_handler(None))
            case [*xs]:
                handler_pairs += [self._discriminate_handler(x) for x in xs]
            case str() | pl.Path():
                handler_pairs.append(self._discriminate_handler(self.target))
            case _:
                raise ValueError("Unknown target value for LoggerSpec", self.target)

        log_filters = self._build_filters()
        for pair in handler_pairs:
            match pair:
                case None, _:
                    pass
                case hand, None:
                    hand.setLevel(self.level)
                    for fltr in log_filters:
                        hand.addFilter(fltr)
                    logger.addHandler(hand)
                case hand, fmt:
                    hand.setLevel(self.level)
                    hand.setFormatter(fmt)
                    for fltr in log_filters:
                        hand.addFilter(fltr)
                    logger.addHandler(hand)
                case _:
                    pass
        else:
            if not bool(logger.handlers):
                logger.setLevel(self.level)
                logger.propagate = True
            return logger

    def get(self) -> Logger:
        logger = logmod.getLogger(self.fullname)
        return logger

    def clear(self):
        """ Clear the handlers for the logger referenced """
        logger = self.get()
        handlers = logger.handlers[:]
        for h in handlers:
            logger.removeHandler(h)

    def logfile(self) -> pl.Path:
        log_dir  = pl.Path(".temp/logs")
        if not log_dir.exists():
            log_dir = pl.Path()

        filename = datetime.datetime.now().strftime(self.filename_fmt)
        return log_dir / filename

    def set_level(self, level:int|str):
        match level:
            case str():
                level = logmod._nameToLevel.get(level, 0)
            case int():
                pass
        logger = self.get()
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
