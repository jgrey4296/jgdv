#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import abc
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

# ##-- end stdlib imports

# ##-- 3rd party imports
from tomlguard import TomlGuard
from pydantic import BaseModel

# ##-- end 3rd party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

T = TypeVar("T")

from jgdv._abstract.protocols import (ProtocolModelMeta, ArtifactStruct_p,
                                      UpToDate_p, StubStruct_p, ParamStruct_p, SpecStruct_p, TomlStubber_p,
                                      CLIParamProvider_p, ActionGrouper_p, Loader_p, Buildable_p, Factory_p,
                                      Nameable_p, Key_p, ExecutableTask_p, Decorator_p
                                      )

@runtime_checkable
class ExecutableTask(Protocol):
    """ Runners pass off to Tasks/Jobs implementing this protocol
      instead of using their default logic
    """

    def setup(self):
        """ """
        pass

    def expand(self) -> list[Task_i|"TaskSpec"]:
        """ For expanding a job into tasks """
        pass

    def execute(self):
        """ For executing a task """
        pass

    def teardown(self):
        """ For Cleaning up the task """
        pass

    def check_entry(self) -> bool:
        """ For signifiying whether to expand/execute this object """
        pass

    def execute_action_group(self, group_name:str) -> "ActRE"|list:
        """ Optional but recommended """
        pass

    def execute_action(self):
        """ For executing a single action """
        pass

    def current_status(self) -> TaskStatus_e:
        pass

    def force_status(self, status:TaskStatus_e):
        pass

    def current_priority(self) -> int:
        pass

    def decrement_priority(self):
        pass

