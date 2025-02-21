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
from collections import ChainMap
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from statemachine import State, StateMachine
from statemachine.exceptions import TransitionNotAllowed
from statemachine.states import States

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import Proto
from jgdv.structs.chainguard import ChainGuard

# ##-- end 1st party imports

from . import errors
from .param_spec import HelpParam, ParamSpec, SeparatorParam
from .parse_machine_base import ParseMachineBase
from ._interface import ParseResult_d, EXTRA_KEY, EMPTY_CMD

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
from dataclasses import InitVar, dataclass, field

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
from ._interface import ParamStruct_p, ArgParser_p, ParamSource_p
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

HELP            : Final[ParamSpec]     = HelpParam()
SEPERATOR       : Final[ParamSpec]     = SeparatorParam()

class ParseMachine(ParseMachineBase):
    """ Implemented Parse State Machine

    __call__ with:
    args       : list[str]       -- the cli args to parse (ie: from sys.argv)
    head_specs : list[ParamSpec] -- specs of the top level program
    cmds       : list[ParamSource_p] -- commands that can provide their parameters
    subcmds    : dict[str, list[ParamSource_p]] -- a mapping from commands -> subcommands that can provide parameters

    A cli call will be of the form:
    {proghead} {prog args} {cmd} {cmd args}* [{subcmd} {subcmdargs} [-- {subcmd} {subcmdargs}]* ]? (--help)?

    eg:
    doot -v list -by-group a b c --help
    doot run basic::task -quick --value=2 --help

    Will raise a jgdv.cli.errors.ParseError on failure
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("parser", CLIParser())
        super().__init__(**kwargs)

    def __call__(self, args:list[str], *, head_specs:list[ParamSpec], cmds:list[ParamSource_p], subcmds:list[tuple[str, ParamSource_p]]) -> Maybe[dict]:
        assert(self.current_state == self.Start)
        try:
            self.setup(args, head_specs, cmds, subcmds)
            if self.current_state not in [self.ReadyToReport, self.Failed, self.End]:
                self.parse()
            self.finish()
        except TransitionNotAllowed as err:
            raise errors.ParseError("Transition failure", err) from err
        else:
            return self.model.report()

@Proto(ArgParser_p)
class CLIParser:
    """

    # {prog} {args} {cmd} {cmd_args}
    # {prog} {args} [{task} {tasks_args}] - implicit do cmd

    """
    _initial_args     : list[str]                              = []
    _remaining_args   : list[str]                              = []
    _head_specs       : list[ParamSpec]                        = []
    _cmd_specs        : dict[str, list[ParamSpec]]             = {}
    _subcmd_specs     : dict[str, tuple[str, list[ParamSpec]]] = {}
    head_result       : Maybe[ParseResult_d]                     = None
    cmd_result        : Maybe[ParseResult_d]                     = None
    subcmd_results    : list[ParseResult_d]                      = []
    extra_results     : ParseResult_d                            = ParseResult_d(EXTRA_KEY)
    _force_help        : bool                                   = False

    def __init__(self):
        self._remaining_args = []

    def _parse_fail_cond(self) -> bool:
        return False

    def _has_no_more_args_cond(self):
        return not bool(self._remaining_args)

    @ParseMachine.finish._transitions.before
    def all_args_consumed_val(self):
        if bool(self._remaining_args):
            raise errors.ArgParseError("Not All Args Were Consumed", self._remaining_args)

    @ParseMachine.Prepare.enter
    def _setup(self, args:list[str], head_specs:list, cmds:list[ParamSource_p], subcmds:list[tuple[str, ParamSource_p]]):
        """
          Parses the list of arguments against available registered parameter head_specs, cmds, and tasks.
        """
        logging.debug("Setting up Parsing : %s", args)
        head_specs                                  = head_specs or []
        cmds                                        = cmds or []
        subcmds                                     = subcmds or []
        self._initial_args                          = args[:]
        self._remaining_args                        = args[:]
        self._head_specs : list[ParamSpec]          = head_specs

        if not isinstance(cmds, list):
            raise TypeError("cmds needs to be a list", cmds)

        for x in cmds:
            match x:
                case (str() as alias, ParamSource_p() as source):
                    self._cmd_specs[alias] = source.param_specs
                case ParamSource_p():
                    self._cmd_specs[x.name] = x.param_specs
                case x:
                    raise TypeError(x)

        match subcmds:
            case [*xs]:
                self._subcmd_specs = {y.name:(x, y.param_specs) for x,y in xs}
            case _:
                logging.info("No Subcmd Specs provided for parsing")
                self._subcmd_specs = {}

        self.head_result       : Maybe[ParseResult_d]                      = None
        self.cmd_result        : Maybe[ParseResult_d]                      = None
        self.subcmd_results    : list[ParseResult_d]                     = []
        self.extra_results     : ParseResult_d                           = ParseResult_d(EXTRA_KEY)
        self._force_help       : bool                                  = False

    @ParseMachine.Cleanup.enter
    def _cleanup(self) -> None:
        logging.debug("Cleaning up")
        self._initial_args      = []
        self._remaining_args    = []
        self._specs             = {}
        self._cmd_specs         = {}
        self._subcmd_specs      = {}

    @ParseMachine.CheckForHelp.enter
    def help_flagged(self):
        logging.debug("Checking for Help Flag")
        match HELP.consume(self._remaining_args[-1:]):
            case None:
                self._force_help = False
            case _:
                self._force_help = True
                self._remaining_args.pop()

    @ParseMachine.Head.enter
    def _parse_head(self):
        """ consume arguments for doot actual """
        logging.debug("Head Parsing: %s", self._remaining_args)
        if not bool(self._head_specs):
            self.head_result = ParseResult_d(name=self._remaining_args.pop(0))
            return
        head_specs       = sorted(self._head_specs, key=ParamSpec.key_func)
        defaults : dict  = ParamSpec.build_defaults(head_specs)
        self.head_result = ParseResult_d("_head_", defaults)
        self._parse_params_unordered(self.head_result, head_specs)

    @ParseMachine.Cmd.enter
    def _parse_cmd(self):
        """ consume arguments for the command being run """
        logging.debug("Cmd Parsing: %s", self._remaining_args)
        if not bool(self._cmd_specs):
            self.cmd_result = ParseResult_d(EMPTY_CMD, {})
            return

        # Determine cmd
        cmd_name = self._remaining_args[0]
        if cmd_name not in self._cmd_specs:
            self.cmd_result = ParseResult_d(EMPTY_CMD, {})
            return

        logging.info("Cmd matches: %s", cmd_name)
        self._remaining_args.pop(0)
        # get its specs
        cmd_specs        = sorted(self._cmd_specs[cmd_name], key=ParamSpec.key_func)
        defaults : dict  = ParamSpec.build_defaults(cmd_specs)
        self.cmd_result  = ParseResult_d(cmd_name, defaults)
        self._parse_params_unordered(self.cmd_result, cmd_specs)

    @ParseMachine.SubCmd.enter
    def _parse_subcmd(self):
        """ consume arguments for tasks """
        if not bool(self._subcmd_specs):
            return
        logging.debug("SubCmd Parsing: %s", self._remaining_args)
        active_cmd = self.cmd_result.name
        last = None
        # Determine subcmd
        while (bool(self._remaining_args)
               and last != (sub_name:=self._remaining_args[0])
               ):
            if self._parse_separator():
                continue
            else:
                self._remaining_args.pop(0)

            logging.debug("Sub Cmd: %s", sub_name)
            last = sub_name
            match self._subcmd_specs.get(sub_name, None):
                case cmd_constraint, params if active_cmd in [cmd_constraint, EMPTY_CMD]:
                    sub_specs        = sorted(params, key=ParamSpec.key_func)
                    defaults : dict  = ParamSpec.build_defaults(sub_specs)
                    sub_result       = ParseResult_d(sub_name, defaults)
                    self._parse_params_unordered(sub_result, sub_specs)
                    self.subcmd_results.append(sub_result)
                case _, _:
                    pass
                case _:
                    raise errors.SubCmdParseError("Unrecognised SubCmd", sub_name)

    @ParseMachine.Extra.enter
    def _parse_extra(self):
        logging.debug("Extra Parsing: %s", self._remaining_args)
        self._remaining_args = []

    def _parse_params(self, res:ParseResult_d, params:list[ParamSpec]) -> None:
        for param in params:
            match param.consume(self._remaining_args):
                case None:
                    logging.debug("Skipping Parameter: %s", param.name)
                case data, count:
                    logging.debug("Consuming Parameter: %s", param.name)
                    self._remaining_args = self._remaining_args[count:]
                    res.args.update(data)
                    res.non_default.add(param.name)

    def _parse_params_unordered(self, res:ParseResult_d, params:list[ParamSpec]):
        logging.debug("Parsing Params Unordered: %s", params)

        def consume_it(x:ParamSpec):
            # TODO refactor this as a partial
            logging.debug("Consume it: %s", x.name)
            match x.consume(self._remaining_args):
                case None:
                    raise errors.ParseError("Failed to consume", x.name)
                case data, count:
                    logging.debug("Consuming Parameter: %s", x.name)
                    self._remaining_args = self._remaining_args[count:]
                    res.args.update(data)
                    res.non_default.add(x.name)

        # Parse non-positional params
        remaining = [x for x in params if not x.positional]
        while bool(remaining) and bool(self._remaining_args):
            match [x for x in remaining if x.matches_head(self._remaining_args[0])]:
                case []:
                    remaining = []
                case [x]:
                    consume_it(x)
                    remaining.remove(x)
                case [*xs]:
                    raise errors.ParseError("Too many potential params", xs)
        else:
            logging.debug("Finished consuming non-positional")

        # Parse positional params
        remaining = [x for x in params if x.positional]
        while bool(remaining) and bool(self._remaining_args):
            match [x for x in remaining if x.matches_head(self._remaining_args[0])]:
                case []:
                    remaining = []
                case [x]:
                    consume_it(x)
                    remaining.remove(x)
                case [*xs]:
                    raise errors.ParseError("Too many potential params", xs)
        else:
            logging.debug("Finished Consuming Positional")

    def _parse_separator(self) -> bool:
        match SEPERATOR.consume(self._remaining_args):
            case None:
                return False
            case _:
                logging.debug("----")
                self._remaining_args.pop(0)
                return True

    def report(self) -> Maybe[dict]:
        """ Take the parsed results and return a nested dict """

        match self._force_help:
            case False:
                cmd_result = self.cmd_result
            case True if self.cmd_result is None:
                self.head_result.args['help'] = True
                cmd_result = ParseResult_d(EMPTY_CMD)
            case True if self.cmd_result.name == EMPTY_CMD:
                cmd_result = ParseResult_d("help", {"target":None, "args": self.cmd_result.args}, self.cmd_result.non_default)
            case True:
                cmd_result = ParseResult_d("help", {"target":self.cmd_result.name, "args": self.cmd_result.args}, self.cmd_result.non_default)

        result = {
            "head"  : self.head_result.to_dict() if self.head_result else {},
            "cmd"   : cmd_result.to_dict() if cmd_result else {},
            "sub"   : {y['name']:y['args'] for x in self.subcmd_results if (y:=x.to_dict()) is not None},
            "extra" : self.extra_results.to_dict(),
        }
        return result
