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
from .processor import StrangBasicProcessor
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
from collections.abc import Callable

if TYPE_CHECKING:
    from jgdv.structs.chainguard import ChainGuard
    import enum
    from jgdv import Maybe, Result, MaybeT
    from typing import Final
    from typing import ClassVar, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv._abstract.pre_processable import PreProcessResult
    type SpecialType  = typing._SpecialForm
    type CheckType    = type | types.UnionType
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
    __slots__                                 = ("_value",)

    _processor  : ClassVar                    = StrangBasicProcessor()
    _formatter  : ClassVar                    = StrangFormatter()
    _sections   : ClassVar                    = API.Sections_d(*API.CODEREF_DEFAULT_SECS)
    _check      : ClassVar[Maybe[CheckType]]  = None

    @classmethod
    def _pre_process_h[T:CodeReference](cls:type[T], input:Any, *args:Any, strict:bool=False, **kwargs:Any) -> MaybeT[bool, *PreProcessResult[T]]:  # noqa: A002, ANN401, ARG003
        inst_data : dict = {}
        post_data : dict = {}
        match input:
            case str():
                full_str = input
            case Callable():
                split_qual = input.__qualname__.split(".")
                val_iden = ":".join([".".join(split_qual[:-1]), split_qual[-1]])
                full_str = f"{input.__module__}:{val_iden}"
                inst_data['value'] = input
        ##--|
        return False, full_str, inst_data, post_data, None

    def __class_getitem__(cls, *args:Any, **kwargs:Any) -> type:  # noqa: ANN401
        match super().__class_getitem__(*args, **kwargs):
            case type() as x:
                return x
            case types.GenericAlias() as alias:
                pass

        match alias.__args__[0]:
            case types.UnionType() as x:
                annotation = str(x)
            case type() as x:
                annotation = x.__name__
            case x:
                raise TypeError(type(x))
        ##--|
        def force_slots(ns:dict) -> None:
            ns['__slots__'] = ()
        newtype = types.new_class(f"{cls.__name__}[{annotation}]", (alias,), exec_body=force_slots)
        return newtype


    def __init__(self, *args:Any, value:Maybe[type]=None, check:Maybe[type]=None, **kwargs:Any) -> None:  # noqa: ANN401, ARG002
        super().__init__(**kwargs)
        self._value = value

    def __call__(self, *, check:Maybe[CheckType]=None, raise_error:bool=False) -> Result[type, ImportError]:
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

    def _do_import(self, *, check:Maybe[CheckType]=None) -> Any:  # noqa: ANN401
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
        ##--|
        self._check_imported_type(check)
        return self._value

    def _check_imported_type(self, check:Maybe[CheckType]=None) -> None:
        if self._value is None:
            return
        marks        : Maybe[type[API.StrangMarkAbstract_e]]
        has_mark     : bool
        is_callable  : bool
        is_type      : bool

        marks        = self.section(0).marks
        assert(marks is not None)
        has_mark     = any(x in self for x in [marks.fn, marks.cls])  # type: ignore[attr-defined]
        is_callable  = callable(self._value)
        is_type      = isinstance(self._value, type)

        match self.cls_annotation():
            case [types.UnionType()|type() as check_type] if check: # Merge types to check
                check |= check_type
            case [types.UnionType()|type() as check_type]: # Use annotation
                check = check_type
            case [x, *xs]: # Too many
                raise ImportError("too many types to check", x, xs)
            case _: # Nothing
                return

        if marks.fn in self and not is_callable:  # type: ignore[attr-defined]
            raise ImportError(errors.CodeRefImportNotCallable, self._value, self)

        if marks.cls in self and not is_type: # type: ignore[attr-defined]
            raise ImportError(errors.CodeRefImportNotClass, self._value, self)

        if marks.value in self and (is_type or is_callable):
            raise ImportError(errors.CodeRefImportNotValue, self._value, self)

        match check, self._value:
            case None, _:
                return
            case type() | types.UnionType(), type() if issubclass(self._value, check):
                return
            case type() | types.UnionType(), _ if isinstance(self._value, check):
                return
            case _:
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
