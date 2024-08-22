#!/usr/bin/env python3
"""
printing areas:

[header]
[setup]
[cmd entry]
[help]
[plan]
[task loop] - start

[[Task Header]]:
- [Action Group Running]
-- [actions]
-- [State]
- [Task Queuing]
- [Skips,Failure]
- [Artifacts]
[task loop] -exit

[report]

[shutdown]

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

from jgdv.logging.log_colour import (JGDVColourFormatter,
                                     JGDVColourStripFormatter)
from tomlguard import TomlGuard
from jgdv.logging.logger_spec import LoggerSpec

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

env : dict = os.environ
subprinters : Final[list[str]]= [
    "action_exec", "action_group", "artifact", "cmd", "fail", "header", "help", "queue",
    "report", "skip", "sleep", "success", "task", "task_header", "task_loop", "task_state",
    "track",
    ]

stream_initial_spec  : Final[LoggerSpec] = LoggerSpec.build({
    "name"           : logmod.root.name,
    "level"          : "WARNING",
    "target"         : "stdout",
    "format"         : "{levelname}  : INIT : {message}",
    })
printer_initial_spec : Final[LoggerSpec] = LoggerSpec.build({
    "name"           : printer,
    "level"          : "WARNING",
    "target"         : "stdout",
    "format"         : "{message}",
    "propagate"      : False,
    })


def subprinter(name:None|str=None) -> logmod.Logger:
    """ Utility method to get a subprinter from the constant defined types
    if no subprinter name is specified, return the printer itself
    """
    if not name:
        return printer
    if name not in subprinters:
        raise ValueError("Unknown Subprinter", name)
    return printer_initial_spec.get().getChild(name)

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

    def __init__(self, printer:str="_printer"):
        # Root Logger for everything
        self.root                = logmod.root
        self._printer_children   = subprinters[:]

        self.stream_initial_spec = LoggerSpec.build({
            "name": logmod.root.name,
            "level" : "WARNING",
            "target": "stdout",
            "format" : "{levelname}  : INIT : {message}",
            })
        # EXCEPT this, which replaces 'print(x)' when print is redirected
        self.printer_initial_spec = LoggerSpec.build({
            "name": printer,
            "level": "WARNING",
            "target": "stdout",
            "format": "{message}",
            "propagate": False,
            })

        self.stream_initial_spec.apply()
        self.printer_initial_spec.apply()
        logging.debug("Post Log Setup")

    def setup(self, config:TomlGuard):
        """ a setup that uses config values """
        if config is None:
            raise ValueError("Config data has not been configured")

        self.stream_initial_spec.clear()
        self.printer_initial_spec.clear()

        file_spec         = LoggerSpec.build(config.on_fail({}).logging.file(), name=LoggerSpec.RootName)
        stream_spec       = LoggerSpec.build(config.on_fail({}).logging.stream(), name=LoggerSpec.RootName)
        print_spec        = LoggerSpec.build(config.on_fail({}).logging.printer(), name="_printer")

        file_spec.apply()
        stream_spec.apply()
        print_spec.apply()
        self._setup_print_children(config)
        self._setup_logging_extra(config)

    def set_level(self, level):
        self.stream_initial_spec.set_level(level)
        self.printer_initial_spec.set_level(level)


    def capture_printing_to_file(path:str|pl.Path="print.log", *, disable_warning=False):
        """
        Setup a file handler for a separate logger,
        to keep a trace of anything printed.
        Strips colour print command codes out of any string
        printed strings are logged at DEBUG level
        """
        if not disable_warning:
            import warnings
            warnings.warn("Modifying builtins.print", RuntimeWarning)

        import builtins
        oldprint = builtins.print
        file_handler = logmod.FileHandler(path, mode='w')
        file_handler.setLevel(logmod.DEBUG)
        file_handler.setFormatter(ColourStripPrintCapture())

        print_logger = logmod.getLogger('print.intercept')
        print_logger.setLevel(logmod.NOTSET)
        print_logger.addHandler(file_handler)
        print_logger.propagate = False

        @wraps(oldprint)
        def intercepted(*args, **kwargs):
            """ Wraps `print` to also log to a separate file """
            oldprint(*args, **kwargs)
            if bool(args):
                print_logger.debug(args[0])

        builtins.print = intercepted

    def redirect_printing_to_logging(*, disable_warning=False):
        """ redirect printing into logging the logging system to handle
          logged at DEBUG level
        """
        if not disable_warning:
            import warnings
            warnings.warn("Modifying builtins.print", RuntimeWarning)

        import builtins
        oldprint     = builtins.print
        print_logger = logmod.getLogger('print.intercept')
        print_logger.setLevel(logmod.DEBUG)

        @wraps(oldprint)
        def intercepted(*args, **kwargs):
            """ Wraps `print` to also log to a separate file """
            oldprint(*args, **kwargs)
            if bool(args):
                print_logger.debug(args[0])

        builtins.print = intercepted

    def _setup_print_children(self):
        basename            = doot.constants.printer.PRINTER_NAME
        subprint_data       = doot.config.on_fail({}).logging.subprinters()
        acceptable_names    = doot.constants.printer.PRINTER_CHILDREN
        for data in subprint_data.items():
            match data :
                case ("default", TomlGuard()|dict() as spec_data):
                    for name in {x for x in acceptable_names if x not in subprint_data}:
                        match LoggerSpec.build(spec_data, name=name, base=basename):
                            case None:
                                print("Could not build LoggerSpec for {}".format(name))
                            case LoggerSpec() as spec:
                                spec.apply()
                case (str() as name, _) if name not in subprint_data:
                    print("Unknown Subprinter mentioned in config: ", name)
                    pass
                case (str(), False|None):
                    # disable the subprinter
                    LoggerSpec.build({"disabled":True}, name=name, base=basename).apply()
                case (str() as name, TomlGuard()|dict() as spec_data):
                    match LoggerSpec.build(spec_data, name=name, base=basename):
                case None:
                    print("Could not build LoggerSpec for {}".format(name))
                case LoggerSpec() as spec:
                    spec.apply()


    def _setup_logging_extra(self):
        """ read the doot config logging section
          setting up each entry other than stream, file, printer, and subprinters
        """
        extras = config.on_fail({}).logging.extra()
        for key,data in extras.items():
            match LoggerSpec.build(data, name=key):
                case None:
                    print("Could not build LoggerSpec for {}".format(name))
                case LoggerSpec() as spec:
                    spec.apply()
