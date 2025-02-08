"""
jgdv.cli provides a statemachine based argument parser

"""
from . import errors
from .errors import ParseError
from .arg_parser import ParseMachine
from .parse_machine_base import ArgParser_p
from .param_spec import ParamSpec
