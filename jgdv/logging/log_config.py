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
        self.root    = logmod.root
        self._printer_children = [
            "action_exec", "action_group", "artifact", "cmd", "fail", "header", "help", "queue",
            "report", "skip", "sleep", "success", "task", "task_header", "task_loop", "task_state",
            "track",
            ]
        self.stream_initial_spec = LoggerSpec.build({"name": logmod.root.name,
                                                     "level" : "WARNING",
                                                     "target": "stdout",
                                                     "format" : "{levelname}  : INIT : {message}",
                                                    })
        # EXCEPT this, which replaces 'print(x)'
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
        assert(config is not None)
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

    def _setup_print_children(self, config):
        basename      = "_printer"
        subprint_data = config.on_fail({}).logging.subprinters()
        for name in self._printer_children:
            if name not in subprint_data:
                continue
            fullname = "{}.{}".format(basename, name)
            match LoggerSpec.build(subprint_data[name], name=fullname):
                case None:
                    print("Could not build LoggerSpec for {}".format(name))
                case LoggerSpec() as spec:
                    spec.apply()

    def _setup_logging_extra(self, config):
        """ read the config logging section
          setting up each entry other than stream, file, and printer
        """
        extras = config.on_fail({}).logging.extra()
        for key,data in extras.items():
            match LoggerSpec.build(data, name=key):
                case None:
                    print("Could not build LoggerSpec for {}".format(name))
                case LoggerSpec() as spec:
                    spec.apply()
