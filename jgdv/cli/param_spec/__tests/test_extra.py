#!/usr/bin/env python3
"""

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
from ..param_spec import ParamSpec
from .. import extra
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

@pytest.mark.skip
class TestRepeatableParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_consume_list_single_value(self):
        obj = extra.RepeatableParam(**{"name" : "test", "type" : list})
        match obj.consume(["-test", "bloo"]):
            case {"test": ["bloo"]}, 2:
                assert(True)
            case x:
                assert(False), x

    def test_consume_list_multi_key_val(self):
        obj     = extra.RepeatableParam(**{"name":"test"})
        in_args = ["-test", "bloo", "-test", "blah", "-test", "bloo", "-not", "this"]
        match obj.consume(in_args):
            case {"test": ["bloo", "blah", "bloo"]}, 6:
                assert(True)
            case x:
                assert(False), x

    def test_consume_set_multi(self):
        obj = extra.RepeatableParam[set](**{
            "name"    : "test",
            "type"    : set,
            "default" : set,
          })
        in_args             = ["-test", "bloo", "-test", "blah", "-test", "bloo", "-not", "this"]
        match obj.consume(in_args):
            case {"test": set() as x}, 6:
                assert(x == {"bloo", "blah"})
            case x:
                assert(False), x

    def test_consume_str_multi_set_fail(self):
        obj = extra.RepeatableParam[set](**{
            "name" : "test",
            "type" : str,
            "default" : "",
          })
        in_args             = ["-nottest", "bloo", "-nottest", "blah", "-nottest", "bloo", "-not", "this"]
        match obj.consume(in_args):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_consume_multi_assignment_fail(self):
        obj     = extra.RepeatableParam(**{"name":"test", "type":list, "default":list, "prefix":"--"})
        in_args = ["--test=blah", "--test=bloo"]
        match obj.consume(in_args):
            case None:
                assert(True)
            case x:
                assert(False), x

@pytest.mark.skip
class TestImplicitParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

@pytest.mark.skip
class TestChoiceParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

@pytest.mark.skip
class TestEntryParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

@pytest.mark.skip
class TestConstrainedParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

@pytest.mark.skip
class TestLiteralParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_literal(self):
        obj = extra.LiteralParam(name="blah")
        match obj.consume(["blah"]):
            case {"blah":True}, 1:
                assert(True)
            case None:
                assert(False)

    def test_literal_fail(self):
        obj = extra.LiteralParam(name="blah")
        match obj.consume(["notblah"]):
            case None:
                assert(True)
            case _:
                assert(False)

@pytest.mark.skip
class TestWildCardParam:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_wildcard_assign(self):
        obj = extra.WildcardParam()
        match obj.consume(["--blah=other"]):
            case {"blah":"other"}, 1:
                assert(True)
            case x:
                assert(False), x
