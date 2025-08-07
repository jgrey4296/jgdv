#!/usr/bin/env python3
"""


"""
# ruff: noqa: ANN202

# Imports
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest
# ##-- end 3rd party imports


##--|
from .. import JGDVLogConfig
##--|

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:
class TestLogConfig:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133


    def test_basic(self):
        obj   = JGDVLogConfig(force_new=True)
        obj2  = JGDVLogConfig(force_new=True)
        assert(obj is not obj2)


    ##--|
    @pytest.mark.skip
    def test_todo(self):
        pass
