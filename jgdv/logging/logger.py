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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

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

from .enums import LogLevel_e

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class JGDVLogger(logmod.getLoggerClass()):
    """ Basic extension of the logger class

    checks the classvar _levels (intEnum) for additional log levels
    which can be accessed as attributes and items.
    eg: logger.trace(...)
    and: logger['trace'](...)
    """

    @classmethod
    def install(cls):
        logmod.setLoggerClass(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prefixes = []
        self._colour   = None

    def __getattr__(self, attr:str) -> callable:
        try:
            return ftz.partial(self.log, LogLevel_e[attr])
        except KeyError:
            raise AttributeError("Invalid Extension Log Level", attr) from None

    def __getitem__(self, key:str) -> callable:
        return self.__getattr__(key)

    def set_colour(self, colour:str):
        self._colour = self._colour or colour

    def set_prefixes(self, *prefixes:Maybe[str|callable]):
        self._prefixes =  list(prefixes)

    def prefix(self, prefix:str|callable) -> Logger:
        match prefix:
            case str():
                child = self.getChild(prefix)
            case x if callable(x):
                child = self.getChild(prefix.__name__)
            case _:
                raise TypeError(prefix)

        child.set_prefixes(*self._prefixes, prefix)
        return child

    def getChild(self, name):
        child = super().getChild(name)
        child.set_colour(self._colour)
        return child

    def makeRecord(self, *args, **kwargs):
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.
        args: name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None
        """
        args = list(args)
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
                    args[5] = [args[4]] + list(args[5])
            args[4] = "".join(msg_total)

        rv = super().makeRecord(*args, **kwargs)
        if self._colour and "colour" not in rv.__dict__:
            rv.__dict__["colour"] = self._colour
        return rv
