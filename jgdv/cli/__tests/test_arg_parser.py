#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN201, PLR0133, B011, ANN001, ANN202
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

from .. import param_spec as Specs  # noqa: N812
from ..arg_parser import CLIParser, ParseMachine, ParseResult_d
from ..param_spec import ParamSpec
from ..import param_spec as core

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

@dataclass
class _ParamSource:
    name : str
    _param_specs : list[ParamSpec]

    def param_specs(self) -> list[ParamSpec]:
        return self._param_specs

##--|

class TestParseMachine:

    def test_sanity(self):
        assert(True is not False)

    def test_parse_empty(self):
        obj = ParseMachine()
        match obj([], head_specs=[], cmds=[], subcmds=[]):
            case {"head": {}, "cmd": {}, "sub":{}, "extra":{"args":{}, "name": "_extra_"}}:
                assert(True)
            case x:
                assert(False), x

    def test_parse_no_specs(self):
        obj = ParseMachine()
        match obj(["test", "blah"], head_specs=[], cmds=[], subcmds=[]):
            case {"head": {}, "cmd": {}, "sub":{}, "extra":{"args":{}, "name": "_extra_"}}:
                assert(True)
            case x:
                assert(False), x

class TestParser:

    @pytest.fixture(scope="function")
    def a_source(self) -> _ParamSource:

        def builder(name:str) -> ParamSource_p:
            obj = _ParamSource(name=name,
                               _param_specs=[
                                   core.ToggleParam(name="-on", type=bool),
                                   core.KeyParam(name="-val"),
                               ],
                               )
            return obj
        ##--|
        return builder

    def test_sanity(self):
        assert(True is not False)

    def test_setup(self, a_source):
        obj = CLIParser()
        obj._setup(["a","b","c"], [ParamSpec(name="blah")], [a_source("testcmd")], [])
        assert(obj._initial_args == ["a","b","c"])
        assert(obj._remaining_args == ["a","b","c"])
        assert(len(obj._head_specs) == 1)
        assert(obj._head_specs[0].name == "blah")
        assert("testcmd" in obj._cmd_specs)
        assert(not bool(obj._subcmd_specs))

    def test_check_for_help_flag(self):
        obj = CLIParser()
        obj._remaining_args = ["a","b","c", "--help"]
        obj.help_flagged()
        assert(obj._force_help)

    def test_check_for_help_flag_fail(self):
        obj = CLIParser()
        obj._remaining_args = ["a","b","c"]
        obj.help_flagged()
        assert(not obj._force_help)

    def test_parse_empty(self, a_source):
        the_cmd  = a_source("testcmd")
        in_args  = []
        obj      = CLIParser()
        obj._setup(in_args, [ParamSpec(name="blah")], [the_cmd], [])
        obj._parse_head()
        assert(True)

    def test_parse_head(self, a_source):
        the_cmd  = a_source("testcmd")
        in_args  = ["-blah","b","c"]
        obj = CLIParser()
        obj._setup(in_args, [ParamSpec(name="-blah")], [the_cmd], [])
        obj._parse_head()
        assert(obj.head_result.name == "_head_")
        assert(obj.head_result.args['blah'] is True)

    def test_parse_cmd(self, a_source):
        the_cmd  = a_source("testcmd")
        in_args  = ["testcmd", "-val", "aweg", "b","c"]
        obj      = CLIParser()
        obj._setup(in_args, [], [the_cmd], [])
        assert(bool(obj._cmd_specs))
        obj._parse_cmd()
        assert(obj.cmd_result.name == "testcmd")
        match obj.cmd_result.args:
            case {"val": "aweg"}:
                assert(True)
            case x:
                assert(False), x

    def test_parse_cmd_arg_same_as_subcmd(self, a_source):
        the_cmd  = a_source("testcmd")
        in_args = ["testcmd", "-val", "blah", "b","c"]
        obj      = CLIParser()
        obj._setup(in_args, [], [the_cmd], [])
        assert(bool(obj._cmd_specs))
        obj._parse_cmd()
        assert(obj.cmd_result.name == "testcmd")
        match obj.cmd_result.args:
            case {"val": "blah"}:
                assert(True)
            case x:
                 assert(False), x
        assert(not bool(obj.subcmd_results))

    def test_parse_subcmd(self, a_source):
        first_cmd   = a_source("testcmd")
        second_cmd  = a_source("blah")
        in_args     = ["testcmd", "blah"]
        obj         = CLIParser()
        obj._setup(in_args, [], [first_cmd], [(first_cmd.name, second_cmd)])
        assert(obj._subcmd_specs['blah'] == ("testcmd", second_cmd.param_specs()))
        assert(not bool(obj.subcmd_results))
        obj._parse_cmd()
        obj._parse_subcmd()
        assert(obj.cmd_result.name == "testcmd")
        assert(len(obj.subcmd_results) == 1)
        assert(obj.subcmd_results[0].name == "blah")

    def test_parse_multi_subcmd(self, a_source):
        first_cmd             = a_source("testcmd")
        second_cmd            = a_source("blah")
        third_cmd             = a_source("bloo")
        in_args               = ["testcmd", "blah", "-on", "--", "bloo", "-val", "lastval"]
        expected_sub_results  = 2
        obj                   = CLIParser()
        obj._setup(in_args,
                   [],
                   [first_cmd],
                   [(first_cmd.name, second_cmd), (first_cmd.name, third_cmd)])
        assert(obj._subcmd_specs['blah'] == ("testcmd", first_cmd.param_specs()))
        assert(not bool(obj.subcmd_results))
        obj._parse_cmd()
        obj._parse_subcmd()
        assert(obj.cmd_result.name == "testcmd")
        assert(len(obj.subcmd_results) == expected_sub_results)
        assert(obj.subcmd_results[0].name == "blah")
        match obj.subcmd_results[0].args:
            case {"on": True}:
                assert(True)
            case x:
                 assert(False), x

        match obj.subcmd_results[1].args:
            case {"on": False, "val": "lastval"}:
                assert(True)
            case x:
                 assert(False), x

