#!/usr/bin/env python3

from typing import Final, TypeAlias
import datetime
from collections import ChainMap

__all__     = ["GuardedAccessError", "GuardedChain", "load"]

__version__ : Final[str] = "0.4.0"

TomlTypes : TypeAlias = str | int | float | bool | list['TomlTypes'] | dict[str,'TomlTypes'] | datetime.datetime
TGDict    : TypeAlias = dict | ChainMap

from .error import GuardedAccessError
from .guarded_chain import GuardedChain

load        = GuardedChain.load
load_dir    = GuardedChain.load_dir
read        = GuardedChain.read
