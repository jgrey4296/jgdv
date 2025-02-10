#!/usr/bin/env python3

__version__ = "0.3.2"

from . import prelude
from ._types import *
from . import errors
from jgdv.decorators.class_decorators import Mixin, Proto, check_protocol, CheckProtocol
from .errors import JGDVError

def identity_fn(x):
    """ Just returns what it gets """
    return x
