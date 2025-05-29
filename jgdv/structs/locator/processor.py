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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from jgdv._abstract.pre_processable import PreProcessor_p, InstanceData, PostInstanceData
from jgdv.structs.strang import _interface as StrangAPI  # noqa: N812
from jgdv.structs.strang.processor import StrangBasicProcessor
from . import _interface as API # noqa: N812

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

    from jgdv._abstract.pre_processable import PreProcessResult
    from jgdv import Maybe, Ctor

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class LocationProcessor[T:API.Location_p](PreProcessor_p):

    @override
    def pre_process(self, cls:type[T], input:Any, *args:Any, strict:bool=False, **kwargs:Any) -> PreProcessResult[T]: # type: ignore[override]
        x             : Any
        default_mark  : StrangAPI.StrangMarkAbstract_e
        head_sep      : str
        text          : str
        inst_data     : InstanceData                          = InstanceData({})
        post_data     : PostInstanceData                      = PostInstanceData({})
        marks         : type[StrangAPI.StrangMarkAbstract_e]  = cls.Marks  # type: ignore[attr-defined]
        ctor          : Ctor[T]                               = cls
        match cls.section(0).end:
            case None:
                raise ValueError()
            case str() as x:
                head_sep = x

        match marks.default():
            case None:
                raise ValueError()
            case x:
                default_mark  = marks.default()

        match input:
            case StrangAPI.Strang_p():
                text = input[:,:]
            case pl.Path() as x if not strict and bool(x.suffix):
                text = f"{marks.file}{head_sep}{x}"
            case pl.Path() if not strict:
                text = f"{default_mark}{head_sep}{data}"
            case str() as x if head_sep not in x:
                return self.pre_process(cls, pl.Path(x), *args, strict=strict, **kwargs)
            case str() as x:
                text = x
            case _:
                text = str(x)

        return text, inst_data, post_data, ctor

    @override
    def process(self, obj:T, *, data:Maybe[dict]=None) -> Maybe[T]:
        pass

    @override
    def post_process(self, obj:T, data:Maybe[dict]=None) -> Maybe[T]:
        max_body         = len(self._body)
        self._body_meta  = [None for x in range(max_body)]

        # Group metadata
        for elem in self.group:
            self._group_meta.add(self.gmark_e[elem]) # type: ignore

        # Body wildycards
        for i, elem in enumerate(self.body()):
            match elem:
                case self.bmark_e.glob:
                    self._group_meta.add(self.gmark_e.abstract)
                    self._body_meta[i] = self.bmark_e.glob
                case self.bmark_e.rec_glob:
                    self._group_meta.add(self.gmark_e.abstract)
                    self._body_meta[i] = self.bmark_e.rec_glob
                case self.bmark_e.select:
                    self._group_meta.add(self.gmark_e.abstract)
                    self._body_meta[i] = self.bmark_e.select
                case str() if self.bmark_e.key in elem:
                    self._group_meta.add(self.gmark_e.abstract)
                    self._body_meta[i] = self.bmark_e.key
        else:
            match self.stem:
                case (self.bmark_e(), _):
                    self._group_meta.add(self.gmark_e.abstract)
                    self._group_meta.add(self.gmark_e.expand)
                case _:
                    pass

            match self.ext():
                case (self.bmark_e(), _):
                    self._group_meta.add(self.gmark_e.abstract)
                case _:
                    pass
