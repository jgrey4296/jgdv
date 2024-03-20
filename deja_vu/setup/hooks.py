#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import os
import sys
import atexit
import faulthandler
import signal

env : dict = os.environ

def exception_hook(exc_type, exc_value, tb):
    """ A Basic exception handler example
      from https://python.plainenglish.io/creating-beautiful-tracebacks-with-pythons-exception-hooks-c8a79e13558d
    """
    print('Traceback:')
    filename = tb.tb_frame.f_code.co_filename
    name = tb.tb_frame.f_code.co_name
    line_no = tb.tb_lineno
    print(f"File {filename} line {line_no}, in {name}")

    # Exception type and value
    print(f"{exc_type.__name__}, Message: {exc_value}")

def exception_hook_loop(exc_type, exc_value, tb):
    ""
    local_vars = tb.tb_frame.f_locals
    tb = tb.tb_next
    print(f"Local variables in top frame: {local_vars}")

class DejaVuHookConfig:

    def __init__(self):
        self._disabled = "PRE_COMMIT" in env
        self._exit_hook       = None
        self._exception_hook  = None
        self._breakpoint_hook = None
        self._display_hook    = None
        self._unraisable_hook = None

    def setup(self):
        pass

    def set_fault(self):
        faulthandler.enable(file=sys.stderr, all_threads=True)

    def set_exit(self):
        if not self._exit_hook:
            return

        @atexit.register(self._exit_hook)

    def set_exception(self):
        if not self._exception_hook:
            return
        sys.excepthook = self._exception_hook

    def set_breakpoint(self):
        if not self._breakpoint_hook:
            return
        sys.breakpointhook = self._breakpointhook

    def set_display(self):
        if not self._display_hook:
            reutrn
        sys.displayhook = self._display_hook

    def set_unraisable(self):
        if not self._unraisable_hook:
            return

        self.unraisablehook = self._unraisable_hook


    def set_signal(self, sig=signal.SIGINT):
        printer.debug("Installing Task Loop handler for: %s", signal.strsignal(sig))
        # Install handler for Interrupt signal
        signal.signal(sig, SignalHandler.handle)

    def unset_signal(self, sig=signal.SIGINT):
        printer.debug("Uninstalling Task Loop handler for: %s", signal.strsignal(sig))
        signal.signal(sig, signal.SIG_DFL)

    def __enter__(self):
        if not self._disabled:
            self.set_signal()
        return

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self._disabled:
            self.unset_signal()
        # return False to reraise errors
        return
