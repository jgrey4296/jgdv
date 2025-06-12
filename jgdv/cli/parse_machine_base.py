#!/usr/bin/env python3
"""
Provdes the Main ArgParser_p Protocol,
and the ParseMachineBase StateMachine.

ParseMachineBase descibes the state progression to parse arguments,
while jgdv.cli.arg_parser.CLIParser adds the specific logic to states and transitions
"""
# ruff: noqa: F401
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

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from .param_spec import ParamSpec

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
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
from ._interface import ParamStruct_p, ParamSource_p, ArgParser_p
# isort: on
# ##-- end types

 #-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class ParseMachineBase(StateMachine):
    """ Base Implementaiton of an FSM for running a CLI arg parse.
    Subclass and init with a default ArgParser_p that has bound callback for events
    """

    # States
    Start         = State(initial=True)
    Prepare       = State()
    Head          = State()
    CheckForHelp  = State()
    Cmd           = State()
    SubCmd        = State()
    Extra         = State()
    Cleanup       = State()
    ReadyToReport = State()
    Failed        = State()
    End           = State(final=True)

    # Event Transitions
    setup = (Prepare.to(Failed,            cond="_parse_fail_cond")
             | Prepare.to(ReadyToReport,   cond="_has_no_more_args_cond")
             | Start.to(Prepare,           after="setup")
             | Prepare.to(CheckForHelp,    after="setup")
             | CheckForHelp.to(Head)
             )

    parse = (Failed.from_(Start, Prepare, CheckForHelp, Head, Cmd, SubCmd, cond="_parse_fail_cond")
             | ReadyToReport.from_(Head, Cmd, SubCmd, Extra, cond="_has_no_more_args_cond")
             | Head.to(Cmd,      after="parse")
             | Cmd.to(SubCmd,    after="parse")
             | SubCmd.to(Extra,  after="parse")
             | Extra.to(Failed)
             )

    finish  = (End.from_(Cleanup)
               | ReadyToReport.to(Cleanup, after="finish")
               | Failed.to(Cleanup, after="finish")
               )

    def __init__(self, *, parser:Maybe[ArgParser_p]=None):
        assert(parser is not None)
        super().__init__(parser)
        self.count = 0
        self.max_attempts = 20

    def on_exit_state(self):
        self.count += 1
        if self.max_attempts < self.count:
            raise StopIteration

    def __call__(self, args:list[str], *, head_specs:list[ParamSpec], cmds:list[ParamSource_p], subcmds:list[tuple[str, ParamSource_p]]) -> Maybe[dict]:
        raise NotImplementedError()
