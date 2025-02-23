#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import itertools as itz
import logging as logmod
import warnings
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
##-- end imports
logging = logmod.root

import pytest
from jgdv.cli import ParseError
from jgdv.cli.param_spec import ParamSpec
from jgdv.cli.param_spec.defaults import HelpParam, VerboseParam, SeparatorParam

good_names = ("test", "blah", "bloo")
bad_names  = ("-test", "blah=bloo")

class TestHelpParam:

    def test_sanity(self):
        assert(True is not False)

    @pytest.mark.skip
    def test_todo(self):
        pass

class TestVerboseParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    @pytest.mark.skip
    def test_todo(self):
        pass

class TestSeparatorParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    @pytest.mark.skip
    def test_todo(self):
        pass
