#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import builtins
import datetime
import functools as ftz
import itertools as itz
import logging as logmod
import os
import re
import time
import types
import warnings
import weakref
from sys import stderr, stdout
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Mixin, Proto
from jgdv.structs.chainguard import ChainGuard
from jgdv.structs.metalord.singleton import MLSingleton

# ##-- end 1st party imports

from . import _interface as API# noqa: N812
from .format import StripColourFormatter
from .logger import JGDVLogger
from .logger_spec import LoggerSpec

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, overload

if TYPE_CHECKING:
    import pathlib as pl
    import enum
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

env                  : dict              = os.environ # type: ignore
printer_initial_spec : Final[LoggerSpec] = LoggerSpec.build(API.default_printer)
initial_spec         : Final[LoggerSpec] = LoggerSpec.build(API.default_stdout)

##--|

class PrintCapture_m:
    """ Mixin for redirecting builtins.print to a file  """
    original_print : Maybe[Callable]

    def capture_printing_to_file(self, path:str|pl.Path=API.default_print_file, *, disable_warning:bool=False) -> None:
        """ Modifies builtins.print to also print to a file

        Setup a file handler for a separate logger,
        to keep a trace of anything printed.
        Strips colour print command codes out of any string
        printed strings are logged at DEBUG level
        """
        match getattr(self, "original_print", None):
            case None:
                self.original_print = builtins.print
            case _:
                return

        if not disable_warning:
            warnings.warn("Modifying builtins.print", RuntimeWarning, 2)

        file_handler = logmod.FileHandler(path, mode='w')
        file_handler.setLevel(logmod.DEBUG)
        file_handler.setFormatter(StripColourFormatter())

        print_logger = logmod.getLogger(f"{API.PRINTER_NAME}.intercept")
        print_logger.setLevel(logmod.DEBUG)
        print_logger.addHandler(file_handler)
        print_logger.propagate = False

        @ftz.wraps(self.original_print)
        def intercepted(*args, **kwargs) -> None:
            """ Wraps `print` to also log to a separate file """
            self.original_print(*args, **kwargs)
            if bool(args):
                print_logger.debug(args[0])

        builtins.print = intercepted

    def remove_print_capture(self) -> None:
        """ removes a previously advised builtins.print """
        match getattr(self, "original_print", None):
            case None:
                return
            case x:
                builtins.print = x
                self.original_print = None

##--|

