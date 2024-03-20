"""

"""
##-- imports
from __future__ import annotations

import abc
import importlib
import logging as logmod
import re
from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from enum import Enum
from os.path import abspath, exists, expanduser, split, splitext
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)

import acab
import pyparsing as pp
from acab import types as AT
from acab.core.parsing import debug_funcs as DBF
from acab_config.utils.log_formatter import AcabLogFormatter, AcabMinimalLogRecord
from acab.core.value.instruction import ProductionOperator, ProductionStructure
from acab.modules.repl import ReplParser as RP
from acab.modules.repl.repl_commander import register

##-- end imports

config = acab.config


logging = logmod.getLogger(__name__)

# TODO shift this into config
ModuleFragment : TypeAlias = AT.ModuleFragment

SPLIT_RE         = re.compile("[ .!?/]")
shortcut_config  = config.module.REPL.shortcuts
shortcut_pairs   = sorted([(shortcut_config[cmd], cmd) for cmd in shortcut_config._keys])

@register
def do_shortcuts(self, line):
    """
    Print the :{kw} shortcut bindings loaded from config
    """
    print("Repl Shortcut commands: ")
    for kw, cmd in shortcut_pairs:
        print(f"    :{kw:<5} -> {cmd}")


@register
def do_acab(self, line):
    """ All Cops Are Bastards """
    print("All Cops Are Bastards")