class TestParseResultReport:

    def test_sanity(self):
        assert(True is not False)

    def test_report(self):
        obj = CLIParser()
        obj.head_result = ParseResult_d(name="blah")
        obj.cmd_result = ParseResult_d(name="bloo")
        obj.subcmd_results = []
        match obj.report():
            case {"head": {"name":"blah"}, "cmd": {"name":"bloo"}}:
                assert(True)
            case x:
                 assert(False), x

class TestParseArgs:

    def test_sanity(self):
        assert(True is not False)

    def test_non_positional_params(self):
        params = [
            core.ToggleParam(**{"name":"--aweg", "type":"bool"}),
            core.KeyParam(**{"name":"-val", "type":"str"}),
            core.ToggleParam(**{"name":"-on", "type":"bool"}),
        ]
        obj = CLIParser()
        obj._setup(["--aweg", "-val", "bloo", "-on", "blah"], [],[],[])
        result = ParseResult_d("test results")
        obj._parse_params_unordered(result, params)
        assert(result.args['aweg'] is True)
        assert(result.args['on'] is True)
        assert(result.args['val'] == "bloo")

    def test_positional_params(self):
        params = sorted([
            core.PositionalParam(**{"name":"<4>val",  "type":"str"}),
            core.PositionalParam(**{"name":"<1>blah", "type":"str"}),
            core.PositionalParam(**{"name":"<2>bloo", "type":"str"}),
        ], key=ParamSpec.key_func)
        obj = CLIParser()
        # -on before --aweg
        obj._setup(["first", "second", "third"], [],[],[])
        result = ParseResult_d("test results")
        obj._parse_params_unordered(result, params)
        assert(result.args['blah'] == "first")
        assert(result.args['bloo'] == "second")
        assert(result.args['val'] == "third")
