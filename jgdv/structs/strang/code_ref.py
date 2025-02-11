#!/usr/bin/env python3
"""

"""

##-- builtin imports
from __future__ import annotations

# import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping, Never,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

# ##-- types
# isort: off
if TYPE_CHECKING:
   from jgdv import Maybe
   Enum = enum.Enum

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from pydantic import field_validator, model_validator
import importlib
from importlib.metadata import EntryPoint
from jgdv.structs.chainguard import ChainGuard
from . import Strang
from jgdv import Result

class CodeRefMeta_e(enum.StrEnum):
    module  = "module"
    cls     = "cls"
    value   = "value"
    fn      = "fn"

    val     = "value"
    default = fn

class CodeReference(Strang):
    """
      A reference to a class or function. can be created from a string (so can be used from toml),
      or from the actual object (from in python)

    has the form [cls::]module.a.b.c:ClassName

    Can be built with an imported value directly, and a type to check against
    __call__ imports the reference
    """

    _value            : Maybe[type]                        = None
    _separator        : ClassVar[str]                      = "::"
    _tail_separator   : ClassVar[str]                      = ":"
    _body_types       : ClassVar[Any]                      = str
    gmark_e           : ClassVar[Enum]                     = CodeRefMeta_e

    @classmethod
    def from_value(cls, value):
        return cls(f"{value.__module__}:{value.__qualname__}", value=value)

    @classmethod
    def pre_process(cls, data, strict=False):
        match data:
             case Strang():
                 pass
             case str() if cls._separator not in data:
                 data = f"{cls.gmark_e.default}{cls._separator}{data}"
             case _:
                 pass

        return super().pre_process(data)

    def _post_process(self):
        for elem in self.group:
            self._group_meta.add(self.gmark_e[elem])

        # Modify the last body slice
        last_slice = self._body.pop()
        last       = str.__getitem__(self, last_slice)
        if self._tail_separator not in last:
            raise ValueError("CodeRef didn't have a final value", str.__str__(self))

        index = last.index(self._tail_separator)
        self._body.append(slice(last_slice.start, last_slice.start + index))
        self._value_idx = slice(last_slice.start+index+1, last_slice.stop)


    def __init__(self, *, value:Maybe[type]=None, check:Maybe[type]=None, **kwargs):
        super().__init__(**kwargs)
        self._value = value
        self._value_idx = None

    def __repr__(self) -> str:
        code_path = str(self)
        return f"<CodeRef: {code_path}>"

    @ftz.cached_property
    def module(self):
        return self[1::-1]

    @ftz.cached_property
    def value(self) -> str:
        return str.__getitem__(self, self._value_idx)



    def __call__(self, *, check:type=Any, raise_error=False) -> Result[type, ImportError]:
        """ Tries to import and retrieve the reference,
        and casts errors to ImportErrors
        """
        if self._value is not None:
            return self._value
        try:
            return self._do_import(check)
        except ImportError as err:
            if raise_error:
                raise err
            return err


    def _do_import(self, check):
        match self._value:
            case None:
                try:
                    mod = importlib.import_module(self.module)
                    curr = getattr(mod, self.value)
                except ModuleNotFoundError:
                    raise ImportError("Attempted import failed, module not found", str(self), self.module) from None
                except AttributeError:
                    raise ImportError("Attempted import failed, attribute not found", str(self), self.value) from None
                else:
                    self._value = curr
            case _:
                curr = self._value

        has_mark     = any(x in self for x in [self.gmark_e.fn, self.gmark_e.cls])
        is_callable  = callable(self._value)
        is_type      = isinstance(self._value, type)
        if not has_mark:
            pass
        elif self.gmark_e.fn in self and not is_callable:
            raise ImportError("Imported 'Function' was not a callable", self._value, self)
        elif self.gmark_e.cls in self and not is_type:
            raise ImportError("Imported 'Class' was not a type", self._value, self)

        match self._typevar:
            case None:
                pass
            case type() as the_type if not issubclass(self._value, the_type):
                raise ImportError("Imported Value does not match required type", the_type, self._value)

        match check:
            case x if x is Any:
                return curr
            case x if not (isinstance(curr, x) or issubclass(curr, check)):
                raise ImportError("Imported Code Reference is not of correct type", self, check)

        Never()

    def to_alias(self, group:str, plugins:dict|ChainGuard) -> str:
        """ TODO Given a nested dict-like, see if this reference can be reduced to an alias """
        base_alias = str(self)
        match [x for x in plugins[group] if x.value == base_alias]:
            case [x, *_]:
                base_alias = x.name

        return base_alias

    def to_uniq(self):
        raise NotImplementedError("Code References shouldn't need UUIDs")

    def with_head(self):
        raise NotImplementedError("Code References shouldn't need $head$s")
