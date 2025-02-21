#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import builtins
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import os
import pathlib as pl
import re
import time
import types
import weakref
from sys import stderr, stdout
import warnings
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv.logging.colour_format import ColourFormatter, StripColourFormatter
from jgdv.logging.logger_spec import LoggerSpec
from jgdv.structs.chainguard import ChainGuard
from .logger import JGDVLogger

from._interface import PRINTER_NAME, SUBPRINTERS, LogLevel_e
# ##-- end 1st party imports

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
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    from ._interface import Logger

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

env          : dict       = os.environ
stream_initial_spec  : Final[LoggerSpec] = LoggerSpec.build({
    "name"           : logmod.root.name,
    "level"          : "trace",
    "target"         : "stdout",
    "format"         : "{levelname}  : INIT : {message}",
    "style"          : "{"
    })
printer_initial_spec : Final[LoggerSpec] = LoggerSpec.build({
    "name"           : PRINTER_NAME,
    "level"          : "trace",
    "target"         : "stdout",
    "format"         : "{name}({levelname}) : {message}",
    "style"          : "{",
    "propagate"      : False,
    })

##--|
class JGDVLogConfig:
    """ Utility class to setup [stdout, stderr, file] logging.
      Also creates a 'printer' logger, so instead of using `print`,
      tasks can notify the user using the printer,
      which also includes the notifications into the general log trace

      The Printer has a number of children, which can be controlled
      to customise verbosity.

      Standard _printer children:
      [ action_exec, action_group, artifact, cmd, fail, header, help, queue,
      report, skip, sleep, success, task, task_header, task_loop, task_state,
      track,
      ]

    """

    levels : ClassVar[enum.IntEnum] = LogLevel_e

    def __init__(self, subprinters=None, style=None):
        # Root Logger for everything
        self.root                 = logmod.root
        self._printer_children    = (subprinters or SUBPRINTERS)[:]
        self.stream_initial_spec  = stream_initial_spec
        self.printer_initial_spec = printer_initial_spec
        JGDVLogger.install()

        self.stream_initial_spec.apply()
        self.printer_initial_spec.apply()
        for name,lvl in self.levels.__members__.items():
            logmod.addLevelName(lvl, name)

        logging.log(self.levels.bootstrap, "Post Log Setup")

    def _setup_print_children(self, config:ChainGuard):
        logging.info("Setting up print children")
        basename            = PRINTER_NAME
        subprint_data       = config.on_fail({}).logging.subprinters()
        acceptable_names    = self._printer_children
        logging.info("Known Print Children: %s", acceptable_names)
        for data in subprint_data.items():
            match data :
                case ("default", ChainGuard()|dict() as spec_data):
                    for name in {x for x in acceptable_names if x not in subprint_data}:
                        match LoggerSpec.build(spec_data, name=name, base=basename):
                            case None:
                                print("Could not build LoggerSpec for {}".format(name))
                            case LoggerSpec() as spec:
                                spec.apply()
                case (str() as name, _) if name not in acceptable_names:
                    print("Unknown Subprinter mentioned in config: ", name)
                    pass
                case (str() as name, bool()|ChainGuard()|dict() as spec_data):
                    match LoggerSpec.build(spec_data, name=name, base=basename):
                        case None:
                            print("Could not build LoggerSpec for {}".format(name))
                        case LoggerSpec() as spec:
                            spec.apply()
                case _:
                    raise TypeError("Unknown subprinter data", data)

    def _setup_logging_extra(self, config:ChainGuard):
        """ read the doot config logging section
          setting up each entry other than stream, file, printer, and subprinters
        """
        extras = config.on_fail({}).logging.extra()
        for key,data in extras.items():
            match LoggerSpec.build(data, name=key):
                case None:
                    print("Could not build LoggerSpec for {}".format(key))
                case LoggerSpec() as spec:
                    spec.apply()

    def setup(self, config:ChainGuard):
        """ a setup that uses config values """
        if config is None:
            raise ValueError("Config data has not been configured")

        self.stream_initial_spec.clear()
        self.printer_initial_spec.clear()

        file_spec         = LoggerSpec.build(config.on_fail({}).logging.file(),    name=LoggerSpec.RootName)
        stream_spec       = LoggerSpec.build(config.on_fail({}).logging.stream(),  name=LoggerSpec.RootName)
        print_spec        = LoggerSpec.build(config.on_fail({}).logging.printer(), name=PRINTER_NAME)

        file_spec.apply()
        stream_spec.apply()
        print_spec.apply()
        self._setup_print_children(config)
        self._setup_logging_extra(config)

    def set_level(self, level:int|str):
        names = logmod.getLevelNamesMapping()
        lvl   = None
        match level:
            case int():
                lvl = level
            case str() if (lvl:=names.get(level, None)) is not None:
                pass
            case _:
                raise ValueError("Unknown level name", level)

        assert(lvl is not None)
        self.stream_initial_spec.set_level(lvl)
        self.printer_initial_spec.set_level(lvl)

    def capture_printing_to_file(self, path:str|pl.Path="print.log", *, disable_warning=False):
        """
        Setup a file handler for a separate logger,
        to keep a trace of anything printed.
        Strips colour print command codes out of any string
        printed strings are logged at DEBUG level
        """
        if not disable_warning:
            warnings.warn("Modifying builtins.print", RuntimeWarning, 2)


        oldprint = builtins.print
        file_handler = logmod.FileHandler(path, mode='w')
        file_handler.setLevel(logmod.DEBUG)
        file_handler.setFormatter(StripColourFormatter())

        print_logger = logmod.getLogger(f"{PRINTER_NAME}.intercept")
        print_logger.setLevel()
        print_logger.addHandler(file_handler)
        print_logger.propagate = False

        @ftz.wraps(oldprint)
        def intercepted(*args, **kwargs):
            """ Wraps `print` to also log to a separate file """
            oldprint(*args, **kwargs)
            if bool(args):
                print_logger.debug(args[0])

        builtins.print = intercepted

    def redirect_printing_to_logging(self, *, disable_warning=False):
        """ redirect printing into logging the logging system to handle
          logged at DEBUG level
        """
        if not disable_warning:
            # ##-- stdlib imports
            import warnings

            # ##-- end stdlib imports
            warnings.warn("Modifying builtins.print", RuntimeWarning, 2)

        # ##-- stdlib imports
        import builtins

        # ##-- end stdlib imports
        oldprint     = builtins.print
        print_logger = logmod.getLogger(f"{PRINTER_NAME}.intercept")
        print_logger.setLevel(logmod.DEBUG)

        @ftz.wraps(oldprint)
        def intercepted(*args, **kwargs):
            """ Wraps `print` to also log to a separate file """
            oldprint(*args, **kwargs)
            if bool(args):
                print_logger.debug(args[0])

        builtins.print = intercepted

    def subprinter(self, *names) -> Logger:
        """ Get a subprinter of the printer logger.
          The First name needs to be a registered subprinter.
          Additional names are unconstrained
        """
        base = self.printer_initial_spec.get()
        if not bool(names) or names == (None,):
            return base

        if names[0] not in self._printer_children:
            raise ValueError("Unknown Subprinter", names[0], self._printer_children)

        current = base
        for name in names:
            current = current.getChild(name)

        return current
