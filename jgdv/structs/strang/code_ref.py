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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from pydantic import field_validator, model_validator
import importlib
from importlib.metadata import EntryPoint
from tomlguard import TomlGuard
from . import Strang

class CodeReference(Strang):
    """
      A reference to a class or function. can be created from a string (so can be used from toml),
      or from the actual object (from in python)

    has the form module.a.b.c:ClassName

    Can be built with an imported value directly, and a type to check against
    __call__ imports the reference
    """

    _separator       : ClassVar[str]                    = ":"
    _value           : None|type                        = None

    def __init__(self, *, value:None|type=None, check:None|type=None):
        super().__init__()
        self._value = value

    def __repr__(self) -> str:
        code_path = str(self)
        return f"<CodeRef: {code_path}>"

    @ftz.cached_property
    def module(self):
        return self[0:]

    @ftz.cached_property
    def value(self) -> str:
        return self[1:]

    def __call__(self, *, check:type=Any) -> type|ImportError:
        """ Tries to import and retrieve the reference,
        and casts errors to ImportErrors
        """
        match self._value:
            case None:
                try:
                    mod = importlib.import_module(self.module)
                    curr = mod
                    for name in self.body():
                        curr = getattr(curr, name)
                except ImportError as err:
                    return err
                except AttributeError as err:
                    return ImportError("Attempted import failed, attribute not found", str(self), name)
                else:
                    self._value = curr
            case _:
                pass

        if not callable(self._value):
            return ImportError("Imported value was not a callable or type", self._value, self)

        match self._typevar:
            case None:
                pass
            case type() as the_type if not issubclass(self._value, the_type):
                return ImportError("Imported Value does not match required type", the_type, self._value)

        match check:
            case x if x is Any:
                return curr
            case x if not (isinstance(curr, x) or issubclass(curr, check)):
                return ImportError("Imported Code Reference is not of correct type", self, ensure)

        Never()

    def to_alias(self, group:str, plugins:dict|TomlGuard) -> tuple[str, list[str]]:
        """ Given a nested dict-like, see if this reference can be reduced to an alias """
        base_alias = str(self)
        match [x for x in plugins[group] if x.value == base_alias]:
            case [x, *xs]:
                base_alias = x.name

        if group != "mixins":
            mixins = [x.to_aliases("mixins", plugins)[0] for x in  self._calculate_minimal_mixins(plugins)]
        else:
            mixins = []

        return base_alias, mixins

    def to_uniq(self):
        raise NotImplementedError("Code References shouldn't need UUIDs")

    def with_head(self):
        raise NotImplementedError("Code References shouldn't need $head$s")
