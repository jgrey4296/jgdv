#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

from dataclasses import replace
import logging as logmod
import warnings
import pathlib
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
##-- end imports

import pytest
from clingo import Control, parse_term, Function, Number
from instal.solve.clingo_solver import ClingoSolver
import instal.interfaces.solver as iSolve

logging = logmod.root

class TestInstalClingoSolver:

    def test_initial(self):
        solver = ClingoSolver()
        self.assert(isinstance(solver, ClingoSolver)

    def test_solver_initialisation(self):
        solver = ClingoSolver()
        assert(solver.ctl is not None)

    def test_solver_with_init_options(self):
        solver = ClingoSolver(options=['-n', 2, '-c', "horizon=2"])
        assert(isinstance(solver, ClingoSolver))

    def test_basic_model(self):
        solver = ClingoSolver("a. b. c. d. e :- a, b, c.")
        result = solver.solve()
        assert(result == 1)

    def test_basic_model_result(self):
        solver = ClingoSolver("a. b. c. d. e :- a, b, c.")
        count = solver.solve()
        assert(count == 1)
        model = solver.results[0]
        assert(isinstance(model,iSolve.InstalModelResult)
        assert(all([str(x) in {"a","b","c","d","e"} for x in model.atoms]))

    def test_basic_fail(self):
        # Leaving off the final `.`
        with pytest.raises(RuntimeError):
            solver = ClingoSolver("a. b. c. d. e :- a, b, c")

    def test_assertion_assignment(self):
        term   = parse_term("testVal")
        term_2 = parse_term("a")
        solver = ClingoSolver("#external testVal. a.")
        count  = solver.solve(["testVal"])
        assert(count == 1)

        assert(term in solver.results[0].atoms)
        assert(term_2 in solver.results[0].atoms)

    def test_assertion_assignment_false(self):
        term   = parse_term("testVal")
        term_2 = parse_term("a")
        solver = ClingoSolver("#external testVal. a.")
        count  = solver.solve()
        assert(count == 1)

        assert(term not in solver.results[0].atoms)
        assert(term_2 in solver.results[0].atoms)

    def test_force_fresh(self):
        term   = parse_term("testVal")
        term_2 = parse_term("a")
        solver = ClingoSolver("#external testVal. a.")
        count  = solver.solve(["testVal"])

        assert(count == 1)
        assert(term in solver.results[0].atoms)
        assert(term_2 in solver.results[0].atoms)
        count2 = solver.solve(fresh=True)
        assert(count == 1)
        assert(len(solver.results) == 1)
        assert(term not in solver.results[0].atoms)
        assert(term_2 in solver.results[0].atoms)


    def test_maintenance_no_change(self):
        term   = parse_term("testVal")
        term_2 = parse_term("a")
        solver = ClingoSolver("#external testVal. a.")
        count  = solver.solve([ term ])

        assert(count == 1)
        assert(term in solver.results[0].atoms)
        assert(term_2 in solver.results[0].atoms)

        count2 = solver.solve()
        assert(len(solver.results) == 2)
        assert(count == 1)
        assert(term in solver.results[-1].atoms)
        assert(term_2 in solver.results[-1].atoms)


    def test_maintenance_with_change(self):
        term         = parse_term("testVal(1)")
        term_2       = parse_term("testVal(2)")
        a_term       = parse_term("a")
        solver = ClingoSolver("#external testVal(1..3). a.")
        count  = solver.solve([term])

        assert(count == 1)
        assert(term in solver.results[0].atoms)
        assert(a_term in solver.results[0].atoms)

        # change the value of the term:
        count2 = solver.solve([term_2, term])
        assert(count == 1)
        assert(str(term) not in solver.results[-1].atoms)
        assert(term_2 in solver.results[-1].atoms)
        assert(a_term in solver.results[-1].atoms)


    def test_maintenance_incremental(self):
        solver = ClingoSolver("""
        #program base.
        on(X, 0) :- init_on(X).
        init_on(a).
        disc(a;b;c).

        #program step(t).
        1 { move(D,t) : disc(D) } 1.

        on(X, t) :- move(X,t).
        """)
        count  = solver.solve()
        assert(count == 1)

        # change the value of the term:
        solver.solve(reground=[("step", [Number(1)])])
        solver.solve(reground=[("step", [Number(5)])])
        solver.solve(reground=[("step", [Number(10)])])
        assert(True)

    def test_all_models(self):
    	# Setup:

        # Pre-check:

        # Action

        # Post-check:

        assert(True)

    @pytest.mark.skip(reason="TODO")
    def test_file_load(self):
        solver = ClingoSolver([])

    @pytest.mark.skip(reason="TODO")
    def test_metadata(self):
        pass
