##-- imports
from __future__ import annotations

# import abc
# import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
# from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
# from uuid import UUID, uuid1
# from weakref import ref

##-- end imports

from statemachine import State, StateMachine
from statemachine.exceptions import TransitionNotAllowed
from statemachine.states import States
from collections import ChainMap
from jgdv import Maybe
from jgdv.structs.chainguard import ChainGuard
from jgdv._abstract.protocols import ParamStruct_p
from .param_spec import ParamSpec, ParseError, HelpParam, LiteralParam, SeparatorParam
from .parse_machine_base import ParseMachineBase, ArgParser_p
from .errors import ParseError

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

EXTRA_KEY       : Final[str]           = "_extra_"
NON_DEFAULT_KEY : Final[str]           = "_non_default_"
DEFAULT_KEY     : Final[str]           = "_default_"
HELP            : Final[ParamSpec]     = HelpParam()
SEPERATOR       : Final[ParamSpec]     = SeparatorParam()

@dataclass
class ParseResult:
    name : str
    args : dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {"name":self.name, "args":self.args}

@runtime_checkable
class ParamSource_p(Protocol):

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def param_specs(self) -> list[ParamStruct_p]:
        raise NotImplementedError()



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
            raise ParseError("Transition failure", err) from err
        else:
            return self.model.report()

class CLIParser(ArgParser_p):
    """
    convert argv to tomlguard by:
    parsing each arg as toml,

    # {prog} {args} {cmd} {cmd_args}
    # {prog} {args} [{task} {tasks_args}] - implicit do cmd

    """
    _initial_args     : list[str]                              = []
    _remaining_args   : list[str]                              = []
    _head_specs       : list[ParamSpec]                        = []
    _cmd_specs        : dict[str, list[ParamSpec]]             = {}
    _subcmd_specs     : dict[str, tuple[str, list[ParamSpec]]] = {}
    head_result       : Maybe[ParseResult]                     = None
    cmd_result        : Maybe[ParseResult]                     = None
    subcmd_results    : list[ParseResult]                      = []
    extra_results     : ParseResult                            = ParseResult(EXTRA_KEY)
    non_default_args  : ParseResult                            = ParseResult(NON_DEFAULT_KEY)
    force_help        : bool                                   = False

    def __init__(self):
        self._remaining_args = []

    def _parse_fail_cond(self) -> bool:
        return False

    def _has_no_more_args_cond(self):
        return not bool(self._remaining_args)

    @ParseMachine.finish._transitions.before
    def all_args_consumed_val(self):
        if bool(self._remaining_args):
            raise ValueError("Not All Args Were Consumed", self._remaining_args)

    @ParseMachine.Prepare.enter
    def _setup(self, args:list[str], head_specs:list, cmds:list, subcmds:list):
        """
          Parses the list of arguments against available registered parameter head_specs, cmds, and tasks.
        """
        logging.debug("Setting up Parsing : %s", args)
        self._initial_args                     = args[:]
        self._remaining_args                   = args[:]
        self._head_specs : list[ParamSpec]          = head_specs
        match cmds:
            case [*xs]:
                self._cmd_specs = {x.name:x.param_specs for x in cmds}
            case _:
                logging.info("No Cmd Specs provided for parsing")
                self._cmd_specs = {}

        match subcmds:
            case [*xs]:
                self._subcmd_specs = {y.name:(x, y.param_specs) for x,y in xs}
            case _:
                logging.info("No Subcmd Specs provided for parsing")
                self._subcmd_specs = {}

        self.head_result       : Maybe[ParseResult]                      = None
        self.cmd_result        : Maybe[ParseResult]                      = None
        self.subcmd_results    : list[ParseResult]                     = []
        self.extra_results     : ParseResult                           = ParseResult(EXTRA_KEY)
        self.non_default_args  : ParseResult                           = ParseResult(NON_DEFAULT_KEY)
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

    @ParseMachine.Head.enter
    def _parse_head(self):
        """ consume arguments for doot actual """
        logging.debug("Head Parsing: %s", self._remaining_args)
        if not bool(self._head_specs):
            self.head_result = ParseResult(name=self._remaining_args.pop(0))
            return
        head_specs       = sorted(self._head_specs, key=ParamSpec.key_func)
        defaults : dict  = ParamSpec.build_defaults(head_specs)
        self.head_result = ParseResult("_head_", defaults)
        self._parse_params(self.head_result, head_specs)

    @ParseMachine.Cmd.enter
    def _parse_cmd(self):
        """ consume arguments for the command being run """
        logging.debug("Cmd Parsing: %s", self._remaining_args)
        if not bool(self._cmd_specs):
            self.cmd_result = ParseResult("_cmd_", {})
            return

        # Determine cmd
        cmd_name = self._remaining_args[0]
        logging.info("Cmd matches: %s", cmd_name)
        if cmd_name not in self._cmd_specs:
            raise KeyError("Unrecognised command name", cmd_name)
        else:
            self._remaining_args.pop(0)
        # get its specs
        cmd_specs        = sorted(self._cmd_specs[cmd_name], key=ParamSpec.key_func)
        defaults : dict  = ParamSpec.build_defaults(cmd_specs)
        self.cmd_result  = ParseResult(cmd_name, defaults)
        self._parse_params(self.cmd_result, cmd_specs)

    @ParseMachine.SubCmd.enter
    def _parse_subcmd(self):
        """ consume arguments for tasks """
        if not bool(self._subcmd_specs):
            return
        logging.debug("SubCmd Parsing: %s", self._remaining_args)
        cmd_name = self.cmd_result.name
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
                case cmd_constraint, params if cmd_constraint == cmd_name:
                    sub_specs        = sorted(params, key=ParamSpec.key_func)
                    defaults : dict  = ParamSpec.build_defaults(sub_specs)
                    sub_result       = ParseResult(sub_name, defaults)
                    self._parse_params(sub_result, sub_specs)
                    self.subcmd_results.append(sub_result)
                case _, _:
                    pass
                case _:
                    raise ValueError("Unrecognised SubCmd", sub_name)

    @ParseMachine.Extra.enter
    def _parse_extra(self):
        logging.debug("Extra Parsing: %s", self._remaining_args)
        self._remaining_args = []

    def _parse_params(self, res:ParseResult, params:list[ParamSpec]):
        for param in params:
            match param.consume(self._remaining_args):
                case None:
                    logging.debug("Skipping Parameter: %s", param.name)
                case data, count:
                    logging.debug("Consuming Parameter: %s", param.name)
                    self._remaining_args = self._remaining_args[count:]
                    res.args.update(data)
                    self.non_default_args.args.update(data)
        
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
        result = {
            "head"  : self.head_result.to_dict() if self.head_result else {},
            "cmd"   : self.cmd_result.to_dict() if self.cmd_result else {},
            "sub"   : {y['name']:y['args'] for x in self.subcmd_results if (y:=x.to_dict()) is not None},
            "extra" : self.extra_results.to_dict(),
        }
        return result
