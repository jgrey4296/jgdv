#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
# import abc
import datetime
import enum
import functools as ftz
import importlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
# from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import more_itertools as mitz
from pydantic import BaseModel, Field, field_validator
from tomlguard import TomlGuard

# ##-- end 3rd party imports

# ##-- 1st party imports
import doot
import doot.errors
from doot._abstract.protocols import Buildable_p, Nameable_p, ProtocolModelMeta
from doot.enums import Report_f, TaskMeta_f

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

PAD            : Final[int]                = 15
TaskFlagNames  : Final[str]                = [x.name for x in TaskMeta_f]
TailEntry      : TypeAlias                 = str|int|UUID
FMT_PATTERN    : Final[re.Pattern]         = re.compile("^(h?)(t?)(p?)")

class StrStruct(str, Nameable_p):
    """
      A Structured String, in the form (using sep=::):
      {head}::{tail}::{params}
      params can be lists '[x,y,z]'
      or dicts '{a=x, b=y}'

      eg: tasks.simple::format.files[*.py]

      Useful methods to override:
      '_validate' for ensuring the origin str is of the right format
      '_process'
      '_process_head'
      '_process_tail'
      '_process_params'
      '_tidy_up'
    """

    __sep    : ClassVar[str] = "::"
    __subsep : ClassVar[str] = "."

    def __new__(cls, *args, **kwargs):
        # only pass the first argument to str new
        return str.__new__(cls, args[0])

    def __init__(self, data, *, sep=None, subsep=None, meta=None):
        super().__init__()
        self._sep    = sep or StrStruct.__sep
        self._subsep = subsep or StrStruct.__subsep
        self.metadata = {}
        if meta:
            self.metadata.update(meta)
        self._validate()
        head, tail, params           = self._process()
        self.head   : list[str]      = head
        self.tail   : list[str]      = tail
        self.params : None|list|dict = params
        self._tidy_up()

    def __lt__(self, other) -> bool:
        """ test for hierarhical ordering of names
        eg: self(a.b.c) < other(a.b.c.d)
        ie: other ∈ self
        """
        match other:
            case StrStruct():
                pass
            case str():
                other = self.__class__(other)
            case _:
                return False

        if len(self.head) != len(other.head):
            return False
        if len(self.tail) >= len(other.tail):
            return False

        for x,y in zip(self.head, other.head):
            if x != y:
                return False

        for x,y in zip(self.tail, other.tail):
            if x != y:
                return False

        return True

    def __format__(self, spec) -> str:
        """ format additions for structured strings:
          {:h} = print only the head_str
          {:t} = print only the tail_str
          {:p} = print only the params_str

          """
        relevant   = FMT_PATTERN.search(spec)
        remaining  = FMT_PATTERN.sub("", spec)
        result     = []
        if bool(relevant[1]):
            result.append(self.head_str())
        if bool(relevant[2]):
            result.append(self.tail_str())
        if bool(relevant[3]) and bool(self.params):
            result.append(str(self.params))

        return format(self._sep.join(result), remaining)

    def _validate(self) -> None:
        if self._sep not in self:
            raise ValueError("Separator not found", self, self._sep)

    def _process(self) -> tuple[list[str], list[str], list|dict]:
        raw_head, _, raw_tail_w_params = self.partition(self._sep)
        raw_tail, _, raw_params = raw_tail_w_params.partition(self._sep)
        return (self._process_head(raw_head.strip()),
                self._process_tail(raw_tail.strip()),
                self._process_params(raw_params.strip()))

    def _process_head(self, head:str) -> list[str]:
        result = []
        for part in [x for x in head.split(self._subsep) if bool(x)]:
            result.append(part.removeprefix('"').removesuffix('"'))

        return result

    def _process_tail(self, tail:str) -> list[str]:
        result = []
        for part in [x for x in tail.split(self._subsep)]:
            result.append(part.removeprefix('"').removesuffix('"'))

        return result

    def _process_params(self, params:str) -> None|list|dict:
        if not bool(params):
            return None

        return TomlGuard.read(f"params = {params}").params

    def _tidy_up(self):
        """ for post-processing self.head and self.tail """
        self.tail = [x for x in self.tail if bool(x)]
        # subsplit values
        # check invariants
        # remove elements

    def tail_str(self) -> str:
        return self._subsep.join(str(x) for x in self.tail)

    def head_str(self) -> str:
        return self._subsep.join(str(x) for x in self.head)

