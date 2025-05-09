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

from jgdv import identity_fn
from jgdv.structs.strang import Strang
from jgdv.structs.strang.code_ref import CodeReference

EX_STR    : Final[str] = "fn::jgdv:identity_fn"
NO_PREFIX : Final[str] = "jgdv:identity_fn"

class TestCodeReference:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        ref = CodeReference(EX_STR)
        assert(isinstance(ref, CodeReference))

    def test_with_no_prefix(self):
        ref = CodeReference(NO_PREFIX)
        assert(isinstance(ref, CodeReference))

    def test_(self):
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
        assert(ref[1::-1] == "jgdv")
        assert(ref.module == "jgdv")

    def test_value(self):
        ref = CodeReference(EX_STR)
        assert(ref.value == "identity_fn")


    def test_from_fn(self):
        def simple_fn():
            return "blah"

        ref = CodeReference.from_value(simple_fn)
        assert(ref() is simple_fn)

class TestCodeReferenceImporting:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_import(self):
        ref      = CodeReference(EX_STR)
        match ref():
            case Exception() as x:
                assert(False), x
            case x:
                assert(callable(x))
                assert(x == identity_fn)

    def test_import_module_fail(self):
        ref = CodeReference("cls::jgdv.taskSSSSS.base_task:DootTask")
        match ref():
            case ImportError():
                assert(True)
            case x:
                assert(False), x

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
