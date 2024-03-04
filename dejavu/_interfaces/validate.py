#/usr/bin/env python3
"""
The Interface for running compile time sanity validates on an instal model
"""
##-- imports
from __future__ import annotations

import warnings
import abc
import logging as logmod
from collections import defaultdict
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from re import Pattern
from typing import (Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload)
from uuid import UUID, uuid1
from weakref import ref

from instal.interfaces.ast import InstalAST
from instal.interfaces.util import InstalASTVisitor_i

from instal.util.generated_visitor import InstalGeneratedASTVisitor
##-- end imports


logging = logmod.getLogger(__name__)

@dataclass
class InstalValidationReport:
    """
    A Result of an InstalValidate.

    """
    ast       : InstalAST         = field()
    msg       : str               = field()
    level     : int               = field(kw_only=True)
    validator : InstalValidator_i = field(kw_only=True)
    data      : Any               = field(kw_only=True, default=None)

    fmt       : None|str          = field(kw_only=True, default="({level}) {source}{loc} {msg}")

    def __repr__(self):
        return str(self) + f" AST: {self.ast}"

    def __str__(self):
        loc    = ""
        source = ""
        if self.ast and bool(self.ast.parse_source):
            source = f"Source: {self.ast.sources_str} : "

        if self.ast and self.ast.parse_loc is not None:
            loc = f"L:{self.ast.parse_loc[0]}, C:{self.ast.parse_loc[1]}: "

        return self.fmt.format_map({"msg"    : self.msg,
                                    "level"  : logmod.getLevelName(self.level),
                                    "source" : source,
                                    "loc"    : loc})

@dataclass
class InstalValidator_i(metaclass=abc.ABCMeta):
    """
    The Core Interface for running compile time validates
    on an instal specification.

    parsers return list[InstalAST],

    the validation runner triggers an AST walk, which a validator will
    have registered actions on with `get_actions`

    then `validate` is called, and any data the validator's actions have stored
    will be used to generate reports

    NOTE: validators use an internal trio of debug/info/warning methods
    instead of just logging, or raising an error,
    so that *all* validates can be run, instead of throwing up to the runner on the first error.

    validator runners call `full_clear` at the start of a validation pass.
    which re-call's any validator's fields default_factories.

    """

    current_reports : list[InstalValidationReport] = field(init=False, default_factory=list)

    def clear(self):
        """
        an empty method for more involved reinitialization
        """
        pass

    def full_clear(self):
        """
        The full clear triggered by the validate runner
        """
        self.current_reports = []
        for field in self.__dataclass_fields__.values():
            if field.default_factory is None:
                continue

            setattr(self, field.name, field.default_factory())

        self.clear()

    def debug(self, msg, ast=None, data=None):
        self.build_note(ast, msg, logmod.DEBUG, data)

    def delay_info(self, msg, ast=None, data=None):
        self.build_note(ast, msg, logmod.INFO, data)

    def delay_warning(self, msg, ast=None, data=None):
        self.build_note(ast, msg, logmod.WARN, data)

    def delay_error(self, msg, ast=None, data=None):
        self.build_note(ast, msg, logmod.ERROR, data)

    def build_note(self, ast, msg, level, data):
        self.current_reports.append(InstalValidationReport(ast, msg,
                                                           level=level,
                                                           validator=self.__class__,
                                                           data=data))


    def __call__(self) -> list[InstalValidationReport]:
        """
        The access point used by InstalValidateRunner.
        Clears the log of reports generated, runs the .validate method,
        and returns the new list of reports.
        """
        self.validate()
        return self.current_reports[:]

    def validate(self): pass



@dataclass
class InstalValidatorRunner:
    """
    Given a collection of Instal Validators,
    and a list of InstalAST's,
    runs the validators on the ast's
    and warns / errors / reports a collection of results
    """

    validators : list[InstalValidator_i] = field(default_factory=list)
    visitor    : InstalASTVisitor_i      = field(default_factory=InstalGeneratedASTVisitor)

    def __post_init__(self):
        # Register all validators' actions with the visitor
        for validator in self.validators:
            self.visitor.add_actions(validator)

        self.visitor.flatten_for_classes()

        logging.info("%s built with %s validators and visitor class %s",
                     self.__class__.__name__,
                     len(self.validators),
                     self.visitor.__class__.__name__)

    def validate(self, asts:list[InstalAST]) -> dict[int, list[InstalValidationReport]]:
        if not isinstance(asts, list):
            asts = [asts]
        logging.info("Running Validate on %s primary level asts", len(asts))
        total_results                = defaultdict(lambda: [])
        hard_fails : list[Exception] = []
        error_count : int            = 0

        for validator in self.validators:
            validator.clear()


        logging.debug("Visiting nodes")
        self.visitor.visit_all(asts)


        for validator in self.validators:
            logging.debug("Running Validator: %s", validator.__class__.__name__)
            # Run the Validate, recording results
            try:
                results = validator()
                # Collect the reports by level
                for note in results:
                    total_results[note.level].append(note)
                    error_count += 1 if note.level >= logmod.ERROR else 0

            except Exception as err:
                # If a validator actually *errors*, record that but keep going
                logging.exception("Validator Hard Failed: %s", validator)
                hard_fails.append(err)
                error_count += 1

        # When all validates are done, report exceptions
        if bool(error_count):
            just_errors = {x:y for x,y in total_results.items() if x >= logmod.ERROR}
            just_errors.update({101:hard_fails})
            raise Exception(f"Validating produced Errors: {error_count}", just_errors)

        # warning if theres any
        warnings = [report for x,y in total_results.items() for report in y if logmod.INFO < x <= logmod.ERROR]
        for report in sorted(warnings, key=lambda x:x.level):
            logging.warning(str(report))

        return dict(total_results)
