#!/usr/bin/env python3
"""
Utility classes for attribute based access to loaded toml data ::

    # Simplifies:
    data['blah']['awe']['awg']
    # to:
    data.blah.awe.awg

    # Also allows guarded access:

    result = data.on_fail('fallback').somewhere.along.this.doesnt.exist()
    result == "fallback" or data.somewhere.along.this.doesnt.exist


The underlying Python access model (simplified)::

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

# ##-- Generated Exports
__all__ = (
    "ChainGuard",
    "load"
    "GuardedAccessError",
)
# ##-- end Generated Exports


from .errors import GuardedAccessError
from ._base import TomlTypes
from .chainguard import ChainGuard

load        = ChainGuard.load     # type: ignore
load_dir    = ChainGuard.load_dir # type: ignore
read        = ChainGuard.read     # type: ignore