class TaskName(StrStruct):
    """
      A Structured String for describing tasks and jobs

      Marks roots with empty subsections,
      eg: tasks.formatting::simple.task..one

    """

    __sep               : ClassVar[str]           = doot.constants.patterns.TASK_SEP
    __gen_marker         : ClassVar[str]           = doot.constants.patterns.SPECIALIZED_ADD
    __internal_marker    : ClassVar[str]           = doot.constants.patterns.INTERNAL_TASK_PREFIX
    __head_marker        : ClassVar[str]           = doot.constants.patterns.SUBTASKED_HEAD
    __job_marker         : ClassVar[str]           = "+" # TODO move to constants.toml
    __root_marker        : ClassVar[str]           = ""  # TODO move to constants.toml

    def __init__(self, data):
        super().__init__(data, sep=TaskName.__sep)
        self._roots : tuple[int, int] = self._find_roots() or [-1, -1]
        self._flags = TaskMeta_f.default

    def _tidy_up(self):
        # Remove duplicate root marks from tail
        # eg: a...b -> a..b
        root_set = {self.__root_marker}
        self.tail = [x for x,y in zip(self.tail, itz.chain(self.tail[1:], [None])) if {x,y} != root_set ]

        # handle metadata
        if self.tail[0] == TaskName.__job_marker:
            self._flags |= TaskMeta_f.JOB
        if self.tail[0] == TaskName.__internal_marker:
            self._flags |= TaskMeta_f.INTERNAL
        if TaskName.__gen_marker in self.tail:
            self._flags |= TaskMeta_f.CONCRETE
        if TaskName.__head_marker in self.tail:
            self._flags |= TaskMeta_f.JOB_HEAD
            self._flags &= ~TaskMeta_f.JOB

    def _find_roots(self) -> None|tuple[int, int]:
        # filter out double root markers
        indices = [i for i,x in enumerate(self.tail[:-1]) if x == TaskName.__root_marker]
        if not bool(indices):
            return None

        top_root, bottom_root = min(indices), max(indices)
        return (top_root, bottom_root)

    def has_root(self):
        match self._roots:
            case [-1, -1]:
                return False
            case _:
                return True

    def root(self, *, top=False) -> TaskName:
        """
        Strip off one root marker's worth of the name, or to the top marker.
        eg:
        root(test::a.b.c..<UUID>.sub..other) => test::a.b.c..<UUID>.sub.
        root(test::a.b.c..<UUID>.sub..other, top=True) => test::a.b.c.

        """
        match self._roots:
            case [-1, -1]:
                return self
            case [x, _] if top:
                tail_selection = self._subsep.join(self.tail[:x])
                val = f"{self:h}{self._sep}{tail_selection}{self._sep}{self:p}"
                return TaskName(head=self.head[:], tail=self.tail[:x])
            case [_, x]:
                tail_selection = self._subsep.join(self.tail[:x])
                val = f"{self:h}{self._sep}{tail_selection}{self._sep}{self:p}"
                return TaskName(head=self.head[:], tail=self.tail[:x])

    def add_root(self) -> TaskName:
        """ Add a root marker if the last element isn't already a root marker
        eg: group::a.b.c => group.a.b.c.
        (note the trailing '.')
        """
        match self.last():
            case x if x == TaskName.__root_marker:
                return self
            case _:
                return self.subtask()

    def subtask(self, *subtasks, subgroups:list[str]|None=None, **kwargs) -> TaskName:
        """ generate an extended name, with more information
        eg: a.group::simple.task
        ->  a.group::simple.task..targeting.something

        adds a root marker to recover the original
        """

        args = self.args.copy() if self.args else {}
        if bool(kwargs):
            args.update(kwargs)
        subs = [TaskName.__root_marker]
        subgroups = subgroups or []
        match [x for x in subtasks if x != None]:
            case [int() as i, TaskName() as x]:
                subs.append(str(i))
                subs.append(x.task.removeprefix(self.task + "."))
            case [str() as x]:
                subs.append(x)
            case [int() as x]:
                subs.append(str(x))
            case [*xs]:
                subs += xs

        return TaskName(head=self.head + subgroups,
                        tail=self.tail + subs,
                        meta=self.meta,
                        args=args,
                        )

    def job_head(self) -> TaskName:
        """ generate a canonical head/completion task name for this name
        eg: (concrete) group::simple.task..$gen$.<UUID> ->  group::simple.task..$gen$.<UUID>..$head$
        eg: (abstract) group::simple.task. -> group::simple.task..$head$

        """
        if TaskMeta_f.JOB_HEAD in self.meta:
            return self

        return self.subtask(TaskName.__head_marker)

    def instantiate(self, *, prefix=None) -> TaskName:
        """ Generate a concrete instance of this name with a UUID appended,
        optionally can add a prefix
          # TODO possibly do $gen$.{prefix?}.<UUID>

          ie: a.task.group::task.name..{prefix?}.$gen$.<UUID>
        """
        uuid = uuid1()
        match prefix:
            case None:
                return self.subtask(TaskName.__gen_marker, uuid, uuid=uuid)
            case _:
                return self.subtask(prefix, TaskName.__gen_marker, uuid, uuid=uuid)

    def last(self) -> None|TailEntry:
        """
        Get the last value of the task/tail
        """
        if bool(self.tail):
            return self.tail[-1]
        return None

class CodeReference(StrStruct):
    """
      A Structured String for describing code to load and run
    """
    __sep : ClassVar[str]                    = doot.constants.patterns.IMPORT_SEP

    def __new__(cls, data):
        match data:
            case str():
                pass
            case type():
                pass
            case EntryPoint():
                pass


        return str.__new__(CodeReference, data)

    def __init__(self, data):
        super().__init__(data, sep=CodeReference.__sep)

    def try_import(self):
        try:
            if self._type is not None:
                curr = self._type
            else:
                mod = importlib.import_module(self.module)
                curr = mod
                for name in self.tail:
                    curr = getattr(curr, name)

            if bool(self._mixins):
                mixins = []
                for mix in self._mixins:
                    match mix:
                        case CodeReference():
                            mixins.append(mix.try_import())
                        case type():
                            mixins.append(mix)
                curr = type(f"DootGenerated:{curr.__name__}", tuple(mixins + [curr]), {})

            if ensure is not Any and not (isinstance(curr, ensure) or issubclass(curr, ensure)):
                raise ImportError("Imported Code Reference is not of correct type", self, ensure)

            return curr
        except ModuleNotFoundError as err:
            raise ImportError("Module can't be found", str(self))
        except AttributeError as err:
            raise ImportError("Attempted to import %s but failed", str(self)) from err


class VersionStr(StrStruct):
    """
      A Structured String for describing version constraints
    """
    pass
