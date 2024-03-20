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

import sh

def exiftool_pdf_md(path) -> str:
    result = ""
    try:
        response = subprocess.run(["exiftool", str(path), "-PDF:all"],
                                  capture_output=True,
                                  shell=False)
        result = response.stdout.decode() if response.returncode == 0 else response.stderr.decode()

    except Exception as err:
        result = str(err)

    return result

def exiftool_xmp_md(path) -> str:
    result = ""
    try:
        response = subprocess.run(["exiftool", str(path), "-XMP:all"],
                                  capture_output=True,
                                  shell=False)
        result = response.stdout.decode() if response.returncode == 0 else response.stderr.decode()

    except Exception as err:
        result = str(err)

    return result
