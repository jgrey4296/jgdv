#!/usr/bin/env python3
"""

"""
# ruff: noqa: ARG001, ANN202, N802, ANN001, ANN204, B011, N803, PLR2004

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

from .._interface import ParseResult_d
from .. import param_spec as Specs  # noqa: N812
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
    from statemachine import StateMachine

##--|

# isort: on
# ##-- end types

# Logging:
logging = logmod.root

# Global Vars:

@pytest.fixture(scope="function")
def parser(mocker):
    return ParseMachine(CLIParserModel())

@pytest.fixture(scope="function")
def PSource(mocker):

    class ASource:

        def __init__(self, *, name=None, specs=None):
            self._name = name or "simple"
            self.specs = specs or []

        @property
        def name(self) -> str:
            return self._name

        def param_specs(self) -> list:
            return self.specs

    return ASource


##--| body

class TestMachine:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_creation(self, parser):
        assert(parser is not None)
        assert(isinstance(parser.model, CLIParserModel))

    def test_with_custom_model(self):

        class SubParser(CLIParserModel):
            pass

        parser = ParseMachine(parser=SubParser())
        assert(parser is not None)
        assert(isinstance(parser.model, SubParser))

    def test_empty_parse(self, parser):
        assert(parser.current_state.id == "Start")
        match parser([], prog=None, cmds=[], subs=[]):
            case None:
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_parse_no_specs(self, parser):
        assert(parser.current_state.id == "Start")
        match parser(["a", "b","c", "d"], prog=None, cmds=[], subs=[]):
            case None:
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_parse_simple_spec(self, parser, PSource):
        assert(parser.current_state.id == "Start")
        prog = PSource(name="blah",
                       specs=[ParamSpec(name="-a")])
        match parser(["blah", "-a", "b","c", "d"], prog=prog, cmds=[], subs=[]):
            case {"remaining":rem, "prog":ParseResult_d() as progargs}:
                assert(rem == ["b","c","d"])
                assert(progargs.args['a'] is True)
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_parse_help(self, parser, PSource):
        assert(parser.current_state.id == "Start")
        prog = PSource(name="bloo",
                       specs=[ParamSpec(name="-a")])
        match parser(["bloo", "--help"], prog=prog, cmds=[], subs=[]):
            case {"remaining":rem, "help":True}:
                assert(rem == [])
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_parse_cmd(self, parser, PSource):
        assert(parser.current_state.id == "Start")
        psource = PSource()
        match parser(["python", psource.name], prog=None, cmds=[psource], subs=[]):
            case {"remaining":rem, "cmds":{"simple": ParseResult_d(name="simple")}}:
                assert(rem == [])
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_parse_cmd_with_arg(self, parser, PSource):
        assert(parser.current_state.id == "Start")
        psource = PSource(specs=[ParamSpec[bool](name="-blah", default=False)])
        assert(psource.name == "simple")
        match parser(["python", "simple"],
                     prog=None,
                     cmds=[psource],
                     subs=[]):
            case {"remaining":rem, "cmds":{"simple": cmdargs}}:
                assert(rem == [])
                assert(cmdargs.name == "simple")
                assert(cmdargs.args['blah'] is False)
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_parse_cmd_with_parsed_arg(self, parser, PSource):
        assert(parser.current_state.id == "Start")
        psource = PSource(specs=[ParamSpec[bool](name="-blah", default=False)])
        assert(psource.name == "simple")
        match parser(["python", "simple", "-blah"],
                     prog=None,
                     cmds=[psource],
                     subs=[]):
            case {"remaining":rem, "cmds":{"simple": cmdargs}}:
                assert(rem == [])
                assert(cmdargs.name == "simple")
                assert(cmdargs.args['blah'] is True)
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_parse_cmd_and_sub(self, parser, PSource):
        assert(parser.current_state.id == "Start")
        ##--|
        prog  = PSource(name="aweg", specs=[])
        cmd   = PSource(name="acmd", specs=[ParamSpec[bool](name="-blah", default=False)])
        sub   = PSource(name="asub", specs=[ParamSpec[bool](name="-blah", default=False)])
        match parser(["aweg", "acmd", "-blah", "asub"],
                     prog=prog,
                     cmds=[cmd],
                     subs=[((cmd.name,), sub)]):
            case {"remaining":rem, "cmds":{"acmd": cmdargs}, "subs": dict() as subs}:
                assert(rem == [])
                assert(cmdargs.args['blah'] is True)
                assert("acmd" in subs)
                assert(len(subs['acmd']) == 1)
                assert(subs['acmd'][0].name == "asub")
                assert(subs['acmd'][0].args['blah'] is False)
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_parse_multi_subs(self, parser, PSource):
        assert(parser.current_state.id == "Start")
        ##--|
        prog  = PSource(name="aweg", specs=[])
        cmd   = PSource(name="acmd", specs=[ParamSpec[bool](name="-blah", default=False)])
        sub   = PSource(name="asub", specs=[
            ParamSpec[bool](name="-blah", default=False),
            ParamSpec[bool](name="-bloo", default=False),
        ])
        match parser(["aweg", "acmd", "-blah", "asub", "--", "asub", "-bloo"],
                     prog=prog,
                     cmds=[cmd],
                     subs=[((cmd.name,), sub)]):
            case {"remaining":rem, "cmds":{"acmd": cmdargs}, "subs": dict() as subs}:
                assert(rem == [])
                assert(cmdargs.args['blah'] is True)
                assert("acmd" in subs)
                assert(len(subs['acmd']) == 2)
                sub1, sub2 = subs['acmd']
                assert(sub1.name == "asub")
                assert(sub1.args['bloo'] is False)
                assert(sub2.name == "asub")
                assert(sub2.args['bloo'] is True)
                assert(parser.current_state_value == "End")
            case x:
                assert(False), x


    def test_multi_cmds(self, parser, PSource):
        assert(parser.current_state.id == "Start")
        ##--|
        prog  = PSource(name="aweg", specs=[])
        cmd1   = PSource(name="acmd", specs=[ParamSpec[bool](name="-blah", default=False)])
        cmd2   = PSource(name="bcmd", specs=[ParamSpec[bool](name="-aweg", default=False)])
        sub   = PSource(name="asub", specs=[
            ParamSpec[bool](name="-blah", default=False),
            ParamSpec[bool](name="-bloo", default=False),
        ])
        match parser(["aweg", "acmd", "-blah", "asub", "--", "bcmd", "-aweg"],
                     prog=prog,
                     cmds=[cmd1, cmd2],
                     subs=[((cmd1.name,), sub)]):
            case {"remaining":rem, "cmds":{"acmd": [acmdargs], "bcmd": [bcmdargs]}, "subs": dict() as subs}:
                assert(rem == [])
                assert(acmdargs.args['blah'] is True)
                assert(bcmdargs.args['aweg'] is True)
                assert("acmd" in subs)

                assert(parser.current_state_value == "End")
            case x:
                assert(False), x



class TestMachine_Dot:
    """ Write out the dot graphs of the machines """

    @pytest.fixture(scope="function")
    def fsm(self) -> StateMachine:
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
