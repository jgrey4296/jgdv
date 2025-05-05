"""
Idenpotent Decorators, as an extendable class

Key Classes:
- DecoratorBase : Simplifies decorations to writing a _wrap_[method/fn/class] method.
- MetaDecorator : Adds metadata to callable, without changing the behaviour of it.
- DataDecorator : Stacks data onto the callable, with only one wrapping function

"""
from __future__ import annotations
import typing

# ##-- types
# isort: off
if typing.TYPE_CHECKING:
   from jgdv import Maybe, Ident
   from typing import ClassVar
# isort: on
# ##-- end types

from ._interface import Signature, Decorable, Decorated, DForm_e, Decorator_p
from ._core import Decorator, MonotonicDec, IdempotentDec, MetaDec, DataDec
from .mixin import Mixin
from .proto import Proto
from .util_decorators import DoMaybe

class DecoratorAccessor_m:
    """ A mixin for building Decorator Accessors like DKeyed.
    Holds a _decoration_builder class, and helps you build it
    """

    _decoration_builder : ClassVar[type[Decorator]] = DataDec

    @classmethod
    def _build_decorator(cls, keys) -> Decorator_p:
        return cls._decoration_builder(keys)

    @classmethod
    def get_keys(cls, target:Decorated) -> list[Ident]:
        """ Retrieve key annotations from a Decorated"""
        dec = cls._build_decorator([])
        return dec.get_annotations(target)
