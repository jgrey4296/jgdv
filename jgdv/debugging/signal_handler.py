#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
# import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import os
import pathlib as pl
import re
import signal
import time
import types
import weakref

# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

##-- logging
logging    = logmod.getLogger(__name__)
##-- end logging

env : dict = os.environ

class SignalHandler:
    """ Install a breakpoint to run on (by default) SIGINT

    disables itself if PRE_COMMIT is in the environment.
    Can act as a context manager
    """

    def __init__(self):
        self._disabled = "PRE_COMMIT" in env

    @staticmethod
    def handle(signum, frame):
        breakpoint()
        pass

    @staticmethod
    def install(sig=signal.SIGINT):
        logging.debug("Installing Task Loop handler for: %s", signal.strsignal(sig))
        # Install handler for Interrupt signal
        signal.signal(sig, SignalHandler.handle)

    @staticmethod
    def uninstall(sig=signal.SIGINT):
        logging.debug("Uninstalling Task Loop handler for: %s", signal.strsignal(sig))
        signal.signal(sig, signal.SIG_DFL)

    def __enter__(self):
        if not self._disabled:
            SignalHandler.install()
        return

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self._disabled:
            SignalHandler.uninstall()
        # return False to reraise errors
        return
