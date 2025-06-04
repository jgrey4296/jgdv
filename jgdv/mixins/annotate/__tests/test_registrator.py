#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011, PLR2004
# Imports
from __future__ import annotations

##-- stdlib imports
import logging as logmod
import pathlib as pl
from typing import (Any, ClassVar, Generic, TypeAlias,
                    TypeVar, cast)
from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping, Sequence
from re import Match
from types import GenericAlias
import warnings

##-- end stdlib imports

import pytest
from .. import Subclasser
from ..annotate import SubAnnotate_m
from ..registrator import SubRegistry_m
from .._interface import AnnotationTarget

# Logging:
logging = logmod.root

# Global Vars:

class BasicEx(SubAnnotate_m):
    pass

class BasicSub(BasicEx):
    pass

class BasicTargeted(SubAnnotate_m, AnnotateTo="blah"):
    pass

##--|

class TestAnnotate_Registry:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_registry(self):

        class BasicReg(SubRegistry_m):
            pass

        class BasicSubReg(BasicReg[int]):
            pass

        class BasicSubOther(BasicReg[float]):
            pass

        assert(BasicReg[int] is BasicSubReg)
        assert(BasicReg[float] is not BasicReg[int])
        assert(int in BasicReg._registry)
        assert(BasicReg._registry is BasicSubReg._registry)

