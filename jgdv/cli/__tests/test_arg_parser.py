#!/usr/bin/env python4
"""

"""
##-- imports
from __future__ import annotations

import logging as logmod
import warnings
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
from dataclasses import dataclass, field, InitVar

##-- end imports

import pytest
from jgdv.cli.arg_parser import ParseMachine, CLIParser, ParseResult
from jgdv.cli.param_spec import ParamSpec
import jgdv.cli.param_spec as Specs

logging = logmod.root

@dataclass
class _ParamSource:
    name : str
    param_specs : list[ParamSpec]


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
        obj = _ParamSource(name="testcmd",
                           param_specs=[
                               ParamSpec(name="on", type=bool),
                               ParamSpec(name="val", type=str)
                           ]
                           )
        return obj

    @pytest.fixture(scope="function")
    def b_source(self) -> _ParamSource:
        obj = _ParamSource(name="blah",
                           param_specs=[
                               ParamSpec(name="on", type=bool),
                               ParamSpec(name="val", type=str)
                           ]
                           )
        return obj

    @pytest.fixture(scope="function")
    def c_source(self) -> _ParamSource:
        obj = _ParamSource(name="bloo",
                           param_specs=[
                               ParamSpec(name="on", type=bool),
                               ParamSpec(name="val", type=str)
                           ]
                           )
        return obj

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
        assert(obj.head_result.args['blah'] == True)

    def test_parse_cmd(self, a_source):
        obj = CLIParser()
        obj._setup(["testcmd", "-val", "aweg", "b","c"], [], [a_source], [])
        assert(bool(obj._cmd_specs))
        obj._parse_cmd()
        assert(obj.cmd_result.name == "testcmd")
        match obj.cmd_result.args:
            case {"val": "aweg"}:
                assert(True)
            case _:
                assert(False)

    def test_parse_cmd_arg_same_as_subcmd(self, a_source):
        obj = CLIParser()
        obj._setup(["testcmd", "-val", "blah", "b","c"], [], [a_source], [])
        assert(bool(obj._cmd_specs))
        obj._parse_cmd()
        assert(obj.cmd_result.name == "testcmd")
        match obj.cmd_result.args:
            case {"val": "blah"}:
                assert(True)
            case _:
                assert(False)
        assert(not bool(obj.subcmd_results))

    def test_parse_subcmd(self, a_source, b_source):
        obj = CLIParser()
        obj._setup(["testcmd", "blah"], [], [a_source], [(a_source.name, b_source)])
        assert(obj._subcmd_specs['blah'] == ("testcmd", b_source.param_specs))
        assert(not bool(obj.subcmd_results))
        obj._parse_cmd()
        obj._parse_subcmd()
        assert(obj.cmd_result.name == "testcmd")
        assert(len(obj.subcmd_results) == 1)
        assert(obj.subcmd_results[0].name == "blah")

    def test_parse_multi_subcmd(self, a_source, b_source, c_source):
        obj = CLIParser()
        obj._setup(["testcmd", "blah", "-on", "--", "bloo", "-val", "lastval"],
                   [], [a_source], [(a_source.name, b_source), (a_source.name, c_source)])
        assert(obj._subcmd_specs['blah'] == ("testcmd", b_source.param_specs))
        assert(not bool(obj.subcmd_results))
        obj._parse_cmd()
        obj._parse_subcmd()
        assert(obj.cmd_result.name == "testcmd")
        assert(len(obj.subcmd_results) == 2)
        assert(obj.subcmd_results[0].name == "blah")
        match obj.subcmd_results[0].args:
            case {"on": True}:
                assert(True)
            case _:
                assert(False)

        match obj.subcmd_results[1].args:
            case {"on": False, "val": "lastval"}:
                assert(True)
            case _:
                assert(False)

    @pytest.mark.skip
    def test_parse_extra(self, a_source, b_source, c_source):
        pass

class TestParseResultReport:

    def test_sanity(self):
        assert(True is not False)

    def test_report(self):
        obj = CLIParser()
        obj.head_result = ParseResult(name="blah")
        obj.cmd_result = ParseResult(name="bloo")
        obj.subcmd_results = []
        match obj.report():
            case {"head": {"name":"blah"}, "cmd": {"name":"bloo"}}:
                assert(True)
            case _:
                assert(False)