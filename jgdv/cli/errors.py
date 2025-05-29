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

from jgdv.errors import JGDVError

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
