#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

import pytest
logging = logmod.root

import tomlguard

from jgdv.structs.code_ref.code_ref import CodeReference
from jgdv.util.slice import build_slice

class TestCodeReference:

    def test_basic(self):
        ref = CodeReference.build("jgdv.util.slice:build_slice")
        assert(isinstance(ref, CodeReference))

    def test_str(self):
        ref = CodeReference.build("jgdv.util.slice:build_slice")
        assert(str(ref) == "jgdv.util.slice:build_slice")

    def test_repr(self):
        ref = CodeReference.build("jgdv.util.slice:build_slice")
        assert(repr(ref) == "<CodeRef: jgdv.util.slice:build_slice>")

    def test_head(self):
        ref = CodeReference.build("jgdv.util.slice:build_slice")
        assert(ref.head == ["jgdv", "util", "slice"])

    def test_tail(self):
        ref = CodeReference.build("jgdv.util.slice:build_slice")
        assert(ref.tail == ["build_slice"])

    def test_import(self):
        ref = CodeReference.build("jgdv.util.slice:build_slice")
        imported = ref.try_import()
        assert(callable(imported))
        assert(imported == build_slice)

    def test_import_module_fail(self):
        ref = CodeReference.build("doot.taskSSSSS.base_task:DootTask")
        with pytest.raises(ImportError):
            imported = ref.try_import()

    def test_import_class_fail(self):
        ref = CodeReference.build("doot.task.base_task:DootTaskSSSSSS")
        with pytest.raises(ImportError):
            imported = ref.try_import()
