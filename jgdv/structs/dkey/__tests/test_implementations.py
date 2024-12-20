#!/usr/bin/env python4
"""

"""
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast, Self, Final)
import warnings

import pytest

logging = logmod.root

from jgdv._abstract.protocols import Key_p
from jgdv.structs.strang import CodeReference
from jgdv.structs.dkey import implementations as dkey
from jgdv.structs.dkey.formatter import DKeyFormatter

IMP_KEY_BASES               : Final[list[str]]           = ["bob", "bill", "blah", "other", "23boo", "aweg2531", "awe_weg", "aweg-weji-joi"]
EXP_KEY_BASES               : Final[list[str]]           = [f"{{{x}}}" for x in IMP_KEY_BASES]
EXP_P_KEY_BASES             : Final[list[str]]           = ["{bob:wd}", "{bill:w}", "{blah:wi}", "{other:i}"]
PATH_KEYS                   : Final[list[str]]           = ["{bob}/{bill}", "{blah}/{bloo}", "{blah}/{bloo}"]
MUTI_KEYS                   : Final[list[str]]           = ["{bob}_{bill}", "{blah} <> {bloo}", "! {blah}! {bloo}!"]
IMP_IND_KEYS                : Final[list[str]]           = ["bob_", "bill_", "blah_", "other_"]
EXP_IND_KEYS                : Final[list[str]]           = [f"{{{x}}}" for x in IMP_IND_KEYS]

VALID_KEYS                                           = IMP_KEY_BASES + EXP_KEY_BASES + EXP_P_KEY_BASES + IMP_IND_KEYS + EXP_IND_KEYS
VALID_MULTI_KEYS                                     = PATH_KEYS + MUTI_KEYS

class TestDKeyTypeParams:

    def test_str_mark(self):
        assert(dkey.StrDKey._mark is dkey.DKey.mark.STR)

