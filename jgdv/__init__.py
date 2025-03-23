#!/usr/bin/env python3
"""
JGDV, my kitchen sink library.


"""
__version__ = "1.0.1"

from . import _types as Types      # noqa: N812
from . import decorators as Decos  # noqa: N812
from . import errors
from . import prelude
from ._abstract import protocols as protos
from ._types import *  # noqa: F403
from .errors import JGDVError
from .decorators import Mixin, Proto

def identity_fn[T](x:T) -> T:
    """ Just returns what it gets """
    return x
