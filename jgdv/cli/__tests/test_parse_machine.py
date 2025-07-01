#!/usr/bin/env python3
"""

"""
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

from .. import param_spec as Specs
from ..parser_model import CLIParserModel
from ..parse_machine import ParseMachine
from ..param_spec import ParamSpec

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

# Logging:
logging = logmod.root

# Global Vars:

# Body:
class TestMachine:

    def test_sanity(self):
        assert(True is not False)

    def test_creation(self):
        machine = ParseMachine()
        assert(machine is not None)
        assert(isinstance(machine.model, CLIParser))

    def test_with_custom_model(self):

        class SubParser(CLIParser):
            pass

        machine = ParseMachine(parser=SubParser())
        assert(machine is not None)
        assert(isinstance(machine.model, SubParser))

    def test_setup_ransition(self):
        machine = ParseMachine()
        assert(machine.current_state.id == "Start")
        machine.setup(["a","b","c","d"], None, None, None)
        assert(machine.current_state.id == "Head")

    def test_setup_with_no_more_args(self):
        machine = ParseMachine()
        assert(machine.current_state.id == "Start")
        machine.setup([], None, None, None)
        assert(machine.current_state.id == "ReadyToReport")

    def test_parse_transition(self):
        machine = ParseMachine()
        machine.current_state = machine.Head
        assert(machine.current_state.id == "Head")
        machine.parse()
        assert(machine.current_state.id == "ReadyToReport")

    def test_finish_transition(self):
        machine = ParseMachine()
        machine.current_state = machine.ReadyToReport
        assert(machine.current_state.id == "ReadyToReport")
        machine.finish()
        assert(machine.current_state.id == "End")

    def test_setup_too_many_attempts(self):
        machine = ParseMachine()
        machine.max_attempts = 1
        with pytest.raises(StopIteration):
            machine.setup(["doot", "test"], [], [], [])

    def test_parse_too_many_attempts(self):
        machine = ParseMachine()
        machine.current_state = machine.Head
        machine.model._remaining_args = [1,2,3,4]
        machine.max_attempts = 1
        with pytest.raises(StopIteration):
            machine.parse(["doot", "test"], [], [], [])

    def test_finish_too_many_attempts(self):
        machine = ParseMachine()
        machine.current_state = machine.ReadyToReport
        machine.max_attempts = 1
        with pytest.raises(StopIteration):
            machine.finish()


class TestMachine_Dot:
    """ Write out the dot graphs of the machines """

    @pytest.fixture(scope="function")
    def fsm(self) -> StateMachine:
        model = None
        return ParseMachine(CLIParserModel())

    @pytest.fixture(scope="function")
    def target(self):
        target = pl.Path(__file__).parent.parent  / "_graphs"
        if not target.exists():
            target.mkdir()
        return target

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_parser_dot(self, fsm, target):
        fsm_name  = type(fsm).__name__
        text      = fsm._graph().to_string()
        tfile     = target / f"_{fsm_name}.dot"
        tfile.write_text(text)
        assert(tfile.exists())
