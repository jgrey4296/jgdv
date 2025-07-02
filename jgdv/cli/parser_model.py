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
from collections import ChainMap, defaultdict
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
from .param_spec import HelpParam, SeparatorParam, ParamSpec
from . import _interface as API # noqa: N812
from ._interface import ParseResult_d, EXTRA_KEY, EMPTY_CMD, SectionType_e
from ._interface import ParamSpec_p, ParamSpec_i, ArgParserModel_p, ParamSource_p

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
    from .param_spec.param_spec import ParamProcessor
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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

HELP            : Final[ParamSpec_i]     = HelpParam()
SEPARATOR       : Final[ParamSpec_i]     = SeparatorParam()


##--|

@Proto(ArgParserModel_p)
class CLIParserModel:
    """

    # {prog} {args} {cmd} {cmd_args}
    # {prog} {args} [{task} {tasks_args}] - implicit do cmd

    """
    SectionTypes  : ClassVar[type[SectionType_e]]  = SectionType_e
    type CmdName                                   = str
    type SubName                                   = str
    type SubConstraint                             = tuple[str,...]
    type Sub_Params                                = tuple[SubConstraint, list[ParamSpec_i]]

    args_initial       : tuple[str, ...]
    args_remaining     : list[str]
    data_cmds          : list[ParseResult_d]
    data_prog          : Maybe[ParseResult_d]
    data_subs          : list[ParseResult_d]
    specs_cmds         : dict[CmdName, list[ParamSpec_i]]
    specs_prog_prefix  : list[str]
    specs_prog         : list[API.ParamSpec_i]
    specs_subs         : dict[SubName, list[ParamSpec_i]]

    implicits          : list[str]
    _subs_constraints  : defaultdict[CmdName, set[SubName]]
    _current_section   : Maybe[tuple[str, list[API.ParamSpec_i]]]
    _current_data      : Maybe[ParseResult_d]
    _separator         : ParamSpec_i
    _help              : ParamSpec_i
    _force_help        : bool
    _report            : Maybe[dict]
    _section_type      : Maybe[SectionType_e]
    _processor         : ParamProcessor

    def __init__(self) -> None:
        self._processor         = ParamSpec._processor
        self._separator         = SEPARATOR
        self._help              = HELP
        self._report            = None
        self._current_section   = None
        self._subs_constraints  = defaultdict(set)
        self._force_help        = False
        self._section_type      = None
        self.args_initial       = ()
        self.args_remaining     = []
        self.args_remaining     = []
        self.data_cmds          = []
        self.data_prog          = None
        self.data_subs          = []
        self.specs_prog_prefix  = ["python"]
        self.specs_prog         = []
        self.specs_cmds         = {}
        self.specs_subs         = {}

    ##--| conditions

    def _has_more_args(self) -> bool:
        return bool(self.args_remaining)
    def _has_no_specs(self) -> bool:
        return not (bool(self.specs_prog)
                    or bool(self.specs_cmds)
                    or bool(self.specs_subs))

    def _has_help_flag_at_tail(self) -> bool:
        return self._processor.matches_head(self._help,
                                            self.args_remaining[-1])

    def _prog_at_front(self) -> bool:
        match self.args_remaining:
            case [head, *_] if head in self.specs_prog_prefix:
                self.args_remaining.pop(0)
                return True
            case _:
                return False

    def _cmd_at_front(self) -> bool:
        match self.args_remaining:
            case [x, *_] if x in self.specs_cmds:
                return True
            case _:
                return False

    def _no_cmd(self) -> bool:
        return not bool(self.data_cmds) and bool(self.implicits)

    def _sub_at_front(self) -> bool:
        match self.args_remaining:
            case [x, *_] if x in self.specs_subs:
                return True
            case _:
                return False

    def _kwarg_at_front(self) -> bool:
        """ See if theres a kwarg to parse """
        params : list
        if not bool(self.args_remaining):
            return False
        match self._current_section:
            case None:
                return False
            case _, [*params]:
                pass

        head = self.args_remaining[0]
        for param in params:
            match param:
                case API.PositionalParam_p():
                    continue
                case _:
                    if self._processor.matches_head(param, head):
                        return True
        else:
            return False

    def _posarg_at_front(self) -> bool:
        params : list
        if not bool(self.args_remaining):
            return False
        match self._current_section:
            case None:
                return False
            case _, [*params]:
                pass

        head = self.args_remaining[0]
        for param in params:
            match param:
                case API.PositionalParam_p():
                    if self._processor.matches_head(param, head): # type: ignore[arg-type]
                        return True
                case _:
                    continue
        else:
            return False

    def _separator_at_front(self) -> bool:
        if not bool(self.args_remaining):
            return False
        return self._processor.matches_head(self._separator,
                                            self.args_remaining[0])

    ##--| transition actions
    def _set_implicit_cmd(self) -> None:
        match [x for x in self.implicits if x in self.specs_cmds]:
            case [x]:
                self._section_type = SectionType_e.cmd
                self._current_section = (x, sorted(self.specs_cmds[x], key=ParamSpec.key_func))
                self.initialise_section()
                self.clear_section()
            case []:
                pass
            case x:
                msg = "Too Many possibly implicit commands"
                raise ValueError(msg, x)

    ##--| state actions

    def prepare_for_parse(self, *, prog:ParamSource_p, cmds:list, subs:list, raw_args:list[str], implicits:Maybe[list[str]]=None) -> None:
        logging.debug("Setting up Parsing : %s", raw_args)
        self.args_initial    = tuple(raw_args[:])
        self.args_remaining  = raw_args[:]
        self.implicits       = implicits or []
        self._prep_prog_lookup(prog)
        self._prep_cmd_lookup(cmds)
        self._prep_sub_lookup(subs)

    def set_force_help(self) -> None:
        match self._help.consume(self.args_remaining[-1:]):
            case dict(), 1:
                self._force_help = True
                self.args_remaining.pop()
            case _:
                pass

    def select_prog_spec(self) -> None:
        logging.debug("Setting Prog Spec")
        self._current_section = ("prog", sorted(self.specs_prog, key=ParamSpec.key_func))
        self._section_type = SectionType_e.prog

    def select_cmd_spec(self) -> None:
        head = self.args_remaining.pop(0)
        logging.debug("Setting Cmd Spec: %s", head)
        match self.specs_cmds.get(head, None):
            case None:
                raise ValueError()
            case [*params]:
                self._current_section = (head, sorted(params, key=ParamSpec.key_func))
                self._section_type = SectionType_e.cmd

    def select_sub_spec(self) -> None:
        last_cmd     = self.data_cmds[-1].name
        constraints  = self._subs_constraints[last_cmd]
        head         = self.args_remaining.pop(0)
        logging.debug("Setting Sub Spec: %s", head)
        if head not in constraints:
            msg = "Sub Not Available for cmd"
            raise ValueError(msg, last_cmd, head)

        self._current_section = (head, sorted(self.specs_subs[head], key=ParamSpec.key_func))
        self._section_type = SectionType_e.sub

    def initialise_section(self) -> None:
        name      : str
        defaults  : dict
        ##--|
        match self._current_section:
            case str() as name, list() as params:
                logging.debug("Initialising: %s", name)
                defaults = ParamSpec.build_defaults(params)
            case None:
                raise ValueError()
        match self._section_type:
            case SectionType_e.sub:
                last_cmd            = self.data_cmds[-1].name
                self._current_data  = ParseResult_d(name=name, ref=last_cmd, args=defaults)
            case _:
                self._current_data  = ParseResult_d(name=name, args=defaults)

    def parse_kwarg(self) -> None:
        """ try each param until one works """
        logging.debug("Parsing Kwarg")
        params : list[API.ParamSpec_i]
        assert(self._current_data is not None)
        match self._current_section:
            case str(), list() as params:
                pass
            case x:
                raise TypeError(type(x))

        while bool(params):
            if isinstance(params[0], API.PositionalParam_p):
                return
            param = params.pop(0)
            match param.consume(self.args_remaining):
                case None:
                    continue
                case dict() as data, int() as count:
                    self._current_data.args.update(data)
                    self._current_data.non_default.update(data.keys())
                    self.args_remaining = self.args_remaining[count:]
                    return

    def parse_posarg(self) -> None:
        logging.debug("Parsing Posarg")
        params : list[API.ParamSpec_i]
        assert(self._current_data is not None)
        match self._current_section:
            case _, list() as params:
                pass
            case x:
                raise TypeError(type(x))

        while bool(params):
            param = params.pop(0)
            if not isinstance(param, API.PositionalParam_p):
                continue
            match param.consume(self.args_remaining):
                case None:
                    continue
                case dict() as data, int() as count:
                    self._current_data.args.update(data)
                    self._current_data.non_default.update(data.keys())
                    self.args_remaining = self.args_remaining[count:]
                    return

    def parse_separator(self) -> None:
        match self._separator.consume(self.args_remaining):
            case None:
                pass
            case {}, 1:
                self.args_remaining = self.args_remaining[1:]

    def clear_section(self) -> None:
        assert(self._current_data)
        self._current_section = None
        match self._section_type:
            case None:
                raise ValueError()
            case SectionType_e.prog:
                self.data_prog = self._current_data
            case SectionType_e.cmd:
                self.data_cmds.append(self._current_data)
            case SectionType_e.sub:
                self.data_subs.append(self._current_data)
        ##--|
        self._current_data = None

    def cleanup(self) -> None:
        logging.debug("Cleaning up")
        self.args_initial    = ()
        self.args_remaining  = []
        self.specs_cmds      = {}
        self.specs_subs      = {}
    ##--| Report Generation

    def report(self) -> Maybe[dict]:
        """ Take the parsed results and return a nested dict """
        result : dict
        ##--|
        result = {
            "raw" : self.args_initial,
            "remaining" : self.args_remaining,
            "cmds" : defaultdict(list),
            "subs" : defaultdict(list),
            "help" : self._force_help,
        }


        match self.data_prog:
            case None:
                pass
            case API.ParseResult_d() as pr:
                result['prog'] = pr

        for cmd in self.data_cmds:
            result['cmds'][cmd.name].append(cmd)

        for sub in self.data_subs:
            assert(sub.ref is not None and sub.ref in result['cmds'])
            result['subs'][sub.ref].append(sub)

        self._report = result
        return result

    ##--| util
    def _prep_prog_lookup(self, prog:ParamSource_p) -> None:
        match prog:
            case ParamSource_p():
                # TODO make it so variable amount of prefix can be consumed
                self.specs_prog_prefix  = [prog.name]
                self.specs_prog         = prog.param_specs()
            case None:
                pass
            case x:
                msg = "Prog needs to be a ParamSource_p"
                raise TypeError(msg, x)

    def _prep_cmd_lookup(self, cmds:list[ParamSource_p]) -> None:
        """ get the param specs for each cmd """
        if not isinstance(cmds, list):
            msg = "cmds needs to be a list"
            raise TypeError(msg, cmds)

        for x in cmds:
            match x:
                case (str() as alias, ParamSource_p() as source):
                    self.specs_cmds[alias] = source.param_specs()
                    self.specs_cmds[source.name] = source.param_specs()
                case ParamSource_p() as source:
                    self.specs_cmds[source.name] = source.param_specs()
                case x:
                    raise TypeError(x)

    def _prep_sub_lookup(self, subs:list[ParamSource_p]) -> None:
        """ for each sub cmd, get it's param specs, but also register the parent cmd constraint """
        if not isinstance(subs, list):
            logging.info("No Subcmd Specs provided for parsing")
            return

        for x in subs:
            match x:
                case [*constraints], ParamSource_p() as source:
                    assert(all(isinstance(c, str) for c in constraints))
                    self.specs_subs[source.name] = source.param_specs()
                    for c in constraints:
                        self._subs_constraints[c].add(source.name)
                case x:
                    raise TypeError(type(x))
