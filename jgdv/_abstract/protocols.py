#!/usr/bin/env python3
"""

"""

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
import typing
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from pydantic import BaseModel

# ##-- end 3rd party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

ProtoMeta       = type(Protocol)
PydanticMeta    = type(BaseModel)
if TYPE_CHECKING:
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable
    type ChainGuard = Any
    type Maybe[T]   = None|T
    type Ctor[T]    = type(T) | Callable[[*Any], T]

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class ProtocolModelMeta(ProtoMeta, PydanticMeta):
    """ Use as the metaclass for pydantic models which are explicit Protocol implementers

      eg:

      class Example(BaseModel, ExampleProtocol, metaclass=ProtocolModelMeta):...

    """
    pass

@runtime_checkable
class ArtifactStruct_p(Protocol):
    """ Base class for artifacts, for type matching """

    def exists(self, *, data=None) -> bool:
        pass

@runtime_checkable
class UpToDate_p(Protocol):
    """ For things (often artifacts) which might need to have actions done if they were created too long ago """

    def is_stale(self, *, other:Any=None) -> bool:
        """ Query whether the task's artifacts have become stale and need to be rebuilt"""
        pass

@runtime_checkable
class StubStruct_p(Protocol):
    """ Base class for stubs, for type matching """

    def to_toml(self) -> str:
        pass

@runtime_checkable
class SpecStruct_p(Protocol):
    """ Base class for specs, for type matching """

    @property
    def params(self) -> dict|ChainGuard:
        pass

@runtime_checkable
class TomlStubber_p(Protocol):
    """
      Something that can be turned into toml
    """

    @classmethod
    def class_help(cls) -> str:
        pass

    @classmethod
    def stub_class(cls, stub:StubStruct_p):
        """
        Specialize a StubStruct_p to describe this class
        """
        pass

    def stub_instance(self, stub:StubStruct_p):
        """
          Specialize a StubStruct_p with the settings of this specific instance
        """
        pass

    @property
    def short_doc(self) -> str:
        """ Generate Job Class 1 line help string """
        pass

    @property
    def doc(self) -> list[str]:
        pass

@runtime_checkable
class CLIParamProvider_p(Protocol):
    """
      Things that can provide parameter specs for CLI parsing
    """

    @classmethod
    def param_specs(cls) -> list[ParamStruct_p]:
        """  make class parameter specs  """
        pass

@runtime_checkable
class ActionGrouper_p(Protocol):
    """ For things have multiple named groups of actions """

    def get_group(self, name:str) -> Maybe[list]:
        pass

@runtime_checkable
class Loader_p(Protocol):
    """ The protocol for something that will load something from the system, a file, etc
    TODO add a type parameter
    """

    def setup(self, extra_config:ChainGuard) -> Self:
        pass

    def load(self) -> ChainGuard:
        pass

@runtime_checkable
class Buildable_p(Protocol):
    """ For things that need building, but don't have a separate factory
    TODO add type parameter
    """

    @staticmethod
    def build(*args) -> Self:
        pass

@runtime_checkable
class Factory_p[T](Protocol):
    """
      Factory protocol: {type}.build
    """

    @classmethod
    def build(cls:Ctor[T], *args, **kwargs) -> T:
        pass

@runtime_checkable
class Nameable_p(Protocol):
    """ The core protocol of something use as a name """

    def __hash__(self):
        pass

    def __eq__(self, other) -> bool:
        pass

    def __lt__(self, other) -> bool:
        pass

    def __contains__(self, other) -> bool:
        pass

@runtime_checkable
class InstantiableSpecification_p(Protocol):
    """ A Specification that can be instantiated further """

    def instantiate_onto(self, data:Maybe[Self]) -> Self:
        pass

    def make(self):
        pass

@runtime_checkable
class ExecutableTask(Protocol):
    """ Runners pass off to Tasks/Jobs implementing this protocol
      instead of using their default logic
    """

    def setup(self):
        """ """
        pass

    def expand(self) -> list:
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

    def execute_action_group(self, group_name:str) -> enum.Enum|list:
        """ Optional but recommended """
        pass

    def execute_action(self):
        """ For executing a single action """
        pass

    def current_status(self) -> enum.Enum:
        pass

    def force_status(self, status:enum.Enum):
        pass

    def current_priority(self) -> int:
        pass

    def decrement_priority(self):
        pass

@runtime_checkable
class Persistent_p(Protocol):
    """ A Protocol for persisting data """

    def write(self, target:pl.Path) -> None:
        """ Write this object to the target path """
        pass

    def read(self, target:pl.Path) -> None:
        """ Read the target file, creating a new object """
        pass

@runtime_checkable
class FailHandler_p(Protocol):

    def handle_failure(self, err:Exception, *args, **kwargs) -> Maybe[Any]:
        pass

@runtime_checkable
class PreProcessed_p(Protocol):
    """ Protocol for things like Strang,
    which preprocess the initialisation data before even __new__ is called.

    Is used in a metatype.__call__ as:
    cls._pre_process(...)
    obj = cls.__new__(...)
    obj.__init__(...)
    obj._process()
    obj._post_process()
    return obj

    """

    @classmethod
    def _pre_process(cls, data:Any, *, strict=False) -> Any:
        pass

    def _process(self) -> None:
        pass

    def _post_process(self) -> None:
        pass
