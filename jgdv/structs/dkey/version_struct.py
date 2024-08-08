#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

from __future__ import annotations

import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError, AnyHttpUrl
from packaging.version import Version


##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##-- canonical regex
# From https://packaging.python.org/en/latest/specifications/version-specifiers/#version-specifiers-regex
VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""

CANONICAL = re.compile(
    r"^\s*" + VERSION_PATTERN + r"\s*$",
    re.VERBOSE | re.IGNORECASE,
)

##-- end canonical regex

class Version_s(BaseModel, arbitrary_types_allowed=True, extra="allow"):
    """
      A Struct for holding version information and constraints.

      Main design features:
      - compatible with PyPA version specifiers
      - compatible with PyPA dependency specifier
      - compatible with cargo dependency specifiers

      Thus:
      - semver
      - caret
      - tilde
      - wildcard
      - registry
      - git repo
      - [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
      - sorting
      - comparison
      -- compatiable
      -- matching
      -- exclusion
      -- inclusive ordering
      -- exclusive ordering
      -- arbitrary equality

    """

    version     : Version
    constraints : list
    url         : pl.Path|AnyHttpUrl

    @staticmethod
    def parse_string(version:str):
        return re.match(CANONICAL, version) is not None
