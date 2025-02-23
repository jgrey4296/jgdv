#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

import pytest
from jgdv.structs.strang import Strang, CodeReference

logging = logmod.root

@pytest.mark.xfail
class TestBuildAppropriate:

    def test_sanity(self):
        assert(True is True)

    def test_simple(self):
        obj = Strang("group::tail.a.b.c")
        assert(isinstance(obj, Strang))
        assert(not isinstance(obj, CodeReference))


    def test_simple_coderef(self):
        obj = Strang("fn::tail.a.b.c:build_fn")
        assert(isinstance(obj, Strang))
        assert(isinstance(obj, CodeReference))




    @pytest.mark.skip
    def test_todo(self):
        pass