class TestDKeyBasicConstruction:

    def test_nonkey(self):
        """ text on its own is a null-key """
        key  = dkey.DKey("blah bloo blee")
        assert(isinstance(key, dkey.NonDKey))
        assert(isinstance(key, str))
        assert(isinstance(key, dkey.DKey))
        assert(str(key) == "blah bloo blee")

    def test_implicit(self):
        """ but if its marked as implicit, it is a key """
        key  = dkey.DKey("test", implicit=True)
        assert(isinstance(key, dkey.SingleDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(f"{key:w}" == "{test}")
        assert(f"{key:i}" == "test_")
        assert(f"{key:wi}" == "{test_}")
        assert(str(key) == "test")

    def test_explicit(self):
        """ keys wrapped in braces are explicit """
        key  = dkey.DKey("{test}")
        assert(isinstance(key, dkey.SingleDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(str(key) == "test")

    def test_multi_key(self):
        """ multiple explicit keys in the string create a multikey """
        key  = dkey.DKey("{test}/{blah}")
        assert(isinstance(key, dkey.MultiDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(key._fmt_params is None)
        assert(key.keys() == [dkey.DKey("test"), dkey.DKey("blah")])
        assert(str(key) == "{test}/{blah}")

    def test_multi_key_implicit_errors(self):
        """ trying to mark a key as implicit, when its not, errors  """
        with pytest.raises(ValueError):
            dkey.DKey("{test}/{blah}", implicit=True)

    def test_multi_keys_with_multiple_subkeys(self):
        """ typed keys within multikeys are allowed,
          it will just be all coerced to a string eventually
        """
        key = dkey.DKey("text. {simple!p}. {text}.", implicit=False)
        assert(isinstance(key, dkey.MultiDKey))
        assert(key._has_text)
        assert(len(key.keys()) == 2)


    def test_redirection_implicit(self):
        """ Keys ending in underscores are redirections """
        key = dkey.DKey("simple_", implicit=True)
        assert(isinstance(key, dkey.RedirectionDKey))

    def test_redirection_explicit(self):
        """ Keys ending in underscores are redirections """
        key = dkey.DKey("{simple_}", implicit=False)
        assert(isinstance(key, dkey.RedirectionDKey))

    def test_null_fallback_error(self):
        state = {}
        with pytest.raises(ValueError):
            dkey.DKey("a_null_key", fallback="blah")

    def test_specific_class_ctor_fails(self):
        state = {}
        with pytest.raises(RuntimeError):
            dkey.SingleDKey("a_null_key", fallback="blah")

    def test_specific_class_ctor_force(self):
        state = {}
        key = dkey.SingleDKey("a_null_key", fallback="blah", force=True)
        assert(isinstance(key, dkey.SingleDKey))

class TestDKeyProperties:

    @pytest.mark.parametrize("name", VALID_KEYS)
    @pytest.mark.parametrize("check", [int,str,int|float,list[int],list[str|float], Any, None])
    def test_build_with_typecheck(self, name, check):
        """ Keys can be built to typecheck their return value on expansion """
        obj = dkey.DKey(name, check=check)
        assert(isinstance(obj, dkey.DKey))
        assert(isinstance(obj, str))
        assert(obj._typecheck == check or Any)

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_key_str(self, name):
        """ keys are subclasses of str """
        obj = dkey.DKey(name, implicit=True)
        assert(isinstance(obj, dkey.DKey))
        assert(isinstance(obj, str))
        assert(str(obj) == name)

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_key_down_to_str(self, name):
        """ converting a key to a str removes its key-ness """
        obj = dkey.DKey(name)
        assert(isinstance(obj, dkey.DKey))
        assert(isinstance(obj, str))
        as_str = str(obj)
        assert(as_str == name)
        assert(not isinstance(as_str, dkey.DKey))
        assert(isinstance(as_str, str))

    @pytest.mark.parametrize("name", PATH_KEYS)
    def test_keys_error_on_multi_keys(self, name):
        """ try to buid an implicit key with explicit keys in the string, get an error"""
        with pytest.raises(ValueError):
            dkey.DKey(name, implicit=True)

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_keys_are_implicit(self, name):
        """
          explicit single keys have their braces removed
        """
        explicit = "{%s}" % name
        obj      = dkey.DKey(explicit)
        assert(isinstance(obj, dkey.DKey))
        assert(str(obj) == name)

    @pytest.mark.parametrize("name", PATH_KEYS + MUTI_KEYS)
    def test_multi_build(self, name):
        """
          Keys with multiple expansion points are built as multi keys
        """
        obj = dkey.DKey(name)
        assert(not isinstance(obj, dkey.SingleDKey))
        assert(isinstance(obj, dkey.MultiDKey))
        assert(isinstance(obj, dkey.DKey))

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_build_idempotent(self, name):
        """
          making a key from a key does nothing.
        """
        obj1 = dkey.DKey(name)
        obj2 = dkey.DKey(obj1)
        assert(isinstance(obj1, dkey.DKey))
        assert(isinstance(obj2, dkey.DKey))
        assert(obj1 == obj2)
        assert(obj1 is obj2)
        assert(id(obj1) == id(obj2))

    def test_integrated_str_keys(self):
        """ strings with text and keys do not lose the null-keys parts """
        obj = dkey.DKey("--{raise}={value}")
        assert(str(obj) == "--{raise}={value}")

    def test_key_help(self):
        """ strings with text and keys do not lose the null-keys parts """
        obj = dkey.DKey("--{raise}={value}", help="a help string")
        assert(obj._help == "a help string")

class TestDKeyWithParameters:
    """ Tests for checking construction with various parameter are preserved """

    def test_no_params(self):
        """ pass no params """
        key  = dkey.DKey("test", implicit=True)
        assert(isinstance(key, dkey.SingleDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(key._fmt_params is None)
        assert(key._expansion_type is dkey.identity)
        assert(key._typecheck is Any)

    def test_simple_with_fparams(self):
        """ pass a formatting param """
        key  = dkey.DKey("{test:w}")
        assert(isinstance(key, dkey.SingleDKey))
        assert(isinstance(key, dkey.DKey))
        assert(isinstance(key, str))
        assert(key._fmt_params is not None)
        assert(key._fmt_params == "w")

    def test_conv_parms_redirect(self):
        obj = dkey.DKey("aval!R", implicit=True)
        assert(isinstance(obj, dkey.RedirectionDKey))

    def test_conv_params_code(self):
        obj = dkey.DKey("aval!c", implicit=True)
        assert(isinstance(obj, dkey.ImportDKey))

    def test_conflicting_marks_error(self):
        with pytest.raises(ValueError):
            dkey.DKey("{aval!s}", implicit=False, mark=dkey.DKey.mark.CODE)

class TestDKeyFormatting:

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_repr(self, name):
        key = dkey.DKey(name, implicit=True)
        assert(repr(key) == f"<SingleDKey: {key}>")

    @pytest.mark.parametrize("name", PATH_KEYS)
    def test_multi_repr(self, name):
        key = dkey.DKey(name)
        assert(repr(key) == f"<MultiDKey: {key}>")

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_fstr_explicit_from_implicit(self, name):
        """ key -> {key} """
        key           = dkey.DKey(name, implicit=True)
        result        = f"{key:w}"
        assert(result == "".join(["{", name, "}"]))

    @pytest.mark.parametrize("name", IMP_IND_KEYS)
    def test_fstr_explicit_indirect(self, name):
        """ keys_ -> {keys_}"""
        key           = dkey.DKey(name, implicit=True)
        result        = f"{key:wi}"
        assert(result == "".join(["{", name, "}"]))

    @pytest.mark.parametrize("name", IMP_KEY_BASES + IMP_IND_KEYS)
    def test_coerce_indirect_to_wrapped_direct(self, name):
        """ key_ -> {key} """
        key           = dkey.DKey(name, implicit=True)
        result        = f"{key:wd}"
        assert(result == "".join(["{", name.removesuffix("_"), "}"]))

    @pytest.mark.parametrize("name", PATH_KEYS)
    def test_fstr_multi_key(self, name):
        """ multi keys are explicit by default """
        key           = dkey.DKey(name)
        result        = f"{key}"
        assert(result == name)
        assert(bool(key.keys()))

    def test_anon_format_multistring(self):
        """ multi keys are explicit by default """
        key           = dkey.DKey("head {test}/{blah} tail {bloo} end")
        result        = "head {}/{} tail {} end"
        assert(key._anon == result)

    @pytest.mark.parametrize("name", PATH_KEYS)
    def test_fstr_multi_explicit(self, name):
        """ specifying alt form does nothing """
        key           = dkey.DKey(name)
        explicit = f"{key:w}"
        implicit = f"{key:i}"
        assert(explicit == name == implicit)
        assert(bool(key.keys()))

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_fstr_null_key(self, name):
        """ null keys cant be explicit, specifying alt form does nothing """
        key           = dkey.DKey(name, implicit=False)
        assert(isinstance(key, dkey.NonDKey))
        explicit = f"{key:w}"
        implicit = f"{key}"
        assert(explicit == name == implicit)

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_str_format(self, name):
        key = dkey.DKey(name)
        result = "{}".format(key)
        assert(result == name)

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_fstr_format(self, name):
        key = dkey.DKey(name)
        result = f"{key}"
        assert(result == name)

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_fstr_with_width(self, name):
        key = dkey.DKey(name)
        result = f"{key: <5}"
        assert(result == f"{name: <5}")

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_nonkey_format(self, name):
        key           = dkey.DKey(name, implicit=False)
        result        = f"{key}"
        assert(result == name)

    @pytest.mark.parametrize("name", PATH_KEYS)
    def test_multikey_format(self, name):
        key    = dkey.DKey(name)
        result = f"{key}"
        assert(isinstance(key, dkey.MultiDKey))
        assert(result == name)

class TestDKeyComparison:

    @pytest.mark.parametrize("name", VALID_KEYS)
    def test_sanity(self, name):
        key1 = dkey.DKey(name)
        key2 = dkey.DKey(name)
        assert(key1 == key2)
        assert(key1 is not key2)

    @pytest.mark.parametrize("name", VALID_KEYS)
    def test_hashing(self, name):
        key1 = dkey.DKey(name)
        key2 = dkey.DKey(name)
        assert(hash(key1) == hash(key2) == hash(str(key1)) == hash(str(key2)))

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_key_and_str(self, name):
        """ both __and__ + __rand__ """
        key      = dkey.DKey(name, implicit=True)
        test_str = "this is a {} test".format(f"{key:w}")
        assert(key & test_str)
        assert(test_str & key)

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_key_and_str_fail(self, name):
        """ both __and__ + __rand__ """
        key      = dkey.DKey(name, implicit=True)
        test_str = "this is a {} test".format(f"{key}")
        assert(not (key & test_str))
        assert(not (test_str & key))

    @pytest.mark.xfail
    def test_multikey_and_containment(self):
        """ both __and__ + __rand__ """
        key      = dkey.DKey("{blah} with {bloo}")
        assert((dkey.DKey("blah", implicit=True) & key))

    @pytest.mark.parametrize("name", IMP_KEY_BASES)
    def test_key_eq(self, name):
        """   """
        key      = dkey.DKey(name)
        assert( key == name )

class TestDKeyExpansion:

    def test_recursive_expansion_str(self):
        """
          top -> b -> {b}, is guarded
        """
        state = {"top_": "b", "b": "{b}"}
        key = dkey.DKey("top", implicit=True)
        assert(isinstance(key, dkey.DKey))
        result = key.expand(state)
        assert(isinstance(result, dkey.DKey))
        assert(result == "b")

    def test_expansion_explicit_key(self):
        key           = dkey.DKey("--{raise}")
        result        = key.expand({"raise":"minor"})
        assert(key    == "--{raise}")
        assert(result == "--minor")

    def test_expansion_to_str_for_expansion(self):
        target        = "Before. Middle. After."
        key           = dkey.DKey("middle", implicit=True)
        result        = key.expand({"raise":"Middle", "middle": "Before. {raise}. After."})
        assert(key    == "middle")
        assert(result == target)

    def test_expansion_with_type_spec_in_str(self):
        """ check setting expansion parameters directly from the initial string
          {a!s} -> 2:str
          """
        key   = dkey.DKey("{a!s}")
        state = {"a": 2}
        assert(isinstance(key, dkey.DKey))
        result = key.expand(state)
        assert(isinstance(result, str))
        assert(result == "2")

    def test_nested_expansion(self):
        """
          top -> {y} : {a} -> aweg : 2
        """
        key = dkey.DKey("top", implicit=True)
        assert(isinstance(key, dkey.DKey))
        state = {"top": "{y} : {a}", "y": "aweg", "a": 2}
        result = key.expand(state)
        assert(result == "aweg : 2")

    def test_expansion_of_sh_command(self):
        """
          test_ -> [a, b, c]
        """
        import sh
        from sh import ls
        state = { "cmd":ls}
        key   = dkey.DKey("cmd", implicit=True)
        result = key.expand(state)
        assert(result is not None)
        assert(isinstance(result, sh.Command))
        assert(result is ls)

    @pytest.mark.parametrize("name", ["a", "b"])
    def test_chain_expansion(self, name):
        """ name -> {x} -> y """
        key   = dkey.DKey(name, implicit=True)
        state = {name :"{x}", "x": "y"}
        exp = key.expand(state)
        assert(exp == "y")

    @pytest.mark.parametrize("name", ["a", "b"])
    def test_chain_expand_literal_key(self, name):
        """ name -> DKey(x) -> y """
        key   = dkey.DKey(name, implicit=True)
        state = {name : dkey.DKey("x", implicit=True), "x": "y"}
        exp = key.expand(state)
        assert(exp == "y")

    @pytest.mark.parametrize("name", ["a", "b"])
    def test_string_expansion_with_subkey(self, name):
        """ this is a {name} blah. -> this is a test blah."""
        full_str = "this is a {%s} blah." % name
        key      = dkey.DKey(full_str, implicit=False, mark=dkey.DKey.mark.STR)
        state    = {name : "test"}
        exp      = key.expand(state)
        assert(isinstance(key, dkey.MultiDKey))
        assert(exp == "this is a test blah.")

    def test_max_expansion_limit(self):
        """ this is a {name} blah. -> this is a test blah."""
        full_str = "this is a {name} blah."
        state    = {"name": "test", "base": full_str}
        key      = dkey.DKey("base", implicit=True, mark=dkey.DKey.mark.FREE)
        assert(full_str != key.expand(state))
        assert(full_str == key.expand(state, max=1))

    def test_max_expansion_limit_in_ctor(self):
        """ this is a {name} blah. -> this is a test blah."""
        full_str = "this is a {name} blah."
        state    = {"name": "test", "base": full_str}
        key      = dkey.DKey("base", implicit=True, mark=dkey.DKey.mark.FREE, max_exp=1)
        assert(full_str == key.expand(state))

class TestDKeyMultikeyExpansion:

    @pytest.mark.parametrize("name", ["a", "b"])
    def test_string_expansion_with_multi_use_subkey(self, name):
        """ this is a {name} blah {name}. -> this is a test blah test."""
        full_str = "this is a {%s} blah {c}." % name
        key      = dkey.DKey(full_str, implicit=False, mark=dkey.DKey.mark.STR)
        state    = {name : "test", "c": "test"}
        exp      = key.expand(state)
        assert(isinstance(key, dkey.MultiDKey))
        assert(exp == "this is a test blah test.")

    @pytest.mark.parametrize("name", ["a", "b"])
    def test_string_expansion_with_multi_subkeys(self, name):
        """ this is a {name} blah {name}. -> this is a test blah test."""
        full_str = "this is a {%s} blah {bloo}." % name
        key      = dkey.DKey(full_str, implicit=False, mark=dkey.DKey.mark.STR)
        state    = {name : "test", "bloo": "other"}
        exp      = key.expand(state)
        assert(isinstance(key, dkey.MultiDKey))
        assert(exp == "this is a test blah other.")

class TestDKeyExpansionFallback:

    def test_sanity(self):
        assert(True is not False)
        state = {}
        key = dkey.DKey("a_null_key")
        result = key.expand(state)
        assert(result == key)

    def test_null_fallback_error(self):
        state = {}
        key = dkey.DKey("a_null_key")
        with pytest.raises(ValueError):
            key.expand(state, fallback="blah")

    def test_implicit_with_ctor_fallback(self):
        state = {}
        key = dkey.DKey("a_null_key", implicit=True, fallback="blah")
        assert(key.expand(state) == "blah")

    def test_expansion_fallback_overrides_ctor_fallback(self):
        state = {}
        key = dkey.DKey("an_empty_key", implicit=True, fallback="blah")
        assert(isinstance(key, dkey.SingleDKey))
        assert(key.expand(state) == "blah")
        assert(key.expand(state, fallback="bloo") == "bloo")

    def test_implicit_with_expansion_fallback(self):
        state = {}
        key = dkey.DKey("an_empty_key", implicit=True)
        assert(key.expand(state) is None)
        assert(key.expand(state, fallback="blah") == "blah")

    def test_explicit_with_ctor_fallback(self):
        state = {}
        key = dkey.DKey("{an_empty_key}", implicit=False, fallback="blah")
        assert(key.expand(state) == "blah")

    def test_explicit_with_expansion_fallback(self):
        state = {}
        key = dkey.DKey("{an_empty_key}", implicit=False)
        assert(key.expand(state) is None)
        assert(key.expand(state, fallback="blah") == "blah")

    def test_multikey_with_ctor_fallback(self):
        state = {}
        key = dkey.DKey("{an_empty_key} {and_another}", implicit=False, fallback="blah")
        assert(key.expand(state, fallback="blah") == "blah")

    def test_multikey_with_expansion_fallback(self):
        state = {}
        key = dkey.DKey("{an_empty_key} {and_another}", implicit=False)
        assert(key.expand(state) is None)
        assert(key.expand(state, fallback="blah") == "blah")

    def test_multikey_with_partial_expansion_ctor_fallback(self):
        state = {"and_another": "aweg"}
        key = dkey.DKey("{a_null_key} {and_another}", implicit=False, fallback="blah")
        assert(key.expand(state) == "{a_null_key} aweg")

    def test_multikey_with_partial_expansion_fallback(self):
        state = {"and_another": "aweg"}
        key = dkey.DKey("{a_null_key} {and_another}", implicit=False)
        assert(key.expand(state) == "{a_null_key} aweg")
        assert(key.expand(state, fallback="blah") == "{a_null_key} aweg")

    def test_redirect_key_with_fallback(self):
        state = {}
        key = dkey.DKey("test_", implicit=True, fallback="blah")
        assert(isinstance(key, dkey.RedirectionDKey))
        assert(isinstance(key.expand(state), dkey.SingleDKey))
        assert(key.expand(state) == "blah")

    def test_redirect_key_with_expansion_fallback_error(self):
        state = {}
        key = dkey.DKey("test_", implicit=True)
        with pytest.raises(ValueError):
            key.expand(state, fallback="blah")

class TestDKeyRedirection:

    def test_sanity(self):
        assert(True is not False)

    def test_redirection_multi(self):
        """
          test_ -> [a, b, c]
        """
        state = { "test_": ["a", "b", "c"], "blah": 23, "a":10, "b":15, "c":25}
        key   = dkey.DKey("test_", mark=dkey.DKey.mark.REDIRECT, implicit=True)
        assert(isinstance(key, dkey.RedirectionDKey))
        result = key.redirect(state, multi=True)
        assert(result is not None)
        assert(isinstance(result, list))
        assert(len(result) == 3)
        assert(result[0] == "a")
        assert(result[1] == "b")
        assert(result[2] == "c")

    def test_redirection_expand_multi_in_ctor(self):
        """
          test_ -> [a, b, c]
        """
        state = { "test_": ["a", "b", "c"], "blah": 23, "a":10, "b":15, "c":25}
        key   = dkey.DKey("test_", mark=dkey.DKey.mark.REDIRECT, multi=True, implicit=True)
        assert(isinstance(key, dkey.RedirectionDKey))
        result = key.expand(state)
        assert(result is not None)
        assert(isinstance(result, list))
        assert(len(result) == 3)
        assert(result[0] == "a")
        assert(result[1] == "b")
        assert(result[2] == "c")

    @pytest.mark.parametrize("name", ["a_", "b_", "blah_bloo_"])
    def test_redirect_expansion(self, name):
        """ name_ -> DKey(x) -> y"""
        key   = dkey.DKey(name, implicit=True)
        assert(isinstance(key, dkey.RedirectionDKey))
        state = {name :"x", "x": "y"}
        redir = key.expand(state)
        exp   = redir.expand(state)
        assert(isinstance(redir, dkey.DKey))
        assert(key == name)
        assert(exp == "y")

    @pytest.mark.parametrize("name", ["a", "b", "blah_bloo"])
    def test_redirect_preferred(self, name):
        """
          name -> DKey(x)  -> y
          name_ -> DKey(x) -> y
        """
        name_              = f"{name}_"
        key_direct         = dkey.DKey(name, implicit=True)
        key_indirect       = dkey.DKey(name_, implicit=True)
        state              = {name :"blah", "x": "y", name_: "x"}
        redir              = key_indirect.expand(state)
        indir_exp          = redir.expand(state)
        dir_exp            = key_direct.expand(state)
        assert(isinstance(redir, dkey.DKey))
        assert(key_indirect == name_)
        assert(key_direct == name)
        assert(indir_exp == "y")
        assert(dir_exp == "y")

    @pytest.mark.parametrize("name", ["a", "b", "blah_bloo"])
    def test_redirect_fallbacks_to_actual_by_default(self, name):
        """ name_ -> name -> y"""
        name_     = f"{name}_"
        key       = dkey.DKey(name_, implicit=True)
        state     = {name :"y"}
        redir     = key.expand(state)
        exp       = redir.expand(state)
        assert(isinstance(redir, dkey.DKey))
        assert(redir == name)
        assert(key == name_)
        assert(exp == "y")

    @pytest.mark.parametrize("name", ["a", "b", "blah_bloo"])
    def test_redirect_fallback_to_explicit_None(self, name):
        """ name_ -> name -> y"""
        name_     = f"{name}_"
        key       = dkey.DKey(name_, fallback=None, implicit=True)
        state     = {name :"y"}
        redir     = key.expand(state)
        assert(redir is None)

    @pytest.mark.parametrize("name", ["a_", "b_"])
    def test_redirect_full_expansion(self, name):
        """ name_ -> y"""
        key   = dkey.DKey(name, implicit=True)
        state = {name :"x", "x": "y"}
        exp   = key.expand(state, full=True)
        assert(exp == "y")

class TestDKeyExpansionTyping:

    def test_sanity(self):
        assert(True is not False)

    @pytest.mark.parametrize("name", ["x"])
    def test_basic_type_check(self, name):
        """ name -> 2 """
        key   = dkey.DKey(name, implicit=True, check=int)
        state = {name :2}
        exp = key.expand(state)
        assert(not isinstance(exp, str))
        assert(exp == 2)

    @pytest.mark.parametrize("name", ["x"])
    def test_basic_type_check_fail(self, name):
        """ name -> 2 """
        key   = dkey.DKey(name, implicit=True, check=set)
        state = {name :2}
        with pytest.raises(TypeError):
            key.expand(state)

class TestDKeyCodeKeys:

    def test_coderef_expansion(self):
        """
          test -> coderef
        """
        state = {"test": "cls::doot._structs.task_spec:TaskSpec"}
        key   = dkey.DKey("test", implicit=True, mark=dkey.DKey.mark.CODE)
        assert(isinstance(key, dkey.DKey))
        result = key.expand(state)
        assert(isinstance(result, CodeReference))
