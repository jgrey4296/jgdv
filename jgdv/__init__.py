#!/usr/bin/env python3
"""
JGDV, my kitchen sink library.


"""
__version__ = "1.2.1"

from ._abstract import protocols as protos
from ._abstract.types import *  # noqa: F403
from ._abstract import prelude
from . import errors
from .errors import JGDVError
from .decorators import Mixin, Proto

# Subpackage Accessors
from ._abstract import types as Types # noqa: N812
import jgdv.decorators as Decos  # noqa: N812

def identity_fn[T](x:T) -> T:
    """ Just returns what it gets """
    return x
