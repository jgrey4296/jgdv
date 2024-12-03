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

from jgdv.structs.strang import Strang
from jgdv.structs.strang.code_ref import CodeReference
from jgdv.util.slice import build_slice

EX_STR : Final[str] = "jgdv.util.slice:build_slice"

class TestCodeReference:

    def test_basic(self):
        ref = CodeReference(EX_STR)
        assert(isinstance(ref, CodeReference))

    def test_with_value(self):
        ref = CodeReference(EX_STR, value=int)
        assert(isinstance(ref, CodeReference))

    def test_str(self):
        ref = CodeReference(EX_STR)
        assert(str(ref) == EX_STR)

    def test_repr(self):
        ref = CodeReference("jgdv.util.slice:build_slice")
        assert(repr(ref) == f"<CodeRef: {EX_STR}>")

    def test_module(self):
        ref = CodeReference(EX_STR)
        assert(ref[0:] == "jgdv.util.slice")
        assert(ref.module == "jgdv.util.slice")

    def test_value(self):
        ref = CodeReference(EX_STR)
        assert(ref[1:] == "build_slice")
        assert(ref.value == "build_slice")

    def test_import(self):
        ref = CodeReference(EX_STR)
        imported = ref()
        assert(callable(imported))
        assert(imported == build_slice)

    def test_import_module_fail(self):
        ref = CodeReference("jgdv.taskSSSSS.base_task:DootTask")
        match ref():
            case ImportError():
                assert(True)
            case _:
                assert(False)

    def test_import_class_fail(self):
        ref = CodeReference("jgdv.structs.strang:DootTaskSSSSSS")
        match ref():
            case ImportError():
                assert(True)
            case _:
                assert(False)

    def test_import_non_callable(self):
        ref = CodeReference("jgdv.structs.strang:GEN_K")
        match ref():
            case ImportError():
                assert(True)
            case _:
                assert(False)

    def test_import_typecheck(self):
        ref = CodeReference[Strang]("jgdv.structs.strang:Strang")
        match ref():
            case ImportError():
                assert(False)
            case _:
                assert(True)


    def test_import_typecheck_fail(self):
        ref = CodeReference[bool]("jgdv.structs.strang:Strang")
        match ref():
            case ImportError():
                assert(True)
            case val:
                assert(False)
