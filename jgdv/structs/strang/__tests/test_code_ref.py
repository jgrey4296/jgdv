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

from jgdv.structs.strang import Strang
from jgdv.structs.strang.code_ref import CodeReference
from jgdv.util.slice import build_slice

EX_STR : Final[str] = "fn::jgdv.util.slice:build_slice"

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
        ref = CodeReference(EX_STR)
        assert(repr(ref) == f"<CodeRef: {EX_STR}>")

    def test_module(self):
        ref = CodeReference(EX_STR)
        assert(ref.module == "jgdv.util.slice")

    def test_value(self):
        ref = CodeReference(EX_STR)
        assert(ref.value == "build_slice")

    def test_import(self):
        ref      = CodeReference(EX_STR)
        match ref():
            case Exception():
                assert(False)
            case x:
                assert(callable(x))
                assert(x == build_slice)

    def test_import_module_fail(self):
        ref = CodeReference("cls::jgdv.taskSSSSS.base_task:DootTask")
        match ref():
            case ImportError():
                assert(True)
            case _:
                assert(False)

    def test_import_non_existent_class_fail(self):
        ref = CodeReference("cls::jgdv.structs.strang:DootTaskSSSSSS")
        match ref():
            case ImportError():
                assert(True)
            case _:
                assert(False)

    def test_import_non_class_fail(self):
        ref = CodeReference("cls::jgdv.structs.strang.strang:GEN_K")
        match ref():
            case ImportError():
                assert(True)
            case _:
                assert(False)

    def test_import_non_callable(self):
        ref = CodeReference("fn::jgdv.structs.strang.strang:GEN_K")
        match ref():
            case ImportError():
                assert(True)
            case _:
                assert(False)

    def test_import_value(self):
        ref = CodeReference("val::jgdv.structs.strang.strang:GEN_K")
        match ref():
            case ImportError():
                assert(False)
            case _:
                assert(True)

    def test_import_typecheck(self):
        ref = CodeReference[Strang]("cls::jgdv.structs.strang:Strang")
        match ref():
            case ImportError():
                assert(False)
            case _:
                assert(True)

    def test_import_typecheck_fail(self):
        ref = CodeReference[bool]("cls::jgdv.structs.strang:Strang")
        match ref():
            case ImportError():
                assert(True)
            case val:
                assert(False)
