#!/usr/bin/env python3
"""

"""
# Import:
from __future__ import annotations

# ##-- stdlib imports
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
from uuid import UUID, uuid1
# ##-- end stdlib imports

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

    type Logger = logmod.Logger

# isort: on
# ##-- end types

from ._interface import LogLevel_e

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
LoggerClass : Final[type] = logmod.getLoggerClass()
# Body:

class JGDVLogger(LoggerClass):
    """ Basic extension of the logger class

    checks the classvar _levels (intEnum) for additional log levels
    which can be accessed as attributes and items.
    eg: logger.trace(...)
    and: logger['trace'](...)


    A Logger can add prefixes to a logged messages.
    eg:_

    ..code: python

        logger.set_prefixes('[Test]')
        logger.info('this is a test message')
        # Result :  '[Test] this is a test message'

    """
    _prefixes  : list[str|Callable]
    _colour    : Maybe[str]

    @classmethod
    def install(cls) -> None:
        logmod.setLoggerClass(cls)

    def __init__(self, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self._prefixes = []
        self._colour   = None

    def __getattr__(self, attr:str) -> Callable:
        try:
            return ftz.partial(self.log, LogLevel_e[attr])
        except KeyError:
            msg = "Invalid Extension Log Level"
            raise AttributeError(msg, attr) from None

    def __getitem__(self, key:str) -> Callable:
        return self.__getattr__(key)

    ##--| public methods
    def set_colour(self, colour:str) -> None:
        self._colour = self._colour or colour

    def set_prefixes(self, *prefixes:str|Callable) -> None:
        """
        Set prefixes for the logger to add to logged messages
        """
        match prefixes:
            case None | ():
                pass
            case [*xs]:
                self._prefixes =  list(xs)

    def prefix(self, prefix:str|Callable) -> Self:
        """ Create a new logger, with a prefix """
        match prefix:
            case str():
                child = self.getChild(prefix)
            case x if callable(x):
                child = self.getChild(prefix.__name__)
            case _:
                raise TypeError(prefix)

        child.set_prefixes(*self._prefixes, prefix)
        return child

    def getChild(self, name:str) -> Self:  # noqa: N802
        """
        Create a child logger, copying the colour of this logger
        """
        child = super().getChild(name)
        child.set_colour(self._colour)
        return child

    def makeRecord(self, *args:Any, **kwargs:Any) -> logmod.LogRecord:  # noqa: ANN401, N802
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.
        args: name, level, fn, lno, msg, args, exc_info,
        kwargs: func=None, extra=None, sinfo=None
        """
        modified : list = list(args)
        msg_total = []
        for pre in self._prefixes:
            match pre:
                case None:
                    pass
                case str():
                    msg_total.append(pre)
                case x if callable(x):
                    msg_total.append(x())
        else:
            match args[4]:
                case str():
                    msg_total.append(args[4])
                case x:
                    msg_total.append("%s")
                    modified[5] = [args[4],  *args[5]]
            modified[4] = "".join(msg_total)

        rv = super().makeRecord(*modified, **kwargs)
        if self._colour and "colour" not in rv.__dict__:
            rv.__dict__["colour"] = self._colour
        return rv
