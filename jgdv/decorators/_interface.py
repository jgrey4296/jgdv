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

# ##-- Generated Exports
__all__ = ( # noqa: RUF022
# -- Types
"Decorable", "Decorated", "Signature",
# -- Classes
"DForm_e", "Decorator_p",

)
# ##-- end Generated Exports

##--| Util Types
from jgdv._abstract.types import Func, Method

##--| Primary Types
type Signature                = inspect.Signature
type Decorable                = type | Func | Method
type Decorated[F:Decorable]   = F

##--| Val
WRAPPED             : Final[str]  = "__wrapped__"
ANNOTATIONS_PREFIX  : Final[str]  = "__JGDV__"
MARK_SUFFIX         : Final[str]  = "_mark"
DATA_SUFFIX         : Final[str]  = "_data"
ATTR_TARGET         : Final[str]  = "__annotations__"

class DForm_e(enum.Enum):
    """ This is necessary because you can't use Callable or MethodType
    in match statement
    """

    CLASS    = enum.auto()
    FUNC     = enum.auto()
    METHOD   = enum.auto()

##--|

class DecoratorHooks_p(Protocol):

    def _wrap_method_h[**In, Out](self, meth:Method[In,Out]) -> Decorated[Method[In, Out]]: ...

    def _wrap_fn_h[**In, Out](self, fn:Func[In, Out]) -> Decorated[Func[In, Out]]: ...

    def _wrap_class_h(self, cls:type) -> Maybe[Decorated]: ...

    def _validate_target_h(self, target:Decorable, form:DForm_e, args:Maybe[list]=None) -> None: ...

    def _validate_sig_h(self, sig:Signature, form:DForm_e, args:Maybe[list]=None) -> None: ...

    def _build_annotations_h(self, target:Decorable, current:list) -> list: ...

class DecoratorUtils_p(Protocol):

    def _decoration_logic(self, target:Decorable) -> Decorated: ...

    def _unwrap(self:Decorator_i, target:Decorated) -> Decorable: ...

    def _unwrapped_depth(self:Decorator_i, target:Decorated) -> int: ...

    def _build_wrapper(self:Decorator_i, form:DForm_e, target:Decorable) -> Maybe[Decorated]: ...

    def _apply_onto(self:Decorator_i, wrapper:Decorated, target:Decorable) -> Decorated: ...

    def _signature(self:Decorator_i, target:Decorable) -> Signature: ...

@runtime_checkable
class Decorator_p(DecoratorHooks_p, DecoratorUtils_p, Protocol):

    def __call__[T:Decorable](self, target:T) -> Maybe[Decorated[T]]: ...

    def data_key(self) -> str: ...

    def mark_key(self) -> str: ...

    def dec_name(self) -> str: ...

    def apply_mark(self, *args:Decorable) -> None: ...

    def annotate_decorable(self, target:Decorable) -> list: ...

    def is_marked(self, target:Decorable) -> bool: ...

    def is_annotated(self, target:Decorable) -> bool: ...

    def get_annotations(self, target:Decorable) -> list[str]: ...

##--| Interface
class Decorator_i(Decorator_p, Protocol):

    Form                 : ClassVar[type[DForm_e]]
    needs_args           : ClassVar[bool]

    _annotation_prefix   : str
    _data_key            : Maybe[str]
    _data_suffix         : str
    _mark_key            : Maybe[str]
    _mark_suffix         : str
    _wrapper_assignments : list[str]
    _wrapper_updates     : list[str]
