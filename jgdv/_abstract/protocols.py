#!/usr/bin/env python3
"""

"""
# ruff: noqa: N801
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import functools as ftz
import itertools as itz
import logging as logmod
import re
import time
import types
import typing
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

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

if TYPE_CHECKING:
    import pathlib as pl
    import enum
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from .types import Maybe, Ctor
    type ChainGuard = Any
    type Logger     = logmod.Logger

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@runtime_checkable
class ArtifactStruct_p(Protocol):
    """ Base class for artifacts, for type matching """

    def exists(self, *, data=None) -> bool: ...  # noqa: ANN001

@runtime_checkable
class UpToDate_p(Protocol):
    """ For things (often artifacts) which might need to have actions done if they were created too long ago """

    def is_stale(self, *, other:Any=None) -> bool: ...  # noqa: ANN401
    """ Query whether the task's artifacts have become stale and need to be rebuilt"""

@runtime_checkable
class StubStruct_p(Protocol):
    """ Base class for stubs, for type matching """

    def to_toml(self) -> str: ...

@runtime_checkable
class SpecStruct_p(Protocol):
    """ Base class for specs, for type matching """

    @property
    def params(self) -> dict|ChainGuard: ...

    @property
    def args(self) -> list: ...

    @property
    def kwargs(self) -> dict: ...

@runtime_checkable
class TomlStubber_p(Protocol):
    """
      Something that can be turned into toml
    """

    @classmethod
    def class_help(cls) -> str: ...

    @classmethod
    def stub_class(cls, stub:StubStruct_p) -> None: ...
    """
        Specialize a StubStruct_p to describe this class
    """

    def stub_instance(self, stub:StubStruct_p) -> None: ...
    """
        Specialize a StubStruct_p with the settings of this specific instance
    """

    @property
    def short_doc(self) -> str: ...
    """ Generate Job Class 1 line help string """

    @property
    def doc(self) -> list[str]: ...

@runtime_checkable
class ActionGrouper_p(Protocol):
    """ For things have multiple named groups of actions """

    def get_group(self, name:str) -> Maybe[list]: ...

@runtime_checkable
class Loader_p(Protocol):
    """ The protocol for something that will load something from the system, a file, etc
    TODO add a type parameter
    """

    def setup(self, extra_config:ChainGuard) -> Self: ...

    def load(self) -> ChainGuard: ...

@runtime_checkable
class Buildable_p(Protocol):
    """ For things that need building, but don't have a separate factory
    TODO add type parameter
    """

    @classmethod
    def build(cls, *args:Any) -> Self: ...  # noqa: ANN401

@runtime_checkable
class Factory_p[T](Protocol):
    """
      Factory protocol: {type}.build
    """

    @classmethod
    def build(cls:Ctor[T], *args:Any, **kwargs:Any) -> T: ...  # noqa: ANN401

@runtime_checkable
class Nameable_p(Protocol):
    """ The core protocol of something use as a name """

    def __hash__(self) -> int: ...

    def __eq__(self, other:object) -> bool: ...

    def __lt__(self, other:Nameable_p) -> bool: ...

    def __contains__(self, other:Nameable_p) -> bool: ...

@runtime_checkable
class InstantiableSpecification_p(Protocol):
    """ A Specification that can be instantiated further """

    def instantiate_onto(self, data:Maybe[Self]) -> Self: ...

    def make(self) -> Self: ...

@runtime_checkable
class ExecutableTask(Protocol):
    """ Runners pass off to Tasks/Jobs implementing this protocol
      instead of using their default logic
    """

    def setup(self) -> None: ...
    """ """

    def expand(self) -> list: ...
    """ For expanding a job into tasks """

    def execute(self) -> None: ...
    """ For executing a task """

    def teardown(self) -> None: ...
    """ For Cleaning up the task """

    def check_entry(self) -> bool: ...
    """ For signifiying whether to expand/execute this object """

    def execute_action_group(self, group_name:str) -> enum.Enum|list: ...
    """ Optional but recommended """

    def execute_action(self) -> None: ...
    """ For executing a single action """

    def current_status(self) -> enum.Enum: ...

    def force_status(self, status:enum.Enum) -> None: ...

    def current_priority(self) -> int: ...

    def decrement_priority(self) -> None: ...

@runtime_checkable
class Persistent_p(Protocol):
    """ A Protocol for persisting data """

    def write(self, target:pl.Path) -> None: ...
    """ Write this object to the target path """

    def read(self, target:pl.Path) -> None: ...
    """ Read the target file, creating a new object """

@runtime_checkable
class FailHandler_p(Protocol):

    def handle_failure(self, err:Exception, *args:Any, **kwargs:Any) -> Maybe[Any]: ...  # noqa: ANN401

@runtime_checkable
class Visitor_p(Protocol):

    def visit(self, **kwargs:Any) -> Any: ...  # noqa: ANN401

@runtime_checkable
class DILogger_p(Protocol):
    """ Protocol for classes with a dependency injectable logger """

    def logger(self) -> Logger: ...
