#!/usr/bin/env python3
"""
JGDV, my kitchen sink library.


"""
__version__ = "1.0.0"

from . import prelude
from ._types import *
from . import errors
from jgdv.decorators import Mixin, Proto
from .errors import JGDVError

def identity_fn(x):
    """ Just returns what it gets """
    return x
