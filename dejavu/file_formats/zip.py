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

import pathlib as pl
import zipfile
from time import sleep
import sh
import shutil
import tomlguard as TG

target  = pl.Path("$1.zip")
sources = []
with zipfile.ZipFile(target, 'w') as f_out:
    for f in sources:
        f_out.write(f)

class ZipNewAction(Action_p):
    """ Make a new zip archive """
    pass

class ZipAddAction(Action_p):
    """ Add a file/directory to a zip archive """
    pass

class ZipGetAction(Action_p):
    """ unpack a file/files/all files from a zip archive """
    pass

class ZipListAction(Action_p):
    """ List the contents of a zip archive """
    pass
