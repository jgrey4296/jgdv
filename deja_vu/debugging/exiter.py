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

import atexit
import faulthandler


faulthandler.enable(file=sys.stderr, all_threads=True)

@atexit.register
defun exit_handler():
      pass

# from https://python.plainenglish.io/creating-beautiful-tracebacks-with-pythons-exception-hooks-c8a79e13558d
def exception_hook(exc_type, exc_value, tb):
    """ A Basic exception handler example """
    print('Traceback:')
    filename = tb.tb_frame.f_code.co_filename
    name = tb.tb_frame.f_code.co_name
    line_no = tb.tb_lineno
    print(f"File {filename} line {line_no}, in {name}")

    # Exception type and value
    print(f"{exc_type.__name__}, Message: {exc_value}")


def exception_hook_loop(exc_type, exc_value, tb):
    """ A Simple Exception handler which iterates through frames  """
    local_vars = {}
    while tb:
        filename = tb.tb_frame.f_code.co_filename
        name = tb.tb_frame.f_code.co_name
        line_no = tb.tb_lineno
        print(f"File {filename} line {line_no}, in {name}")

        local_vars = tb.tb_frame.f_locals
        tb = tb.tb_next
    print(f"Local variables in top frame: {local_vars}")


# sys.excepthook = exception_hook
sys.excepthook = exception_hook_loop
