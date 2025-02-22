"""
jgdv.cli provides a statemachine based argument parser.

ParseMachineBase defines the state flow,
ParseMachine implements the __call__ to start the parsing, 
CLIParser implements the callbacks for the different states.

ParamSpec's are descriptions of a single argument type, 
combined with the parsing logic for that type.
"""
from .errors import ParseError
from .arg_parser import ParseMachine
from .parse_machine_base import ArgParser_p
from .param_spec import ParamSpec
