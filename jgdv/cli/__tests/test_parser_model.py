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
from ..parser_model import CLIParserModel
from ..parse_machine import ParseMachine
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

@dataclass
class _ParamSource:
    name : str
    _param_specs : list[ParamSpec]

    def param_specs(self) -> list[ParamSpec]:
        return self._param_specs


@pytest.fixture(scope="function")
def parser(mocker):
    return ParseMachine(CLIParserModel())

##--|

class TestParseMachine:

    def test_sanity(self):
        assert(True is not False)

    def test_no_model_errors(self):
        with pytest.raises(TypeError):
            ParseMachine()

    def test_empty_parse(self, parser):
        match parser([], prog=[], cmds=[], subs=[]):
            case {"raw": ()}:
                assert(True)
            case x:
                assert(False), x

    def test_parse_no_specs(self, parser):
        match parser(["test", "blah"], prog=[], cmds=[], subs=[]):
            case {"head": {}, "cmd": {}, "sub":{}, "extra":{"args":{}, "name": "_extra_"}}:
                assert(True)
            case x:
                assert(False), x

class TestParser:

    @pytest.fixture(scope="function")
    def a_source(self) -> _ParamSource:

        def builder(name:str) -> ParamSource_p:
            parser = _ParamSource(name=name,
                               _param_specs=[
                                   core.ToggleParam(name="-on", type=bool),
                                   core.KeyParam(name="-val"),
                               ],
                               )
            return parser
        ##--|
        return builder

    def test_sanity(self):
        assert(True is not False)

    def test_setup(self, parser, a_source):
        parser.setup(["a","b","c"], [ParamSpec(name="blah")], [a_source("testcmd")], [])
        assert(parser.model._initial_args == ["a","b","c"])
        assert(parser.model._remaining_args == ["a","b","c"])
        assert(len(parser.model._head_specs) == 1)
        assert(parser.model._head_specs[0].name == "blah")
        assert("testcmd" in parser.model._cmd_specs)
        assert(not bool(parser.model._subcmd_specs))

    def test_check_for_help_flag(self, parser):
        parser._remaining_args = ["a","b","c", "--help"]
        parser.help_flagged()
        assert(parser._force_help)

    def test_check_for_help_flag_fail(self, parser):
        parser._remaining_args = ["a","b","c"]
        parser.help_flagged()
        assert(not parser._force_help)

    def test_parse_empty(self, a_source):
        the_cmd  = a_source("testcmd")
        in_args  = []
        parser._setup(in_args, [ParamSpec(name="blah")], [the_cmd], [])
        parser._parse_head()
        assert(True)

    def test_parse_head(self, a_source):
        the_cmd  = a_source("testcmd")
        in_args  = ["-blah","b","c"]
        parser._setup(in_args, [ParamSpec(name="-blah")], [the_cmd], [])
        parser._parse_head()
        assert(parser.head_result.name == "_head_")
        assert(parser.head_result.args['blah'] is True)

    def test_parse_cmd(self, a_source):
        the_cmd  = a_source("testcmd")
        in_args  = ["testcmd", "-val", "aweg", "b","c"]
        parser      = CLIParserModel()
        parser._setup(in_args, [], [the_cmd], [])
        assert(bool(parser._cmd_specs))
        parser._parse_cmd()
        assert(parser.cmd_result.name == "testcmd")
        match parser.cmd_result.args:
            case {"val": "aweg"}:
                assert(True)
            case x:
                assert(False), x

    def test_parse_cmd_arg_same_as_subcmd(self, a_source):
        the_cmd  = a_source("testcmd")
        in_args = ["testcmd", "-val", "blah", "b","c"]
        parser      = CLIParserModel()
        parser._setup(in_args, [], [the_cmd], [])
        assert(bool(parser._cmd_specs))
        parser._parse_cmd()
        assert(parser.cmd_result.name == "testcmd")
        match parser.cmd_result.args:
            case {"val": "blah"}:
                assert(True)
            case x:
                 assert(False), x
        assert(not bool(parser.subcmd_results))

    def test_parse_subcmd(self, a_source):
        first_cmd   = a_source("testcmd")
        second_cmd  = a_source("blah")
        in_args     = ["testcmd", "blah"]
        parser         = CLIParserModel()
        parser._setup(in_args, [], [first_cmd], [(first_cmd.name, second_cmd)])
        assert(parser._subcmd_specs['blah'] == ("testcmd", second_cmd.param_specs()))
        assert(not bool(parser.subcmd_results))
        parser._parse_cmd()
        parser._parse_subcmd()
        assert(parser.cmd_result.name == "testcmd")
        assert(len(parser.subcmd_results) == 1)
        assert(parser.subcmd_results[0].name == "blah")

    def test_parse_multi_subcmd(self, a_source):
        first_cmd             = a_source("testcmd")
        second_cmd            = a_source("blah")
        third_cmd             = a_source("bloo")
        in_args               = ["testcmd", "blah", "-on", "--", "bloo", "-val", "lastval"]
        expected_sub_results  = 2
        parser                   = CLIParserModel()
        parser._setup(in_args,
                   [],
                   [first_cmd],
                   [(first_cmd.name, second_cmd), (first_cmd.name, third_cmd)])
        assert(parser._subcmd_specs['blah'] == ("testcmd", first_cmd.param_specs()))
        assert(not bool(parser.subcmd_results))
        parser._parse_cmd()
        parser._parse_subcmd()
        assert(parser.cmd_result.name == "testcmd")
        assert(len(parser.subcmd_results) == expected_sub_results)
        assert(parser.subcmd_results[0].name == "blah")
        match parser.subcmd_results[0].args:
            case {"on": True}:
                assert(True)
            case x:
                 assert(False), x

        match parser.subcmd_results[1].args:
            case {"on": False, "val": "lastval"}:
                assert(True)
            case x:
                 assert(False), x

class TestParseResultReport:

    def test_sanity(self):
        assert(True is not False)

    def test_report(self):
        parser.head_result = ParseResult_d(name="blah")
        parser.cmd_result = ParseResult_d(name="bloo")
        parser.subcmd_results = []
        match parser.report():
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
        parser._setup(["--aweg", "-val", "bloo", "-on", "blah"], [],[],[])
        result = ParseResult_d("test results")
        parser._parse_params_unordered(result, params)
        assert(result.args['aweg'] is True)
        assert(result.args['on'] is True)
        assert(result.args['val'] == "bloo")

    def test_positional_params(self):
        params = sorted([
            core.PositionalParam(**{"name":"<4>val",  "type":"str"}),
            core.PositionalParam(**{"name":"<1>blah", "type":"str"}),
            core.PositionalParam(**{"name":"<2>bloo", "type":"str"}),
        ], key=ParamSpec.key_func)
        # -on before --aweg
        parser._setup(["first", "second", "third"], [],[],[])
        result = ParseResult_d("test results")
        parser._parse_params_unordered(result, params)
        assert(result.args['blah'] == "first")
        assert(result.args['bloo'] == "second")
        assert(result.args['val'] == "third")
