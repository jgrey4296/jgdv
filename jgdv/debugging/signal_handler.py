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
import pdb
import re
import signal
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging    = logmod.getLogger(__name__)
##-- end logging

env        : dict        = os.environ
PRE_COMMIT : Final[bool] = "PRE_COMMIT" in env
BREAK_HEADER : Final[str] = "\n---- Task Interrupted ---- "

##--| Body:

class SignalHandler:
    """ Install a breakpoint to run on (by default) SIGINT

    disables itself if PRE_COMMIT is in the environment.
    Can act as a context manager

    """

    def __init__(self):
        self._disabled = PRE_COMMIT

    @staticmethod
    def handle(signum, frame):
        breakpoint(header=BREAK_HEADER)
        SignalHandler.install()

    @staticmethod
    def install(sig=signal.SIGINT):
        logging.debug("Installing Basic Interrupt Handler for: %s", signal.strsignal(sig))
        signal.signal(sig, SignalHandler.handle)

    @staticmethod
    def uninstall(sig=signal.SIGINT):
        logging.debug("Uninstalling Basic Interrupt Handler for: %s", signal.strsignal(sig))
        signal.signal(sig, signal.SIG_DFL)

    def __enter__(self):
        if not self._disabled:
            SignalHandler.install()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self._disabled:
            SignalHandler.uninstall()
        return


class NullHandler:
    """ An interrupt handler that does nothing """

    @staticmethod
    def handle(signum, frame):
        return

    @staticmethod
    def install(sig=signal.SIGINT):
        logging.debug("Installing Null Interrupt handler for: %s", signal.strsignal(sig))
        # Install handler for Interrupt signal
        signal.signal(sig, NullHandler.handle)

    @staticmethod
    def uninstall(sig=signal.SIGINT):
        logging.debug("Uninstalling Null Interrupt handler for: %s", signal.strsignal(sig))
        signal.signal(sig, signal.SIG_DFL)

    def __enter__(self):
        if not self._disabled:
            NullHandler.install()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self._disabled:
            NullHandler.uninstall()
        return
