#!/usr/bin/env python3
"""
JGDV, my kitchen sink library.


"""
__version__ = "1.0.1"

from . import _types as Types
from . import decorators as Decos
from . import errors
from . import prelude
from ._abstract import protocols as protos
from ._types import *
from .errors import JGDVError
from .decorators import Mixin, Proto

def identity_fn(x):
    """ Just returns what it gets """
    return x
