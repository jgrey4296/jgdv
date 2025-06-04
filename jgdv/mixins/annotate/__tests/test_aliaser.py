#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN202, B011, PLR2004
# Imports
from __future__ import annotations

##-- stdlib imports
import logging as logmod
import pathlib as pl
from typing import (Any, ClassVar, Generic, TypeAlias,
                    TypeVar, cast)
from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping, Sequence
from re import Match
from types import GenericAlias
import warnings

##-- end stdlib imports

import pytest
from .. import Subclasser, SubAlias_m

# Logging:
logging = logmod.root

# Global Vars:

class TestSubAlias:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_simple(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        assert(hasattr(Basic, "_registry"))
        assert(hasattr(Basic, "_clear_registry"))
        assert(Basic.cls_annotation() == ())

    def test_matching_direct(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        class IntBasic(Basic[int]):
            pass

        inst = IntBasic()
        match inst:
            case IntBasic():
                assert(True)
            case x:
                assert(False), x

    def test_matching_superclass(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        class IntBasic(Basic[int]):
            pass

        inst = IntBasic()
        match inst:
            case Basic():
                assert(True)
            case x:
                assert(False), x

class TestSubAlias_Access:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_class_getitem_generic_aliases(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        match Basic[int]:
            case GenericAlias() as x:
                assert(x.__args__ == (int,))
            case x:
                assert(False), x

        match Basic[float]:
            case GenericAlias() as x:
                assert(x.__args__ == (float,))
            case x:
                assert(False), x

        match Basic["test"]:
            case GenericAlias() as x:
                assert(x.__args__ == ("test",))
            case x:
                assert(False), x

    def test_repeated_access(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        gen1 = Basic[int]
        gen2 = Basic[int]
        assert(gen1 is not gen2)
        assert(gen1 == gen2)

class TestSubAlias_Registry:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_fresh_registry(self):

        class Basic(SubAlias_m):
            pass

        class Other(SubAlias_m, fresh_registry=True):
            pass

        assert(Basic._registry is not Other._registry)

class TestSubAlias_Subclassing:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_annotated(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        class SimpleBasic(Basic):
            pass

        assert(issubclass(SimpleBasic, Basic))
        assert(SimpleBasic.cls_annotation() is Basic.cls_annotation())
        assert(SimpleBasic.cls_annotation() == ())

    def test_unannotated_repeat(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        class SimpleBasic(Basic):
            pass

        class SubSimple(SimpleBasic):
            pass

        assert(issubclass(SimpleBasic, Basic))
        assert(SimpleBasic.cls_annotation() is Basic.cls_annotation())
        assert(SimpleBasic.cls_annotation() == ())

    def test_unannotated_multi(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        class SimpleBasic(Basic):
            pass

        class OtherBasic(Basic):
            pass

        assert(issubclass(SimpleBasic, Basic))
        assert(SimpleBasic.cls_annotation() is Basic.cls_annotation())
        assert(SimpleBasic.cls_annotation() == ())

    def test_annotated_by_access(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        class IntBasic(Basic[int]):
            pass

        assert(IntBasic is Basic[int])
        assert(issubclass(IntBasic, Basic))
        assert(IntBasic.cls_annotation() is Basic[int].cls_annotation())
        assert(IntBasic.cls_annotation() == (int,))


    def test_annotated_by_kwarg(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        class IntBasic(Basic, annotation=int):
            pass

        assert(IntBasic is Basic[int])
        assert(issubclass(IntBasic, Basic))
        assert(IntBasic.cls_annotation() is Basic[int].cls_annotation())
        assert(IntBasic.cls_annotation() == (int,))


    def test_multi_annotation_by_kwarg(self):

        class Basic(SubAlias_m, fresh_registry=True):
            pass

        class IntBasic(Basic, annotation=[int, "blah"]):
            pass

        assert(IntBasic is Basic[int, "blah"])
        assert(issubclass(IntBasic, Basic))
        assert(IntBasic.cls_annotation() is Basic[int, "blah"].cls_annotation())
        assert(IntBasic.cls_annotation() == (int,"blah"))

    def test_retrieved_subclass_conflict_error(self):

        class Basic(SubAlias_m, fresh_registry=True, strict=True):
            pass

        class IntBasic(Basic[int]):
            pass

        assert(IntBasic.cls_annotation() == (int,))
        with pytest.raises(TypeError):

            class RetrievedIntBasic(Basic[int]):
                pass

    def test_explicit_subclass_conflict_error(self):

        class Basic(SubAlias_m, fresh_registry=True, strict=True):
            pass

        class IntBasic(Basic[int]):
            pass

        with pytest.raises(TypeError):

            class ExplicitIntBasic(IntBasic):
                pass

class TestSubAlias_Accumulation:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_accumulation_a(self):

        class Basic(SubAlias_m, fresh_registry=True, accumulate=True):
            pass

        class IntBasic(Basic[int]):
            pass

        class AnotherIntBasic(Basic[int]['another']):
            pass

        assert(issubclass(IntBasic, Basic))
        assert(issubclass(AnotherIntBasic, Basic))
        assert(issubclass(AnotherIntBasic, IntBasic))
        assert(AnotherIntBasic.cls_annotation() == (int, "another"))

    def test_accumulation_b(self):

        class Basic(SubAlias_m, fresh_registry=True, accumulate=True):
            pass

        class IntBasic(Basic[int]):
            pass

        class AnotherIntBasic(IntBasic['blah']):
            pass

        assert(issubclass(IntBasic, Basic))
        assert(issubclass(AnotherIntBasic, Basic))
        assert(issubclass(AnotherIntBasic, IntBasic))
        assert(AnotherIntBasic.cls_annotation() == (int, "blah"))
