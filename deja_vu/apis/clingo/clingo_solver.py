
##-- imports
from __future__ import annotations

import warnings
import logging as logmod
import os
from itertools import cycle, chain
import time
from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from functools import partial
from pathlib import Path
from typing import IO, List

##-- end imports

##-- logging
logging       = logmod.getLogger(__name__)
clingo_logger = logmod.getLogger(__name__ + ".ffi.clingo")
##-- end logging

import clingo
from clingo import Control, Function, Number, Symbol, parse_term
from dejavu._interfaces.solver import SolverWrapper_i
from dejavu.apis.clingo.ast import SolverAST
from dejavu.apis.clingo.solver import SolverModelResult, SolverWrapper_i

def clingo_intercept_logger(code, msg):
    """
    Intercepts messages from clingo, and controls
    the logging of them
    """
    msg = msg.replace("\n", "")
    match code:
        case clingo.MessageCode.AtomUndefined:
            clingo_logger.debug(msg)
        case clingo.MessageCode.RuntimeError:
            clingo_logger.exception(msg)
        case _:
            clingo_logger.info(msg)

def model_cb(self, model:clingo.Model):
    """
    Partial callback for clingo.
    Used for storing models.
    *Must* be constructed using functools.partial
    with 'self' bound to the SolverWrapper

    NOTE: Clingo Models are destroyed/reallocated on exit of the callback,
    Which is why we don't just store the model itself
    """
    self.results.append(SolverModelResult(model.symbols(atoms=True),
                                          model.symbols(shown=True),
                                          model.cost,
                                          model.number,
                                          model.optimality_proven,
                                          model.type))

@dataclass
class ClingoSolver(SolverWrapper_i):
    """
    An Oracle that uses Clingo as the solver
    """

    options      : list[str]    = field(kw_only=True, default_factory=list)
    ctl          : None|Control = field(init=False, default=None)
    program_name : str          = field(kw_only=True, default="base")

    def __post_init__(self):
        if not self.program and bool(self.input_files):
            warnings.warn("ClingoSolver created with no initial program or input files")

        self.options = self.options or ['-n', 1,
                                        '-c', f'horizon={2}']

        self.init_solver()

    def __repr__(self):
        return "[Clingo Solver: {}; Opts: {}; Models: {}]".format(self.ctl is not None,
                                                                  " ".join(self.options),
                                                                  len(self.results))
    def init_solver(self):
        self.results      = []
        default_grounding = [(self.program_name, [])]
        self.ctl          = Control([str(x) for x in self.options], logger=clingo_intercept_logger)

        for path in self.input_files:
            logging.debug("Clingo Loading: %s", path)
            assert(path.exists())
            self.ctl.load(str(path))

        try:
            if self.program:
                self.ctl.add(self.program_name, [], self.program)

        except Exception as err:
            logging.exception("Clingo Failed to add Program")
            logging.debug(self.program)
            raise err

        logging.debug("Initial Grounding of Program: %s", default_grounding)
        self.ctl.ground(default_grounding)
        logging.info("Clingo initialization complete")

    def solve(self, assignments:list[str|SolverAST|Symbol|tuple[bool, Symbol]]=None, fresh:bool=False, reground:list[tuple]=None) -> int:
        assignments = assignments or []

        if fresh or self.ctl is None:
            self.init_solver()

        if bool(reground):
            logging.debug("Grounding Program: %s", reground)
            self.ctl.cleanup()
            self.ctl.ground(reground)

        for sym in assignments:
            logging.debug("assigning: %s", sym)
            match sym:
                case SolverAST():
                    for truthy, sym in self.ast_to_clingo(sym):
                        self.ctl.assign_external(sym, truthy)
                case Symbol():
                    self.ctl.assign_external(sym, True)
                case bool(), Symbol():
                    self.ctl.assign_external(sym[1], sym[0])
                case str():
                    self.ctl.assign_external(parse_term(sym), True)
                case _:
                    raise Exception("Unrecognized situation fact")

        try:
            on_model_cb = partial(model_cb, self)
            logging.info("Running Program")
            self.ctl.solve(on_model=on_model_cb)
        except Exception as err:
            logging.warning("Clingo ran into a problem: %s", err)
            self.ctl = None

        logging.info("There are %s answer sets", len(self.results))
        return len(self.results)


    @property
    def metadata(self):
        return {
            "pid"            : os.getpid(),
            "source_files"   : [str(x) for x in self.input_files],
            "timestamp"      : self.timestamp,
            "mode"           : "multi_shot",
            "current_result" : self.current_answer,
            "result_size"    : len(self.results),
            "clingo_version" : clingo.__version__
        }


    def ast_to_clingo(self, *asts:TermAST) -> list[tuple[bool, Symbol]]:
        """
        Convert terms to clingo terms,
        not caring if they are #external or not
        """
        raise NotImplementedError()
