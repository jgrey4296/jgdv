#!/usr/bin/env python3
"""

"""
# Imports
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings
# ##-- stdlib imports

import pytest
from jgdv.cli.arg_parser import ParseMachine, CLIParser
from jgdv.cli.param_spec import ParamSpec, ArgParseError
import jgdv.cli.param_spec as Specs

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

    def test_setup_ith_no_more_args(self):
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
