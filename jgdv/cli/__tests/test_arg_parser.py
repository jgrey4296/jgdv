#!/usr/bin/env python4
"""

"""
# ruff: noqa: ANN201, PLR0133, B011, ANN001
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

# ##-- 1st party imports
import jgdv.cli.param_spec as Specs  # noqa: N812
from jgdv.cli.arg_parser import CLIParser, ParseMachine, ParseResult_d
from jgdv.cli.param_spec import ParamSpec

# ##-- end 1st party imports

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

class _utils:

    @pytest.fixture(scope="function")
    def a_source(self) -> _ParamSource:
        obj = _ParamSource(name="testcmd",
                           _param_specs=[
                               ParamSpec(name="-on", type=bool),
                               ParamSpec(name="-val"),
                           ],
                           )
        return obj

    @pytest.fixture(scope="function")
    def b_source(self) -> _ParamSource:
        obj = _ParamSource(name="blah",
                           _param_specs=[
                               ParamSpec(name="-on",  type=bool),
                               ParamSpec(name="-val", type=str),
                           ],
                           )
        return obj

    @pytest.fixture(scope="function")
    def c_source(self) -> _ParamSource:
        obj = _ParamSource(name="bloo",
                           _param_specs=[
                               ParamSpec(name="-on", type=bool),
                               ParamSpec(name="-val", type=str),
                           ],
                           )
        return obj

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

class TestParser(_utils):

    def test_sanity(self):
        assert(True is not False)

    def test_setup(self, a_source):
        obj = CLIParser()
        obj._setup(["a","b","c"], [ParamSpec(name="blah")], [a_source], [])
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
        obj = CLIParser()
        obj._setup([], [Specs.LiteralParam(name="blah")], [a_source], [])
        obj._parse_head()

    def test_parse_head(self, a_source):
        obj = CLIParser()
        obj._setup(["blah","b","c"], [Specs.LiteralParam(name="blah")], [a_source], [])
        obj._parse_head()
        assert(obj.head_result.name == "_head_")
        assert(obj.head_result.args['blah'] is True)

    def test_parse_cmd(self, a_source):
        obj = CLIParser()
        obj._setup(["testcmd", "-val", "aweg", "b","c"], [], [a_source], [])
        assert(bool(obj._cmd_specs))
        pass
        obj._parse_cmd()
        assert(obj.cmd_result.name == "testcmd")
        match obj.cmd_result.args:
            case {"val": "aweg"}:
                assert(True)
            case x:
                assert(False), x

    def test_parse_cmd_arg_same_as_subcmd(self, a_source):
        obj = CLIParser()
        obj._setup(["testcmd", "-val", "blah", "b","c"], [], [a_source], [])
        assert(bool(obj._cmd_specs))
        obj._parse_cmd()
        assert(obj.cmd_result.name == "testcmd")
        match obj.cmd_result.args:
            case {"val": "blah"}:
                assert(True)
            case x:
                 assert(False), x
        assert(not bool(obj.subcmd_results))

    def test_parse_subcmd(self, a_source, b_source):
        obj = CLIParser()
        obj._setup(["testcmd", "blah"], [], [a_source], [(a_source.name, b_source)])
        assert(obj._subcmd_specs['blah'] == ("testcmd", b_source.param_specs()))
        assert(not bool(obj.subcmd_results))
        obj._parse_cmd()
        obj._parse_subcmd()
        assert(obj.cmd_result.name == "testcmd")
        assert(len(obj.subcmd_results) == 1)
        assert(obj.subcmd_results[0].name == "blah")

    def test_parse_multi_subcmd(self, a_source, b_source, c_source):
        expected_sub_results = 2
        obj = CLIParser()
        obj._setup(["testcmd", "blah", "-on", "--", "bloo", "-val", "lastval"],
                   [], [a_source], [(a_source.name, b_source), (a_source.name, c_source)])
        assert(obj._subcmd_specs['blah'] == ("testcmd", b_source.param_specs()))
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

    def test_ordered(self):
        params = [
            ParamSpec.build({"prefix":"--", "name":"aweg", "type":"bool"}),
            ParamSpec.build({"name":"on", "type":"bool"}),
            ParamSpec.build({"prefix":1, "name":"val", "type":"str"}),
        ]
        obj = CLIParser()
        obj._setup(["--aweg", "-on", "blah"], [],[],[])
        result = ParseResult_d("test results")
        obj._parse_params(result, params)
        assert(result.args['aweg'] is True)
        assert(result.args['on'] is True)
        assert(result.args['val'] == "blah")

    def test_ordered_fails(self):
        params = [
            ParamSpec.build({"name":"--aweg", "type":"bool"}),
            ParamSpec.build({"name":"-on", "type":"bool"}),
            ParamSpec.build({"name":"<1>val", "type":"str"}),
        ]
        obj = CLIParser()
        # -on before --aweg
        obj._setup(["-on", "--aweg", "blah"], [],[],[])
        result = ParseResult_d("test results")
        obj._parse_params(result, params)
        assert(result.args['on'])
        assert("aweg" not in result.args)
        assert(result.args['val'] == "--aweg")

    def test_unordered(self):
        params = [
            ParamSpec(**{"name":"--aweg", "type":"bool"}),
            ParamSpec(**{"name":"-on", "type":"bool"}),
            ParamSpec(**{"name":"<1>val", "type":"str"}),
        ]
        obj = CLIParser()
        # -on before --aweg
        obj._setup(["-on", "--aweg", "blah"], [],[],[])
        result = ParseResult_d("test results")
        obj._parse_params_unordered(result, params)
        assert(result.args['on'])
        assert(result.args['aweg'])
        assert(result.args['val'] == "blah")
