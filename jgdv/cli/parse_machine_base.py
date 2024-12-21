#!/usr/bin/env python3
"""

"""

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
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from statemachine import State, StateMachine
from statemachine.states import States

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv._abstract.protocols import ParamStruct_p
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from .param_spec import (
    HelpParam,
    LiteralParam,
    ParamSpec,
    SeparatorParam,
)

 #-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@runtime_checkable
class ArgParser_p(Protocol):
    """
    A Single standard process point for turning the list of passed in args,
    into a dict, into a tomlguard,
    along the way it determines the cmds and tasks that have been chosne
    """

    def _parse_fail_cond(self) -> bool:
        raise NotImplementedError()

    def _has_no_more_args_cond(self) -> bool:
        raise NotImplementedError()

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

    def __init__(self, *, parser:ArgParser_p=None):
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
