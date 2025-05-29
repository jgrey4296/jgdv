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
from . import _interface as API # noqa: N812
from . import errors
from .processor import CodeRefProcessor
from .formatter import StrangFormatter
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

ProtoMeta             : Final[type] = type(Protocol)

SpecialTypeCheckFail  : Final[str] = "Checking Special Types like generics is not supported yet"
##--|

class CodeReference(Strang):
    """ A reference to a class or function.

    can be created from a string (so can be used from toml),
    or from the actual object (from in python)

    Has the form::

        [cls::]module.a.b.c:ClassName

    Can be built with an imported value directly, and a type to check against

    __call__ imports the reference
    """
    __slots__ = ("_value",)

    _processor    : ClassVar          = CodeRefProcessor()
    _formatter    : ClassVar          = StrangFormatter()
    _sections     : ClassVar          = API.Sections_d(*API.CODEREF_DEFAULT_SECS)
    _typevar      : ClassVar          = None

    @classmethod
    def from_value(cls:type[CodeReference], value:Any) -> CodeReference:  # noqa: ANN401
        split_qual = value.__qualname__.split(".")
        val_iden = ":".join([".".join(split_qual[:-1]), split_qual[-1]])
        return cls(f"{value.__module__}:{val_iden}", value=value)


    def __init__(self, *args:Any, value:Maybe[type]=None, check:Maybe[type]=None, **kwargs:Any) -> None:  # noqa: ANN401, ARG002
        super().__init__(**kwargs)
        self._value = value

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

    def _do_import(self, *, check:Maybe[SpecialType|type]) -> Any:  # noqa: ANN401
        match self._value:
            case None:
                try:
                    mod = importlib.import_module(self.module)
                    curr = getattr(mod, self.value)
                except ModuleNotFoundError as err:
                    err.add_note(f"Origin: {self}")
                    raise
                except AttributeError as err:
                    raise ImportError(errors.CodeRefImportFailed, str(self), self.value, err.args) from None
                else:
                    self._value = curr
            case _:
                curr = self._value

        self._check_imported_type(check)
        return self._value

    def _check_imported_type(self, check:Maybe[SpecialType|type]) -> None:  # noqa: PLR0912
        assert(self._value is not None)
        marks        = self.section(0).marks
        assert(marks is not None)
        has_mark     = any(x in self for x in [marks.fn, marks.cls])  # type: ignore[attr-defined]
        is_callable  = callable(self._value)
        is_type      = isinstance(self._value, type)
        if not has_mark:
              pass
        elif marks.fn in self and not is_callable:  # type: ignore[attr-defined]
            raise ImportError(errors.CodeRefImportNotCallable, self._value, self)
        elif marks.cls in self and not is_type: # type: ignore[attr-defined]
            raise ImportError(errors.CodeRefImportNotClass, self._value, self)

        match self._typevar:
            case None:
                pass
            case type() as the_type if not issubclass(self._value, the_type):
                raise ImportError(errors.CodeRefImportCheckFail, the_type, self._value)
        match check:
            case None:
                return
            case types.UnionType() if isinstance(self._value, check): # type: ignore[arg-type]
                return
            case typing._SpecialForm():
                raise NotImplementedError(SpecialTypeCheckFail, check, self._value)
            case x if x is Any:
                return
            case x if issubclass(x, Protocol): # type: ignore[arg-type]
                if isinstance(self._value, x):
                    return
            case type() as x:
                val_match = isinstance(self._value, x)
                val_match |= issubclass(self._value, x)
                if not val_match:
                    raise TypeError(self._value, x)

        raise ImportError(errors.CodeRefImportUnknownFail, self, check)

    def to_alias(self, group:str, plugins:dict|ChainGuard) -> str:
        """ TODO Given a nested dict-like, see if this reference can be reduced to an alias """
        base_alias = str(self)
        match [x for x in plugins[group] if x.value == base_alias]:
            case [x, *_]:
                base_alias = x.name

        return base_alias


    def to_uniq(self, *args:str) -> Never:
        raise NotImplementedError(errors.CodeRefUUIDFail)
