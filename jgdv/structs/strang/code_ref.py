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
from typing import Generic, NewType, Any, Never, Union
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from collections.abc import Callable

UnionTypes = types.UnionType | type(Union[int,None])  # noqa: UP007
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

    type CheckType    = type | types.UnionType
    type CheckCancel  = Literal[False]
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

ProtoMeta             : Final[type] = type(Protocol)

TooManyTypesToCheck   : Final[str] = "Too many types to check"
SpecialTypeCheckFail  : Final[str] = "Checking Special Types like generics is not supported yet"
##--|

class CodeReference(Strang, no_register=True):
    """ A reference to a class or function.

    can be created from a string (so can be used from toml),
    or from the actual object (from in python)

    Has the form::

        [cls::]module.a.b.c:ClassName

    Can be built with an imported value directly, and a type to check against

    __call__ imports the reference
    """
    __slots__                                 = ("_check", "_value")

    _processor  : ClassVar                    = StrangBasicProcessor()
    _formatter  : ClassVar                    = StrangFormatter()
    _sections   : ClassVar                    = API.Sections_d(*API.CODEREF_DEFAULT_SECS)
    _check      : Maybe[CheckType]

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
            case x:
                raise TypeError(type(x))
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


    def __init__(self, *args:Any, value:Maybe=None, check:Maybe[CheckType|CheckCancel]=None, **kwargs:Any) -> None:  # noqa: ANN401, ARG002
        super().__init__(**kwargs)
        self._value = value
        match check:
            case False:
                self._check = None
            case None:
                self._check = self.expects_type()
            case type() | types.UnionType():
                self._check = check
            case x:
                raise TypeError(type(x))

    def __call__(self, *, check:Maybe[CheckType|CheckCancel]=None, raise_error:bool=False) -> Result[type, ImportError]:
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

    def _do_import(self, *, check:Maybe[CheckType|CheckCancel]=None) -> Any:  # noqa: ANN401
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

    def _check_imported_type(self, check:Maybe[CheckType|CheckCancel]=None) -> None:
        marks        : Maybe[type[API.StrangMarkAbstract_e]]
        check_target : Maybe[CheckType]
        is_callable  : bool
        is_type      : bool

        if self._value is None:
            return

        marks        = self.section(0).marks
        assert(marks is not None)
        is_callable  = callable(self._value)
        is_type      = isinstance(self._value, type)
        check_target = self.expects_type(check)

        if marks.fn in self and not is_callable:  # type: ignore[attr-defined]
            raise ImportError(errors.CodeRefImportNotCallable, self._value, self)

        if marks.cls in self and not is_type: # type: ignore[attr-defined]
            raise ImportError(errors.CodeRefImportNotClass, self._value, self)

        if marks.value in self and (is_type or is_callable):
            raise ImportError(errors.CodeRefImportNotValue, self._value, self)

        match check_target, self._value:
            case None, _:
                return
            case x, type() as val if isinstance(x, type|UnionTypes) and x is not None and issubclass(val, x):
                return
            case type() | types.UnionType(), val if isinstance(val, check_target):
                return
            case _:
                raise ImportError(errors.CodeRefImportUnknownFail, self, check_target)

    def to_alias(self, group:str, plugins:dict|ChainGuard) -> str:
        """ TODO Given a nested dict-like, see if this reference can be reduced to an alias """
        base_alias = str(self)
        match [x for x in plugins[group] if x.value == base_alias]:
            case [x, *_]:
                base_alias = x.name

        return base_alias

    def to_uniq(self, *args:str) -> Never:
        raise NotImplementedError(errors.CodeRefUUIDFail)

    def expects_type(self, *args:Maybe[CheckType|CheckCancel]) -> Maybe[CheckType]:
        match self.cls_annotation(), args:
            case _, [False] | False:
                return None
            case [types.UnionType()|type() as check_type], [*xs]: # Merge types to check
                return cast("types.UnionType", Union[check_type, *[x for x in xs if x]])
            case [types.UnionType()|type() as check_type]: # Use annotation
                return check_type
            case [x, *xs], _: # Too many
                raise ImportError(TooManyTypesToCheck, x, xs)
            case _: # Nothing
                return None
