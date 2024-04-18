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
# import more_itertools as mitz
# from boltons import
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv.utils.chain_get import ChainedKeyGetter

class JGDVNonKey(str, JGDVBaseKey):
    """
      Just a string, not a key. But this lets you call no-ops for key specific methods
    """

    def __repr__(self):
        return "<JGDVNonKey: {}>".format(str(self))

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        match other:
            case JGDVBaseKey() | str():
                return str(self) == str(other)
            case _:
                return False

    def within(self, other:str|dict|TomlGuard) -> bool:
        match other:
            case str():
                return self.form in other
            case dict() | TomlGuard():
                return self in other
            case _:
                raise TypeError("Uknown JGDVBaseKey target for within", other)

    @property
    def indirect(self) -> JGDVBaseKey:
        if not self.is_indirect:
            return JGDVSimpleKey("{}_".format(super().__str__()))
        return self

    @property
    def is_indirect(self):
        return False

    @property
    def form(self):
        """ Return the key in its use form """
        return str(self)

    def expand(self, spec=None, state=None, *, rec=False, insist=False, chain:list[JGDVBaseKey]=None, on_fail=Any, locs:DootLocations=None, **kwargs) -> str:
        return str(self)

    def redirect(self, spec=None) -> JGDVBaseKey:
        return self

    def to_type(self, spec, state, type_=Any, **kwargs) -> str:
        if type_ not in [Any, str]:
            raise TypeError("NonKey's can only be strings", self, type_)
        return str(self)

class JGDVSimpleKey(str, JGDVBaseKey):
    """
      A Single key with no extras.
      ie: {x}. not {x}{y}, or {x}.blah.
    """

    def __repr__(self):
        return "<JGDVSimpleKey: {}>".format(str(self))

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        match other:
            case JGDVBaseKey() | str():
                return str(self) == str(other)
            case _:
                return False

    @property
    def indirect(self):
        if not self.is_indirect:
            return JGDVSimpleKey("{}_".format(super().__str__()))
        return self

    @property
    def is_indirect(self):
        return str(self).endswith("_")

    @property
    def form(self):
        """ Return the key in its use form, ie: wrapped in braces """
        return "{{{}}}".format(str(self))

    def within(self, other:str|dict|TomlGuard) -> bool:
        match other:
            case str():
                return self.form in other
            case dict() | TomlGuard():
                return self in other
            case _:
                raise TypeError("Uknown JGDVBaseKey target for within", other)

    def expand(self, spec=None, state=None, *, rec=False, insist=False, chain:list[JGDVBaseKey]=None, on_fail=Any, locs:DootLocations=None, **kwargs) -> str:
        key = self.redirect(spec)
        try:
            return JGDVFormatter.fmt(key, _spec=spec, _state=state, _rec=rec, _locs=locs, _insist=insist)
        except (KeyError, TypeError) as err:
            if bool(chain):
                return chain[0].expand(spec, state, rec=rec, chain=chain[1:], on_fail=on_fail)
            elif on_fail != Any:
                return on_fail
            else:
                raise err

    def redirect(self, spec:None|SpecStruct_p=None) -> JGDVBaseKey:
        """
          If the indirect form of the key is found in the spec, use that as a key instead
        """
        if not spec:
            return self

        match spec:
            case SpecStruct_p():
                kwargs = spec.params
            case None:
                kwargs = {}

        match kwargs.get(self.indirect, self):
            case str() as x if x == self.indirect:
                return self
            case str() as x:
                return JGDVBaseKey.build(x)
            case list() as lst:
                raise TypeError("Key Redirection resulted in a list, use redirect_multi", self)

        return self

    def redirect_multi(self, spec:None|SpecStruct_p=None) -> list[JGDVBaseKey]:
        """ redirect an indirect key to a *list* of keys """
        if not spec:
            return [self]

        match spec:
            case SpecStruct_p():
                kwargs = spec.params
            case None:
                kwargs = {}

        match kwargs.get(self.indirect, self):
            case str() as x if x == self:
                return [self]
            case str() as x:
                return [JGDVBaseKey.build(x)]
            case list() as lst:
                return [JGDVBaseKey.build(x) for x in lst]

        return [self]

    def to_type(self, spec:None|SpecStruct_p=None, state=None, type_=Any, chain:list[JGDVBaseKey]=None, on_fail=Any) -> Any:
        target            = self.redirect(spec)

        match spec:
            case SpecStruct_p():
                kwargs = spec.params
            case None:
                kwargs = {}

        task_name = state.get(STATE_TASK_NAME_K, None) if state else None
        match (replacement:=ChainedKeyGetter.chained_get(target, kwargs, state)):
            case None if bool(chain):
                return chain[0].to_type(spec, state, type_=type_, chain=chain[1:], on_fail=on_fail)
            case None if on_fail != Any and isinstance(on_fail, JGDVBaseKey):
                return on_fail.to_type(spec, state, type_=type_)
            case None if on_fail != Any:
                return on_fail
            case None if type_ is Any or type_ is None:
                return None
            case _ if type_ is Any:
                return replacement
            case _ if type_ and isinstance(replacement, type_):
                return replacement
            case None if not any(target in x for x in [kwargs, state]):
                raise KeyError("Key is not available in the state or spec", target)
            case _:
                raise TypeError("Unexpected Type for replacement", type_, replacement, self)

class JGDVArgsKey(str, JGDVBaseKey):
    """ A Key representing the action spec's args """

    def __call__(self, spec, state, **kwargs):
        return self.to_type(spec, state)

    def __repr__(self):
        return "<JGDVArgsKey>"

    def expand(self, *args, **kwargs):
        raise doot.errors.DootKeyError("Args Key doesn't expand")

    def redirect(self, spec=None):
        raise doot.errors.DootKeyError("Args Key doesn't redirect")

    def to_type(self, spec=None, state=None, *args, **kwargs) -> list:
        return spec.args

class JGDVKwargsKey(JGDVArgsKey):
    """ A Key representing all of an action spec's kwargs """

    def __repr__(self):
        return "<JGDVArgsKey>"

    def to_type(self, spec:None|SpecStruct_p=None, state=None, *args, **kwargs) -> dict:
        match spec:
            case SpecStruct_p():
                return spec.params
            case None:
                return {}

class JGDVImportKey(JGDVSimpleKey):
    """ a key to specify a key is used for importing
    ie: str expands -> JGDVCodeReference.build -> .try_import
    """
    pass
