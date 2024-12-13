#!/usr/bin/env python3
"""
Utility classes for attribute based access to loaded toml data,
simplifying: data['blah']['awe']['awg']
to:          data.blah.awe.awg

Also allows guarded access:
result = data.on_fail('fallback').somewhere.along.this.doesnt.exist()
result == "fallback" or data.somewhere.along.this.doesnt.exist

Python access model (simplified):
object.__getattribute(self, name):
    try:
        return self.__dict__[name]
    except AttributeError:
        return self.__getattr__(name)

So by looking up values in ChainGuard.__table and handling missing values,
we can skip dict style key access
"""
from typing import Final, TypeAlias
import datetime
from collections import ChainMap

__all__     = ["GuardedAccessError", "ChainGuard", "load"]

type TomlTypes = str | int | float | bool | list['TomlTypes'] | dict[str,'TomlTypes'] | datetime.datetime

from .error import GuardedAccessError
from .chainguard import ChainGuard

load        = ChainGuard.load
load_dir    = ChainGuard.load_dir
read        = ChainGuard.read
