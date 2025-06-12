"""
jgdv.cli provides a statemachine based argument parser.

ParseMachineBase defines the state flow,
ParseMachine implements the __call__ to start the parsing, 
CLIParser implements the callbacks for the different states.

ParamSpec's are descriptions of a single argument type, 
combined with the parsing logic for that type.
"""
from ._interface import ParamStruct_p, ArgParser_p, ParamSource_p, CLIParamProvider_p
from .errors import ParseError
from .arg_parser import ParseMachine
from .param_spec import ParamSpec
from .builder_mixin import ParamSpecMaker_m
