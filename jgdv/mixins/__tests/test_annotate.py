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
from ..annotate import SubAnnotate_m, SubRegistry_m, Subclasser, AnnotationTarget

# Logging:
logging = logmod.root

# Global Vars:

class BasicEx(SubAnnotate_m):
    pass

class BasicSub(BasicEx):
    pass

class BasicTargeted(SubAnnotate_m, AnnotateTo="blah"):
    pass

##--|

class TestSubClasser_Decoration:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_decorate_name_noop(self):
        match Subclasser.decorate_name(BasicEx):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_decorate_name_with_extras(self):
        target = f"{BasicEx.__name__}<+test>"
        match Subclasser.decorate_name(BasicEx, "test"):
            case str() as x if x == target:
                assert(True)
            case x:
                 assert(False), x

    def test_redecorate_name_with_extras(self):
        target = f"{BasicEx.__name__}<+test>"
        curr = BasicEx.__name__
        for _ in range(10):
            curr = Subclasser.decorate_name(curr, "test")
            assert(curr == target)

    def test_multi_decorate(self):
        target = f"{BasicEx.__name__}<+blah+test>"
        curr = BasicEx.__name__
        for _ in range(10):
            curr = Subclasser.decorate_name(curr, "test", "blah")
            assert(curr == target)

    def test_decorate_param(self):
        target = f"{BasicEx.__name__}[bool]"
        curr = BasicEx.__name__
        for _ in range(10):
            curr = Subclasser.decorate_name(curr, params="bool")
            assert(curr == target)

    def test_decorate_name_override_param(self):
        target = f"{BasicEx.__name__}[int]"
        curr = Subclasser.decorate_name(BasicEx.__name__, params="bool")
        over = Subclasser.decorate_name(curr, params="int")
        assert(over == target)

    def test_decorate_extras_and_params(self):
        target = f"{BasicEx.__name__}<+test>[int]"
        curr = Subclasser.decorate_name(BasicEx.__name__, "test", params="int")
        assert(curr == target)

