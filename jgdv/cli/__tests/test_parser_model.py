#!/usr/bin/env python3
"""

"""
# ruff: noqa: PLR0133, ANN001, ANN202
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest

# ##-- end 3rd party imports

from .._interface import ArgParserModel_p
from .. import param_spec as Specs  # noqa: N812
from ..parser_model import CLIParserModel
from ..param_spec import ParamSpec
from .. import param_spec as core
from .._interface import ParseResult_d

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from dataclasses import InitVar, dataclass, field

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

logging = logmod.root

##--| global vars
@pytest.fixture(scope="function")
def model():
    return CLIParserModel()

@pytest.fixture(scope="function")
def PSource(): # noqa: N802

    class ASource:

        def __init__(self, *, name=None, specs=None) -> None:
            self._name = name or "simple"
            self.specs = specs or []

        @property
        def name(self) -> str:
            return self._name

        def param_specs(self) -> list:
            return self.specs

    return ASource


##--|

class TestMachine:

    def test_sanity(self):
        assert(True is not False)

    def test_creation(self, model):
        assert(model is not None)
        assert(isinstance(model, CLIParserModel))
        assert(isinstance(model, ArgParserModel_p))
