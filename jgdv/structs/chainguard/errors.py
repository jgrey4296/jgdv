#!/usr/bin/env python3
"""

"""

##-- builtin imports
from __future__ import annotations

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

##-- end builtin imports

from jgdv import JGDVError

class ChainGuardError(JGDVError):
    pass

class GuardedAccessError(AttributeError, ChainGuardError):
    pass
