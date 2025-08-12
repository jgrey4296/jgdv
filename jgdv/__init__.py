#!/usr/bin/env python3
"""
JGDV, my kitchen sink library.


"""
from importlib.metadata import version
__version__ = version("jgdv")

from ._abstract import protocols as protos
from ._abstract.types import *  # noqa: F403
from ._abstract.error import JGDVError
from ._abstract import prelude
from . import errors
from .decorators import Mixin, Proto

# Subpackage Accessors
from ._abstract import types as Types # noqa: N812
import jgdv.decorators as Decos  # noqa: N812

def identity_fn[T](x:T) -> T:
    """Just returns what it gets

    :param x: A Value
    :returns: The Same Value
    """
    return x
