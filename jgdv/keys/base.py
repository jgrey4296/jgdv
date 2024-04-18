#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
printer = logmod.getLogger("doot._printer")
##-- end logging

import decorator
import abc
import string
from tomlguard import TomlGuard

from jgdv.utils.chain_get import ChainedKeyGetter

KEY_PATTERN                                = doot.constants.patterns.KEY_PATTERN
MAX_KEY_EXPANSIONS                         = doot.constants.patterns.MAX_KEY_EXPANSIONS
STATE_TASK_NAME_K                          = doot.constants.patterns.STATE_TASK_NAME_K

PATTERN        : Final[re.Pattern]         = re.compile(KEY_PATTERN)
FAIL_PATTERN   : Final[re.Pattern]         = re.compile("[^a-zA-Z_{}/0-9-]")
KEYS_HANDLED   : Final[str]                = "_doot_keys_handler"
ORIG_ARGS      : Final[str]                = "_doot_orig_args"
KEY_ANNOTS     : Final[str]                = "_doot_keys"
EXPANSION_HINT : Final[str]                = "_doot_expansion_hint"
HELP_HINT      : Final[str]                = "_doot_help_hint"
FUNC_WRAPPED   : Final[str]                = "__wrapped__"

class JGDVBaseKey(abc.ABC):
    """ A shared, non-functional base class for keys and variants like MultiKey.
      Use JGDVBaseKey.build for constructing keys
      build takes an 'exp_hint' kwarg dict, which can specialize the expansion

      JGDVSimpleKeys are strings, wrapped in {} when used in toml.
      so JGDVBaseKey.build("blah") -> JGDVSimpleKey("blah") -> JGDVSimpleKey('blah').form =="{blah}" -> [toml] aValue = "{blah}"

      JGDVMultiKeys are containers of a string `value`, and a list of SimpleKeys the value contains.
      So JGDVBaseKey.build("{blah}/{bloo}") -> JGDVMultiKey("{blah}/{bloo}", [JGDVSimpleKey("blah", JGDVSimpleKey("bloo")]) -> .form == "{blah}/{bloo}"
    """
    dec   = KWrapper
    kwrap = KWrapper

    @staticmethod
    def build(s:str|JGDVBaseKey|pl.Path|dict, *, strict=False, explicit=False, exp_hint:str|dict=None, help=None) -> JGDVBaseKey:
        """ Make an appropriate JGDVBaseKey based on input value
          Can only create MultiKeys if strict = False,
          if explicit, only keys wrapped in {} are made, everything else is returned untouched
          if strict, then only simple keys can be returned
        """
        # TODO annotate with 'help'
        # TODO store expansion args on build
        match exp_hint:
            case "path":
                is_path = True
            case {"expansion": "path"}:
                is_path = True
            case _:
                is_path = False
        result = s
        match s:
            case { "path": x }:
                result = JGDVPathMultiKey(x)
                exp_hint = "path"
            case pl.Path():
                result = JGDVPathMultiKey(s)
                exp_hint = "path"
            case JGDVSimpleKey() if strict:
                result = s
            case JGDVBaseKey():
                result = s
            case str() if not (s_keys := PATTERN.findall(s)) and not explicit and not is_path:
                result = JGDVSimpleKey(s)
            case str() if is_path and not bool(s_keys):
                result = JGDVPathSimpleKey(s)
            case str() if is_path and len(s_keys) == 1 and s_keys[0] == s[1:-1]:
                result = JGDVPathSimpleKey(s[1:-1])
            case str() if is_path and len(s_keys) > 1:
                result = JGDVPathMultiKey(s)
            case str() if not s_keys and explicit:
                result = JGDVNonKey(s)
            case str() if len(s_keys) == 1 and s_keys[0] == s[1:-1]:
                result = JGDVSimpleKey(s[1:-1])
            case str() if not strict:
                result = JGDVMultiKey(s)
            case _:
                raise TypeError("Bad Type to build a Doot Key Out of", s)

        if exp_hint is not None:
            result.set_expansion_hint(exp_hint)

        return result

    def set_help(self, help:str):
        setattr(self, HELP_HINT, help)

    def set_expansion_hint(self, etype:str|dict):
        match etype:
            case "str" | "path" | "type" | "redirect" | "redirect_multi":
                setattr(self, EXPANSION_HINT, {"expansion": etype, "kwargs": {}})
            case {"expansion": str(), "kwargs": dict()}:
                setattr(self, EXPANSION_HINT, etype)
            case _:
                raise doot.errors.DootKeyError("Bad Key Expansion Type Declared", self, etype)

    def __call__(self, spec, state):
        """ Expand the key using the registered expansion hint """
        match getattr(self, EXPANSION_HINT, False):
            case False:
                raise doot.errors.DootKeyError("No Default Key Expansion Type Declared", self)
            case {"expansion": "str", "kwargs": kwargs}:
                return self.expand(spec, state, **kwargs)
            case {"expansion": "path", "kwargs": kwargs}:
                return self.to_path(spec, state, **kwargs)
            case {"expansion" : "type", "kwargs" : kwargs}:
                return self.to_type(spec, state, **kwargs)
            case {"expansion": "redirect"}:
                return self.redirect(spec)
            case {"expansion": "redirect_multi"}:
                return self.redirect_multi(spec)
            case {"expansion": "coderef"}:
                return self.to_coderef(spec, state)
            case x:
                raise doot.errors.DootKeyError("Key Called with Bad Key Expansion Type", self, x)

    @property
    def form(self) -> str:
        return str(self)

    @property
    def direct(self):
        return str(self).removesuffix("_")

    @property
    def is_indirect(self) -> bool:
        return False

    def redirect(self, spec=None) -> JGDVBaseKey:
        return self

    def to_path(self, spec=None, state=None, chain:list[JGDVBaseKey]=None, locs:JGDVLocations=None, on_fail:None|str|pl.Path|JGDVBaseKey=Any, symlinks=False) -> pl.Path:
        """
          Convert a key to an absolute path, using registered locations

          The Process is:
          1) redirect the given key if necessary
          2) Expand each part of the keypath, using JGDVFormatter
          3) normalize it

          If necessary, a fallback chain, and on_fail value can be provided
        """
        locs                 = locs or doot.locs
        key : pl.Path        = pl.Path(self.redirect(spec).form)

        try:
            expanded         : list       = [JGDVFormatter.fmt(x, _spec=spec, _state=state, _rec=True, _locs=locs) for x in key.parts]
            expanded_as_path : pl.Path    = pl.Path().joinpath(*expanded) # allows ("a", "b/c") -> "a/b/c"

            if bool(matches:=PATTERN.findall(str(expanded_as_path))):
                raise doot.errors.DootLocationExpansionError("Missing keys on path expansion", matches, self)

            return locs.normalize(expanded_as_path, symlinks=symlinks)

        except doot.errors.DootLocationExpansionError as err:
            if bool(chain):
                return chain[0].to_path(spec, state, chain=chain[1:], on_fail=on_fail, symlinks=symlinks)
            match on_fail:
                case None:
                    return None
                case JGDVBaseKey():
                    return on_fail.to_path(spec, state, symlinks=symlinks)
                case pl.Path() | str():
                    return locs.normalize(pl.Path(on_fail),  symlinks=symlinks)
                case _:
                    raise err

    def within(self, other:str|dict|TomlGuard) -> bool:
        return False

    def basic(self, spec:SpecStruct_p, state, locs=None):
        """ the most basic expansion of a key """
        kwargs = spec.params
        return ChainedKeyGetter.chained_get(str(self), kwargs, state, locs or doot.locs)

    @abc.abstractmethod
    def to_type(self, spec, state, type_=Any, chain:list[JGDVBaseKey]=None, on_fail=Any, **kwargs) -> Any:
        raise NotImplementedError()

    @abc.abstractmethod
    def expand(self, spec=None, state=None, *, rec=False, insist=False, chain:list[JGDVBaseKey]=None, on_fail=Any, locs:JGDVLocations=None, **kwargs) -> str:
        pass

    def to_coderef(self, spec:None|SpecStruct_p, state) -> None|JGDVCodeReference:
        match spec:
            case SpecStruct_p():
                kwargs = spec.params
            case None:
                kwargs = {}

        redir = self.redirect(spec)

        if redir not in kwargs and redir not in state:
            return None
        try:
            expanded = self.expand(spec, state)
            ref = JGDVCodeReference.build(expanded)
            return ref
        except doot.errors.DootError:
            return None

