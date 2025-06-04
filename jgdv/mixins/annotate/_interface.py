#!/usr/bin/env python3
"""


"""
# ruff: noqa:

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

MODULE_NAME              : Final[str]  = "__module__"
SLOTS_NAME               : Final[str]  = "__slots__"
ANNOTS_NAME              : Final[str]  = "__annotations__"

FreshKWD                 : Final[str]  = "fresh_registry"
Default_K                : Final[str]  = "__default__"
AnnotateKWD              : Final[str]  = "_annotate_to"
AnnotationTarget         : Final[str]  = "__jgdv_typevar__"
AnnotateRx               : Final[Rx]   = re.compile(r"(?P<name>\w+)(?:<(?P<extras>.*?)>)?(?:\[(?P<params>.*?)\])?")

MultiParamFail           : Final[str]  = "Multi Param Annotation not supported yet"
BadParamFail             : Final[str]  = "Bad param value for making an annotated subclass"
NoPydanticFail           : Final[str]  = "Extending pydantic classes with a new mro is not implemented"

NoNameMatch              : Final[str]  = "Couldn't even match the cls name"
NoSubName                : Final[str]  = "No decorated name available"
BadDecorationNameTarget  : Final[str]  = "Unexpected name decoration target"
UnexpectedMRO            : Final[str]  = "Unexpected mro type"
UnexpectedNameSpace      : Final[str]  = "Unexpected namespace type"

ORIG_BASES_K             : Final[str]  = "__orig_bases__"
