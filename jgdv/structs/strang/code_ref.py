#!/usr/bin/env python3
"""

"""
# mypy: disable-error-code="misc"
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import functools as ftz
import importlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from importlib.metadata import EntryPoint
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from pydantic import field_validator, model_validator

# ##-- end 3rd party imports

# ##-- 1st party imports
from .strang import Strang
from ._interface import CodeRefMeta_e
# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
import typing
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Any, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv.structs.chainguard import ChainGuard
    import enum
    from jgdv import Maybe, Result
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type SpecialType = typing._SpecialForm
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class CodeReference(Strang):
    """ A reference to a class or function.

    can be created from a string (so can be used from toml),
    or from the actual object (from in python)

    Has the form::

        [cls::]module.a.b.c:ClassName

    Can be built with an imported value directly, and a type to check against

    __call__ imports the reference
    """

    _value            : Maybe[type]                        = None
    _separator        : ClassVar[str]                      = "::"
    _tail_separator   : ClassVar[str]                      = ":"
    _body_types       : ClassVar[Any]                      = str
    gmark_e           : ClassVar[type[CodeRefMeta_e]]     = CodeRefMeta_e

    _value_idx        : slice

    @classmethod
    def from_value(cls:type[CodeReference], value:Any) -> CodeReference:  # noqa: ANN401
        split_qual = value.__qualname__.split(".")
        val_iden = ":".join([".".join(split_qual[:-1]), split_qual[-1]])
        return cls(f"{value.__module__}:{val_iden}", value=value)

    @classmethod
    def pre_process(cls, data:str, *, strict:bool=False) -> str:  # noqa: ARG003
        match data:
             case Strang():
                 pass
             case str() if cls._separator not in data:
                 data = f"{cls.gmark_e.default}{cls._separator}{data}"  # type: ignore[attr-defined]
             case _:
                 pass

        return super().pre_process(data)

    def _post_process(self) -> None:
        for elem in self.group:
            self._group_meta.add(self.gmark_e[elem])

        # Modify the last body slice
        last_slice = self._body.pop()
        last       = str.__getitem__(self, last_slice)
        if self._tail_separator not in last:
            msg = "CodeRef didn't have a final value"
            raise ValueError(msg, last, str.__str__(self))

        index = last.index(self._tail_separator)
        self._body.append(slice(last_slice.start, last_slice.start + index))
        self._value_idx = slice(last_slice.start+index+1, last_slice.stop)

    def __init__(self, *_:Any, value:Maybe[type]=None, check:Maybe[type]=None, **kwargs:Any) -> None:  # noqa: ANN401, ARG002
        super().__init__(**kwargs)
        self._value = value

    def __repr__(self) -> str:
        code_path = str(self)
        return f"<CodeRef: {code_path}>"

    def __call__(self, *, check:SpecialType|type=Any, raise_error:bool=False) -> Result[type, ImportError]:
        """ Tries to import and retrieve the reference,
        and casts errors to ImportErrors
        """
        if self._value is not None:
            return self._value
        try:
            return self._do_import(check=check)
        except ImportError as err:
            if raise_error:
                raise
            return err

    def _do_import(self, *, check:Maybe[SpecialType|type]) -> Any:  # noqa: ANN401, PLR0912
        match self._value:
            case None:
                try:
                    mod = importlib.import_module(self.module)
                    curr = getattr(mod, self.value)
                except ModuleNotFoundError as err:
                    err.add_note(f"Origin: {self}")
                    raise
                except AttributeError as err:
                    msg = "Attempted import failed, attribute not found"
                    raise ImportError(msg, str(self), self.value, err.args) from None
                else:
                    self._value = curr
            case _:
                curr = self._value

        has_mark     = any(x in self for x in [self.gmark_e.fn, self.gmark_e.cls])  # type: ignore[attr-defined]
        is_callable  = callable(self._value)
        is_type      = isinstance(self._value, type)
        if not has_mark:
            pass
        elif self.gmark_e.fn in self and not is_callable:  # type: ignore[attr-defined]
            msg = "Imported 'Function' was not a callable"
            raise ImportError(msg, self._value, self)
        elif self.gmark_e.cls in self and not is_type:
            msg = "Imported 'Class' was not a type"
            raise ImportError(msg, self._value, self)

        match self._typevar:
            case None:
                pass
            case type() as the_type if not issubclass(self._value, the_type):
                msg = "Imported Value does not match required type"
                raise ImportError(msg, the_type, self._value)

        match check:
            case None:
                return curr
            case typing._SpecialForm():
                return curr
            case x if x is Any:
                return curr
            case type() as x if not (isinstance(curr, x) or issubclass(curr, x)):
                msg = "Imported Code Reference is not of correct type"
                raise ImportError(msg, self, check)

        raise RuntimeError()

    @property
    def module(self) -> str:
        return self[1::-1]


    @property
    def value(self) -> str:
        return str.__getitem__(self, self._value_idx)

    def to_alias(self, group:str, plugins:dict|ChainGuard) -> str:
        """ TODO Given a nested dict-like, see if this reference can be reduced to an alias """
        base_alias = str(self)
        match [x for x in plugins[group] if x.value == base_alias]:
            case [x, *_]:
                base_alias = x.name

        return base_alias

    def to_uniq(self) -> Never:
        msg = "Code References shouldn't need UUIDs"
        raise NotImplementedError(msg)

    def with_head(self) -> Never:
        msg = "Code References shouldn't need $head$s"
        raise NotImplementedError(msg)
