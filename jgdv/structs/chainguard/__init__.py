#!/usr/bin/env python3

from typing import Final, TypeAlias
import datetime
from collections import ChainMap

__all__     = ["GuardedAccessError", "ChainGuard", "load"]

__version__ : Final[str] = "0.4.0"

TomlTypes : TypeAlias = str | int | float | bool | list['TomlTypes'] | dict[str,'TomlTypes'] | datetime.datetime
TGDict    : TypeAlias = dict | ChainMap

from .error import GuardedAccessError
from .chainguard import ChainGuard

load        = ChainGuard.load
load_dir    = ChainGuard.load_dir
read        = ChainGuard.read
