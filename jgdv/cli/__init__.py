"""
jgdv.cli provides a statemachine based argument parser.

ParseMachineBase defines the state flow,
ParseMachine implements the __call__ to start the parsing, 
CLIParserModel implements the callbacks for the different states.

ParamSpec's are descriptions of a single argument type, 
combined with the parsing logic for that type.
"""
from ._interface import ParamSpec_p, ArgParserModel_p, ParamSource_p, CLIParamProvider_p
from .errors import ParseError
from .parse_machine import ParseMachine
from .parser_model import CLIParserModel
from .param_spec import ParamSpec
from .builder_mixin import ParamSpecMaker_m
