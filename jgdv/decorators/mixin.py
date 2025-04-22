
#!/usr/bin/env python3
"""

"""
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
import types
import typing
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

from jgdv.debugging import TraceBuilder
from .core import MonotonicDec, IdempotentDec, Decorator, DataDec
from jgdv.mixins.annotate import Subclasser

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, TypeAliasType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from types import resolve_bases, FunctionType, MethodType

if TYPE_CHECKING:
    from ._interface import Decorated
    from ._interface import Decorable, DForm_e
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--| Global Vars:
MIXIN_KWD : Final[str] = "_jgdv_mixins"
ABSMETHS  : Final[str] = "__abstractmethods__"
IS_ABS    : Final[str] = "__isabstractmethod__"
NAME_MOD  : Final[str] = "M"
##--| Funcs

##--| Body

class Mixin(MonotonicDec):
    """ Decorator to App/Prepend Mixins into the decorated class.

    Converts::

        class ClsName(mixins, Supers, Protocols, metaclass=MCls, **kwargs):...

    into::

        @Protocols(*ps)
        @Mixin(*ms, None)
        class ClsName(Supers): ...


    ('None' is used to separate pre and post mixins)
"""

    needs_args = True

    def __init__(self, *mixins:Maybe[type], allow_inheritance:bool=False, silent:bool=False) -> None:
        super().__init__()
        self._silent = silent
        self._name_mod = NAME_MOD
        try:
            index = mixins.index(None)
        except ValueError:
            index = 0
        finally:
            self._pre_mixins  = [x for x in mixins[:index] if x is not None]
            self._post_mixins = [x for x in mixins[index:] if x is not None]
            if not allow_inheritance:
                self._validate_mixins()


    def _validate_mixins(self) -> None:
        for x in itz.chain(self._pre_mixins, self._post_mixins):
            if len(x.mro()) > 3:  # noqa: PLR2004
                msg = "Can't Mixin a class that inherits anything"
                raise TypeError(msg, x)

    def _build_annotations_h(self, target:Decorable, current:list) -> Maybe[list]:  # noqa: ARG002
        """ Given a list of the current annotation list,
        return its replacement
        """
        new_mixins = current[:]
        new_mixins  = [x for x in self._pre_mixins if x not in current]
        new_mixins += [x for x in self._post_mixins  if x not in current]
        return new_mixins

    def _validate_target_h(self, target:Decorable, form:DForm_e, args:Maybe[list]=None) -> None:  # noqa: ARG002
        match target:
            case type() if hasattr(target, "model_fields"):
                msg = "Pydantic classes shouldn't be extended"
                raise TypeError(msg, target)
            case type():
                pass
            case _:
                msg = "Unexpected type passed for mixin annotation"
                raise TypeError(msg, target)

    def _wrap_class_h(self, cls:Decorable) -> Decorated:
        assert(isinstance(cls, type))
        match cls.mro():
            case [x, *xs]:
                new_mro = [*self._pre_mixins, x, *self._post_mixins, *xs]
            case _:
                pass
        match self._silent:
            case False:
                new_name  = Subclasser.decorate_name(cls, self._name_mod)
            case True:
                new_name = cls.__name__
        mixed     = Subclasser.make_subclass(new_name, cls, mro=new_mro)
        self.annotate_decorable(mixed)
        return mixed


class DelayMixin(DataDec):
    """ TODO A Decorator for annotating a class with mixins

    Delays the construction of the True class until later,
    using @MixinNow
    """
    pass

class MixinNow(MonotonicDec):
    """ TODO The trigger for delayed mixins.

    After using @DelayMixin,
    trigger the True class using this.

    eg::

        @MixinNow
        @DelayMixin(m3, None, m4)
        @DelayMixin(m1, m2)
        class Blah:...

    """
    pass
