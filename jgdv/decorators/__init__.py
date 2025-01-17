"""

"""
from __future__ import annotations
import typing

# ##-- types
# isort: off
if typing.TYPE_CHECKING:
   from jgdv import Maybe, Ident
   from typing import ClassVar
   from jgdb._abstract.protocols import Decorator_p
# isort: on
# ##-- end types

from .core import DecoratorBase, _TargetType_e
from .meta_decorator import MetaDecorator
from .data_decorator import DataDecorator

class DecoratorAccessor_m:
    """ A mixin for building Decorator Accessors like DKeyed.
    Holds a _decoration_builder class, and helps you build it
    """

    _decoration_builder : ClassVar[type] = DataDecorator

    @classmethod
    def _build_decorator(cls, keys) -> Decorator_p:
        return cls._decoration_builder(keys)

    @classmethod
    def get_keys(cls, fn) -> list[Ident]:
        """ Retrieve key annotations from a decorated function """
        dec = cls._build_decorator([])
        return dec.get_annotations(fn)
