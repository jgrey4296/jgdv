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

import pyparsing as pp

s         = pp.Suppress
op        = pp.Optional
orm       = pp.OneOrMore
zrm       = pp.ZeroOrMore

ln                = s(pp.White("\n\r", max=1).set_whitespace_chars("\t "))
manyLine          = s(pp.White("\n\r", min=1).set_whitespace_chars("\t "))
emptyLine         = s(ln + manyLine)
opLn              = op(ln)
tab               = pp.White(TAB_S, min=2).set_whitespace_chars("\r\n")

emptyLine.set_name("emptyLine")
ln.set_name("line")
opLn.set_name("OptionalLine")
tab.set_name("tab")

def gap_fail_action(s, loc, expr, err):
    logging.warning("{}\n{}".format(str(err), err.markInputline()))
