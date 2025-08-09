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
import os
import pathlib as pl
import pdb
import re
import signal
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
# isort: on
# ##-- end types

# ##-- type checking
# isort: off
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe
## isort: on
# ##-- end type checking

##-- logging
logging    = logmod.getLogger(__name__)
##-- end logging

env        : dict        = cast("dict", os.environ)
PRE_COMMIT : Final[bool] = "PRE_COMMIT" in env
BREAK_HEADER : Final[str] = "\n---- Task Interrupted ---- "

##--| Body:

class SignalHandler:
    """ Install a breakpoint to run on (by default) SIGINT

    disables itself if PRE_COMMIT is in the environment.
    Can act as a context manager

    """

    def __init__(self) -> None:
        self._disabled = PRE_COMMIT

    @staticmethod
    def handle(signum, frame) -> None:
        breakpoint(header=BREAK_HEADER)
        SignalHandler.install()

    @staticmethod
    def install(sig=signal.SIGINT) -> None:
        logging.debug("Installing Basic Interrupt Handler for: %s", signal.strsignal(sig))
        signal.signal(sig, SignalHandler.handle)

    @staticmethod
    def uninstall(sig=signal.SIGINT) -> None:
        logging.debug("Uninstalling Basic Interrupt Handler for: %s", signal.strsignal(sig))
        signal.signal(sig, signal.SIG_DFL)

    def __enter__(self) -> Self:
        if not self._disabled:
            SignalHandler.install()
        return self

    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool:
        if not self._disabled:
            SignalHandler.uninstall()
        if etype is None:
            return False
        return True

class NullHandler:
    """ An interrupt handler that does nothing """

    @staticmethod
    def handle(signum, frame) -> None:
        return

    @staticmethod
    def install(sig=signal.SIGINT) -> None:
        logging.debug("Installing Null Interrupt handler for: %s", signal.strsignal(sig))
        # Install handler for Interrupt signal
        signal.signal(sig, NullHandler.handle)

    @staticmethod
    def uninstall(sig=signal.SIGINT) -> None:
        logging.debug("Uninstalling Null Interrupt handler for: %s", signal.strsignal(sig))
        signal.signal(sig, signal.SIG_DFL)

    def __enter__(self) -> None:
        if not self._disabled:
            NullHandler.install()
        return self

    def __exit__(self, etype:Maybe[type], err:Maybe[Exception], tb:Maybe[Traceback]) -> bool:
        if not self._disabled:
            NullHandler.uninstall()
        if etype is None:
            return False
        return True
