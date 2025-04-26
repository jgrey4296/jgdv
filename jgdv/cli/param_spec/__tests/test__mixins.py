#!/usr/bin/env python3
"""
TEST File updated

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202, B011

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
from .._mixins import _ParamNameParser_m
##--|

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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class TestSuite:

    ##--|

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match _ParamNameParser_m._parse_name("-blah"):
            case {"name": "blah", "prefix": "-"}:
                assert(True)
            case x:
                 assert(False), x

    def test_prefix(self):
        match _ParamNameParser_m._parse_name("--blah"):
            case {"name": "blah", "prefix": "--"}:
                assert(True)
            case x:
                 assert(False), x

    def test_prefix_alt(self):
        match _ParamNameParser_m._parse_name("+blah"):
            case {"name": "blah", "prefix": "+"}:
                assert(True)
            case x:
                 assert(False), x

    def test_assignment(self):
        match _ParamNameParser_m._parse_name("--blah="):
            case {"name": "blah", "prefix": "--", "separator":"="}:
                assert(True)
            case x:
                 assert(False), x

    def test_nonspecific_positional(self):
        match _ParamNameParser_m._parse_name("blah"):
            case {"name": "blah", "prefix": 99}:
                assert(True)
            case x:
                 assert(False), x


    def test_specific_positional(self):
        match _ParamNameParser_m._parse_name("<2>blah"):
            case {"name": "blah", "prefix": 2}:
                assert(True)
            case x:
                 assert(False), x


    @pytest.mark.xfail
    def test_count(self):
        """ TODO parse counts in the name

        eg: -blah[4] means -blah can be used 4 times
        """
        match _ParamNameParser_m._parse_name("-blah[4]"):
            case {"name": "blah", "prefix": "-", "count":4}:
                assert(True)
            case x:
                 assert(False), x

    ##--|

    @pytest.mark.skip
    def test_todo(self):
        pass