@Mixin(PrintCapture_m)
class JGDVLogConfig(metaclass=MLSingleton):
    """ Utility class to setup [stdout, stderr, file] logging.

      Also creates a 'printer' logger, so instead of using `print`,
      tasks can notify the user using the printer,
      which also includes the notifications into the general log trace

      The Printer has a number of children, which can be controlled
      to customise verbosity.

      Standard _printer children::
        action_exec, action_group, artifact, cmd, fail, header, help, queue,
        report, skip, sleep, success, task, task_header, task_loop, task_state,
        track


    """

    levels                : ClassVar[enum.IntEnum] = API.LogLevel_e
    logger_cls            : ClassVar[type[Logger]] = JGDVLogger

    root                  : Logger
    _printer_children     : list
    _initial_spec         : LoggerSpec
    _printer_initial_spec : LoggerSpec
    _registry             : list[LoggerSpec]
    is_setup              : bool

    def __init__(self, *, subprinters:Maybe[list[str]]=None, style:Maybe[str]=None) -> None:
        # Root Logger for everything
        self.root                                  = logmod.root
        self._printer_children                     = (subprinters or API.SUBPRINTERS)[:]
        self._initial_spec                         = initial_spec
        self._printer_initial_spec                 = printer_initial_spec
        self._registry                             = []
        self.is_setup                              = False

        self._install_logger_override()
        self._register_new_names()

        self.activate_spec(self._initial_spec)
        self.activate_spec(self._printer_initial_spec)

        logging.log(self.levels.bootstrap, "Post Log Setup") # type: ignore

    def __repr__(self) -> str:

        return f"<{self.__class__.__name__}({len(self._registry)}) : >"

    def _report(self) -> None:
        printer = self.subprinter()
        for x in self._registry:
            printer.user("%s : %s", x.fullname, x.level)


    def _install_logger_override(self) -> None:
        if self.logger_cls is None:
            return

        self.logger_cls.install()
        if not issubclass(logmod.getLoggerClass(), self.logger_cls):
            msg = "Logger Class Installation Failed"
            raise TypeError(msg, self.logger_cls)

    def _register_new_names(self) -> None:
        for name,lvl in self.levels.__members__.items(): # type: ignore
            logmod.addLevelName(lvl, name)

    def _setup_print_children(self, config:ChainGuard) -> None:
        logging.info("Setting up print children")
        basename            = API.PRINTER_NAME
        subprint_data       = config.on_fail({}).logging.subprinters()
        acceptable_names    = self._printer_children
        logging.info("Known Print Children: %s", acceptable_names)
        for data in subprint_data.items():
            match data :
                case ("default", ChainGuard()|dict() as spec_data):
                    for name in {x for x in acceptable_names if x not in subprint_data}:
                        match LoggerSpec.build(spec_data, name=name, base=basename):
                            case None:
                                logging.warning(f"Could not build LoggerSpec for {name}")
                            case LoggerSpec() as spec:
                                self.activate_spec(spec)
                case (str() as name, _) if name not in acceptable_names:
                    logging.warning("Unknown Subprinter mentioned in config: %s", name)
                    pass
                case (str() as name, bool()|ChainGuard()|dict() as spec_data):
                    match LoggerSpec.build(spec_data, name=name, base=basename):
                        case None:
                            logging.warning(f"Could not build LoggerSpec for {name}")
                        case LoggerSpec() as spec:
                            self.activate_spec(spec)
                case _:
                    msg = "Unknown Subprinter Data"
                    raise TypeError(msg, data)

    def _setup_logging_extra(self, config:ChainGuard) -> None:
        """ read the doot config logging section
          setting up each entry other than stream, file, printer, and subprinters
        """
        extras = config.on_fail({}).logging.extra()
        for key,data in extras.items():
            match LoggerSpec.build(data, name=key):
                case None:
                    logging.warning(f"Could not build LoggerSpec for {key}")
                case LoggerSpec() as spec:
                    self.activate_spec(spec)

    def activate_spec(self, spec:LoggerSpec, *, override:bool=False) -> None:
        """ Add a spec to the registry and activate it """
        target   = spec
        fullname = spec.fullname
        logging.info("Activating Logging Spec: %s", fullname)
        self._registry.append(spec)
        target.apply()

    def setup(self, config:ChainGuard, *, force:bool=False) -> None:
        """ a setup that uses config values """
        if self.is_setup and not force:
            warnings.warn("Logging Is Already Set Up", stacklevel=2)

        if config is None:
            msg = "Config data has not been configured"
            raise ValueError(msg)

        self._initial_spec.clear()
        self._printer_initial_spec.clear()

        root_spec = LoggerSpec.build([config.on_fail({}).logging.file(),
                                      config.on_fail({}).logging.stream(),
                                      ],
                                     name=LoggerSpec.RootName)
        print_spec        = LoggerSpec.build(config.on_fail({}).logging.printer(),
                                             name=API.PRINTER_NAME)

        self.activate_spec(root_spec, override=True)
        self.activate_spec(print_spec, override=True)
        self._setup_print_children(config)
        self._setup_logging_extra(config)

        self.is_setup = True

    def set_level(self, level:int|str) -> None:
        """ Set the active logging level """
        names = logmod.getLevelNamesMapping()
        lvl   = None
        match level:
            case int():
                lvl = level
            case str() if (lvl:=names.get(level, None)) is not None:
                pass
            case _:
                msg = "Unknown Level Name"
                raise ValueError(msg, level)

        assert(lvl is not None)
        self._initial_spec.set_level(lvl)
        self._printer_initial_spec.set_level(lvl)

    def subprinter(self, *names, prefix:Maybe[str]=None) -> Logger:
        """ Get a subprinter of the printer logger.
          The First name needs to be a registered subprinter.
          Additional names are unconstrained
        """
        base = self._printer_initial_spec.get()
        if not bool(names) or names == (None,):
            return base

        if names[0] not in self._printer_children:
            msg = "Unknown Subprinter"
            raise ValueError(msg, names[0], self._printer_children)

        current = base
        for name in names:
            current = current.getChild(name)
        else:
            if prefix:
                current.set_prefixes(prefix)
            return current
