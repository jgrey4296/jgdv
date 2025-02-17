#!/usr/bin/env python2
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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
# ##-- end stdlib imports

from jgdv import JGDVError

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Global Vars:

# Body:
class ParseError(JGDVError):
    """ A Base Error Class for JGDV CLI Arg Parsing"""
    pass

class HeadParseError(ParseError):
    """ For When an error occurs parsing the head """
    pass

class CmdParseError(ParseError):
    """ For when parsing the command section fails """
    pass

class SubCmdParseError(ParseError):
    """ For when the subcmd section fails """
    pass

class ArgParseError(ParseError):
    """ For when a head/cmd/subcmds arguments are bad """
    pass
