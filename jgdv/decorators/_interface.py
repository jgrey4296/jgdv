## decorators.pyi -*- mode: python -*-
# Type Interface Specification
#
from __future__ import annotations

import enum
# ##-- types
# isort: off
import inspect
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

__all__ = ["Signature", "Decorable", "Decorated", "DForm_e", "Decorator_p"]

##--| Util Types
from jgdv._types import Func, Method

##--| Primary Types
type Signature   = inspect.Signature
type Decorable   = type | Func | Method
type Decorated   = Decorable

class DForm_e(enum.Enum):
    """ This is necessary because you can't use Callable or MethodType
    in match statement
    """

    CLASS    = enum.auto()
    FUNC     = enum.auto()
    METHOD   = enum.auto()

##--|

@runtime_checkable
class Decorator_p(Protocol):

    def __call__(self, target:Decorable) -> Decorated:
        pass

    def _wrap_method_h(self, fn:Func) -> Decorated:
        pass

    def _wrap_fn_h(self, fn:Func) -> Decorated:
        pass

    def _wrap_class_h(self, cls:type) -> Maybe[Decorated]:
        pass

    def _validate_target_h(self, target:Decorable, form:DForm_e, args:Maybe[list]=None) -> None:
        pass

    def _validate_sig_h(self, sig:Signature, form:DForm_e, args:Maybe[list]=None) -> None:
        pass

    def _build_annotations_h(self, target:Decorable, current:list) -> Maybe[list]:
        pass

    def dec_name(self) -> str:
        pass

    def apply_mark(self, *args:Decorable) -> None:
        pass

    def annotate_decorable(self, target:Decorable) -> list:
        pass

    def is_marked(self, target:Decorable) -> bool:
        pass

    def is_annotated(self, target:Decorable) -> bool:
        pass

    def get_annotations(self, target:Decorable) -> list[str]:
        pass
