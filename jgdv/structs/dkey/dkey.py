#!/usr/bin/env python3
"""

"""
# ruff: noqa: ARG002

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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
# ##-- end stdlib imports

from collections import ChainMap
from jgdv import Proto, Mixin
from jgdv.mixins.annotate import SubAlias_m
from jgdv.structs.strang import Strang
from ._util import _interface as ExpAPI # noqa: N812
from ._util.expander import DKeyExpander
from .processor import DKeyProcessor

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol
from . import _interface as API # noqa: N812

if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe, M_
    from ._util._interface import Expander_p


# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
CLASS_GETITEM_K : Final[str] = "__class_getitem__"
# Body:

@Proto(API.Key_p, check=False, mod_mro=False)
class DKey[**K](Strang, fresh_registry=True):
    """ A facade for DKeys and variants.
      Implements __new__ to create the correct key type, from a string, dynamically.

      kwargs:
      explicit = insists that keys in the string are wrapped in braces '{akey} {anotherkey}'.
      mark     = pre-register expansion parameters / type etc
      check    = dictate a type that expanding this key must match
      fparams  = str formatting instructions for the key

      Eg:
      DKey('blah')
      -> SingleDKey('blah')
      -> SingleDKey('blah').format('w')
      -> '{blah}'
      -> [toml] aValue = '{blah}'

      Because cls.__new__ calls __init__ automatically for return values of type cls,
      DKey is the factory, but all DKeys are subclasses of DKeyBase,
      to allow control over __init__.

      Base class for implementing actual DKeys.

      init takes kwargs:
      fmt, mark, check, ctor, help, fallback, max_exp

      on class definition, can register a 'mark', 'multi', and a conversion parameter str
    """
    __slots__                                              = ("data",)
    __match_args                                           = ()
    _annotate_to    : ClassVar[str]                        = "dkey_mark"
    _processor      : ClassVar                             = DKeyProcessor()
    _sections       : ClassVar                             = API.DKEY_SECTIONS
    _expander       : ClassVar[Expander_p]                 = DKeyExpander()
    _typevar        : ClassVar                             = None
    _extra_kwargs   : ClassVar[set[str]]                   = set()
    _extra_sources  : ClassVar[list[ExpInst.SourceBases]]  = []
    Marks           : ClassVar[API.DKeyMarkAbstract_e]     = API.DKeyMark_e  # type: ignore[assignment]
    data            : API.DKey_d

    ##--| Class Utils

    @final
    @staticmethod
    def MarkOf[T](target:T|type[T]) -> API.KeyMark|tuple[API.KeyMark, ...]: # noqa: N802
        """ Get the mark of the key type or instance """
        if not hasattr(target, "cls_annotation"):
            return ()
        match target.cls_annotation(): # type: ignore[union-attr]
            case None:
                return ()
            case [x]:
                return x
            case xs:
                return xs

    @classmethod
    def add_sources(cls, *sources:dict) -> None:
        """ register additional sources that are always included in expansion """
        cls._extra_sources += sources


    def __init_subclass__(cls, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init_subclass__(*args, annotation=kwargs.pop("mark", None), **kwargs)
        cls._expander.set_ctor(DKey) # type: ignore[arg-type]
        cls._processor.register_convert_param(cls, kwargs.pop("convert", None))


    ##--| Class Main

    def __init__(self, *args:Any, **kwargs:Any) -> None:  # noqa: ANN401
        assert(not self.endswith(API.INDIRECT_SUFFIX)), self[:]
        super().__init__(*args, **kwargs)
        self.data = API.DKey_d(**kwargs)

    def __call__(self, *args:Any, **kwargs:Any) -> Any:  # noqa: ANN401
        """ call expand on the key.
        Args and kwargs are passed verbatim to expand()
        """
        return self.expand(*args, **kwargs)

    def __eq__(self, other:object) -> bool:
        match other:
            case DKey() | str():
                return str.__eq__(self, other)
            case _:
                return NotImplemented


    def __hash__(self) -> int:
        return hash(self[:])

    def __format__(self, spec:str) -> str:
        """
          Extends standard string format spec language:
            [[fill]align][sign][z][#][0][width][grouping_option][. precision][type]
            (https://docs.python.org/3/library/string.html#format-specification-mini-language)

          Using the # alt form to declare keys are wrapped.
          eg: for key = DKey('test'), ikey = DKey('test_')
          f'{key}'   -> 'test'
          f'{key:w}' -> '{test}'
          f'{key:i}  ->  'test_'
          f'{key:wi} -> '{test_}'

          f'{ikey:d} -> 'test'

        """
        result = self[:]
        if not bool(spec):
            return result

        rem, wrap, direct = self._processor.consume_format_params(spec) # type: ignore

        # format
        if not direct:
            result = f"{result}{API.INDIRECT_SUFFIX}"

        if wrap:
            result = "".join(["{", result, "}"])  # noqa: FLY002

        return result
    ##--| Utils

    def var_name(self) -> str:
        """ When testing the dkey for its inclusion in a decorated functions signature,
        this gives the 'named' val if its not None, otherwise the str of the key
        """
        return self.data.name or str(self)

    def expand(self, *args:Any, **kwargs:Any) -> Maybe:  # noqa: ANN401
        kwargs.setdefault("limit", self.data.max_expansions)
        assert(isinstance(self, API.Key_p))
        match self._expander.expand(self, *args, **kwargs):
            case ExpAPI.ExpInst_d(value=val, literal=True):
                return val
            case _:
                return None

    def redirect(self, *args:Any, **kwargs:Any) -> list[API.Key_p]:  # noqa: ANN401
        assert(isinstance(self, API.Key_p))
        result = [DKey(x.value) for x in self._expander.redirect(self, *args, **kwargs) if x is not None]
        return result


    ##--| expansion hooks
    def to_exp_inst(self, *, indirect:bool=False, **kwargs) -> ExpAPI.ExpInst_d:
        """ create a basic expinst """
        val = f"{self:i}" if indirect else f"{self:d}"
        return ExpAPI.ExpInst_d(value=val,
                                convert=self.data.convert,
                                rec=self.data.max_expansions,
                                **kwargs,
                                )

    def exp_extra_sources_h(self, current:ExpInst.SourceChain_d) -> ExpInst.SourceChain_d:
        new_sources : Any
        match self._extra_sources:
            case [*xs]:
                return current.extend(*xs)
            case x:
                raise TypeError(type(x))
