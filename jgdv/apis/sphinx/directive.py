#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import StringList

def setup(app):
    """
    Adds the directive `.. $1::` for use in rst-files
    """
    app.add_directive("$1", $2Directive)

class $2Directive(Directive):
    has_content        = False
    required_arguments = 0
    optional_arguments = 0

    the_text = ""

    def run(self):
        container          = nodes.literal_block()
        translated_content = StringList($2Directive.the_text.splitlines(keepends=False))
        self.state.nested_parse(translated_content, 0, container)
        return [container]