class TestSubclasser_Making:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic_subclass(self) -> None:
        builder        = Subclasser()
        target  : str  = "TestCls"

        class Basic:
            val : int
            pass

        match builder.make_subclass(target, Basic):
            case type() as x:
                assert(issubclass(x, Basic))
                assert(x.__name__ == target)
                assert(Basic in x.mro())
                inst = x()
                assert(isinstance(inst, x))
                assert(isinstance(inst, Basic))
            case x:
                assert(False), x

    def test_basic_preserves_slots(self) -> None:
        builder        = Subclasser()
        target  : str  = "TestCls"

        class Basic:
            __slots__ = ("val",)

        class ExSub(Basic):
            """ An example subclass the usual way """
            __slots__ = ()

        ex_inst = ExSub()
        assert(not hasattr(ex_inst, "__dict__"))

        match builder.make_subclass(target, Basic):
            case type() as x:
                assert(issubclass(x, Basic))
                assert(x.__name__ == target)
                assert(Basic in x.mro())
                inst = x()
                assert(isinstance(inst, x))
                assert(isinstance(inst, Basic))
                assert(not hasattr(inst, "__dict__"))
            case x:
                assert(False), x

    def test_preserves_annotations(self) -> None:
        builder                = Subclasser()
        target         : str   = "TestCls"
        target_annots  : dict  = {"other": "float"}
        namespace      : dict  = {"__annotations__": target_annots}

        class Basic:
            val : int

        class ExSub(Basic):
            """ A Typically created subclass """
            other : float

        match ExSub.__annotations__:
            case dict() as annots if annots == target_annots:
                # Subclasses don't have their mro annotations
                ex_inst = ExSub()
                assert(ex_inst.__annotations__ == target_annots)
                assert(True)
            case other:
                assert(False), other

        dyn_subclass   = builder.make_subclass(target, Basic, namespace=namespace)
        match dyn_subclass:
            case type() as x:
                assert(x.__annotations__ == target_annots)
                inst = x()
                assert(inst.__annotations__ == target_annots)
            case x:
                assert(False), x

    def test_preserve_classvars(self) -> None:
        builder                = Subclasser()
        target         : str   = "TestCls"
        target_annots  : dict  = {"other":"ClassVar[float]"}
        namespace      : dict  = {
            "__annotations__": target_annots,
            "other" : 0.5,
        }

        class Basic:
            val : ClassVar[int] = 5

        class ExSub(Basic):
            """ A Typically created subclass """
            other : ClassVar[float] = 0.5

        match ExSub.__annotations__:
            case dict() as annots if annots == target_annots:
                # Subclasses don't have their mro annotations
                ex_inst = ExSub()
                assert(ex_inst.__annotations__ == target_annots)
                assert(ExSub.val == 5)
                assert(ExSub.other == 0.5)
                assert(ex_inst.val == 5)
                assert(ex_inst.other == 0.5)
            case other:
                assert(False), other

        dyn_subclass = builder.make_subclass(target, Basic, namespace=namespace)
        match dyn_subclass:
            case type() as x:
                assert(issubclass(x, Basic))
                assert(x.__annotations__ == target_annots)
                inst = x()
                assert(inst.__annotations__ == target_annots)
                assert(x.val == 5)
                assert(x.other == 0.5) # type: ignore[attr-defined]
                assert(inst.val == 5)
                assert(inst.other == 0.5) # type: ignore[attr-defined]
            case x:
                assert(False), x


    def test_classvars_and_slots_and_annotations(self) -> None:
        """ Check a built subclass can have:

        - classvars+values,
        - annotations
        - still no dict
        """

        builder                = Subclasser()
        target         : str   = "TestCls"
        target_annots  : dict  = {"other":"ClassVar[float]"}
        namespace      : dict  = {
            "__annotations__": target_annots,
            "other" : 0.5,
        }

        class Basic:
            __slots__ = ()
            val : ClassVar[int] = 5

        assert(Basic.val == 5)
        assert(not hasattr(Basic(), "__dict__"))
        class ExSub(Basic):
            """ A Typically created subclass """
            __slots__ = ()
            other : ClassVar[float] = 0.5

        assert(ExSub.val == 5)
        assert(ExSub.other == 0.5)
        match ExSub.__annotations__:
            case dict() as annots if annots == target_annots:
                # Subclasses don't have their mro annotations
                ex_inst = ExSub()
                assert(ex_inst.__annotations__ == target_annots)
                assert(ex_inst.val == 5)
                assert(ex_inst.other == 0.5)
                assert(not hasattr(ex_inst, "__dict__")), ex_inst.__dict__
            case other:
                assert(False), other

        dyn_subclass = builder.make_subclass(target, Basic, namespace=namespace)
        match dyn_subclass:
            case type() as x:
                assert(x.__annotations__ == target_annots)
                inst = x()
                assert(inst.__annotations__ == target_annots)
                assert(x.val == 5)
                assert(x.other == 0.5) # type: ignore[attr-defined]
                assert(inst.val == 5)
                assert(inst.other == 0.5) # type: ignore[attr-defined]
                assert(not hasattr(inst, "__dict__")), inst.__dict__
            case x:
                assert(False), x

    def test_pep0560(self):
        """ Check a subclass matches the example in pep0560
        """
        builder = Subclasser()
        class Basic:
            pass

        class Sub(builder.make_generic(Basic, int)):
            pass

        match Sub.__orig_bases__:
            case [val]:
                assert(val.__origin__ is Basic)
                assert(val.__args__ == (int,))
            case x:
                assert(False), x



class TestSubclasser_Annotation:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_annotation(self):
        builder        = Subclasser()

        class Basic:
            __slots__ = ()
            pass

        match builder.annotate(Basic, "test"):
            case type() as x:
                assert(issubclass(x, Basic))
                assert(Basic in x.mro())
                assert(x.__annotations__[AnnotationTarget] == "ClassVar[str]")
                inst = x()
                assert(inst.__annotations__[AnnotationTarget] == "ClassVar[str]")
                assert(not hasattr(inst, "__dict__"))
            case x:
                assert(False), x



class TestAnnotateMixin:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = BasicEx[int]
        assert(issubclass(obj, BasicEx))
        assert(obj.cls_annotation() is int)

    def test_subclass(self):
        obj = BasicSub[int]
        assert(issubclass(obj, BasicEx))
        assert(issubclass(obj, BasicSub))
        assert(obj.cls_annotation() is int)

    def test_idempotent(self):
        obj = BasicSub[int]
        obj2 = BasicSub[int]
        assert(obj is obj2)

class TestAnnotateRegistry:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_registry(self):

        class BasicReg(SubRegistry_m):
            pass

        class BasicSubReg(BasicReg[int]):
            pass

        class BasicSubOther(BasicReg[float]):
            pass

        assert(BasicReg[int] is BasicSubReg)
        assert(BasicReg[float] is not BasicReg[int])
        assert(int in BasicReg._registry)
        assert(BasicReg._registry is BasicSubReg._registry)
