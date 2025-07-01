#!/usr/bin/env python3
"""
Provdes the Main ArgParser_p Protocol,
and the ParseMachineBase StateMachine.

ParseMachineBase descibes the state progression to parse arguments,
while jgdv.cli.arg_parser.CLIParser adds the specific logic to states and transitions
"""
# ruff: noqa:
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from collections import ChainMap
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from statemachine import State, StateMachine
from statemachine.states import States
from statemachine.exceptions import TransitionNotAllowed

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from . import _interface as API # noqa: N812
from . import errors

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from ._interface import ParamSource_p, ArgParserModel_p
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
# isort: on
# ##-- end types

logging = logmod.getLogger(__name__)
##--|
class ParseMachine(StateMachine):
    """
    Implemented Parse State Machine

    __call__ with:
    args       : list[str]       -- the cli args to parse (ie: from sys.argv)
    prog : list[ParamSpec_i] -- specs of the top level program
    cmds       : list[ParamSource_p] -- commands that can provide their parameters
    subs    : dict[str, list[ParamSource_p]] -- a mapping from commands -> subcommands that can provide parameters

    A cli call will be of the form:
    {proghead} {prog [kw]args} {cmd} {cmd[kw]args}* [{subs} {subs[kw]args} [-- {subs} {subargs}]* ]? (--help)?

    eg:
    doot -v list -by-group a b c --help
    doot run basic::task -quick --value=2 --help

    Will raise a jgdv.cli.errors.ParseError on failure
    """

    ## States
    # startup states
    Start         = State(initial=True)
    Prepare       = State(enter="prepare_for_parse")
    # Parsing states
    Help         = State(enter="set_force_help")
    Head         = State()
    Section      = State(enter="initialise_section")
    Prog         = State(enter="select_prog_spec")
    Cmd          = State(enter="select_cmd_spec")
    Sub          = State(enter="select_sub_spec")
    Kwargs       = State(enter="parse_kwarg")
    Posargs      = State(enter="parse_posarg")
    Section_end  = State(enter="clear_section")
    # teardown states
    Cleanup      = State(enter="cleanup")
    Report   = State(enter="report")
    End      = State(final=True)

    # Event Transitions
    setup    = (
        Start.to(End, cond="not _has_more_args")
        | Start.to(Prepare)
        | Prepare.to(Help, cond="_has_help_flag_at_tail")
        | Head.from_(Prepare, Help)
    )

    parse = (
        # program / cmd / subs
         Head.to(Prog,   cond="_prog_at_front")
        | Head.to(Cmd,   cond="_cmd_at_front")
        | Head.to(Sub,   cond="_sub_at_front")
        | Section.from_(Prog, Cmd, Sub)
        # args
        | Kwargs.from_(Section, Kwargs, cond="_kwarg_at_front")
        | Posargs.from_(Section, Kwargs, Posargs, cond="_posarg_at_front")
        # separator

        # loop
        | Section_end.from_(Section, Kwargs, Posargs)
        | Section_end.to(Report, cond="not _has_more_args")
        | Head.from_(Section_end)
    )

    finish  = (
        Report.to(Cleanup)
        | Cleanup.to(End)
    )

    ##--| composite
    progress = (setup | parse | finish)

    def __init__(self, parser:Maybe[ArgParserModel_p]=None) -> None:
        match parser:
            case API.ArgParserModel_p():
                pass
            case x:
                raise TypeError(type(x))
        super().__init__(parser)
        self.count = 0
        self.max_attempts = 20

    def __call__(self, args:list[str], *, prog:list[API.ParamSpec_i], cmds:list[ParamSource_p], subs:list[tuple[str, ParamSource_p]]) -> Maybe[dict]:
        assert(self.current_state == self.Start) # type: ignore[has-type]
        try:
            self.setup(args, prog, cmds, subs)
            if self.current_state not in [self.Report, self.End]: # type: ignore[has-type]
                self.parse()
                self.finish()
        except TransitionNotAllowed as err:
            msg = "Transition failure"
            raise errors.ParseError(msg, err) from err
        else:
            result = self.model.report()
            # Reset the state
            self.current_state = self.Start
            return result

    def on_exit_state(self) -> None:
        self.count += 1
        if self.max_attempts < self.count:
            raise StopIteration
