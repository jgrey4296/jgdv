#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN001, ANN202, B011, F841, ARG002

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings
from collections import ChainMap
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest

# ##-- end 3rd party imports

# ##-- 1st party imports
from jgdv import identity_fn
# ##-- end 1st party imports

from .._interface import ExpInst_d, SourceChain_d, ExpInstChain_d, InstructionFactory_p, IndirectKey_p, EXPANSION_CONVERT_MAPPING
from ... import DKey, IndirectDKey, NonDKey
from ..expander_stack import DKeyExpanderStack, InstructionFactory

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, cast, assert_type, assert_never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload
from collections.abc import Mapping

if TYPE_CHECKING:
   from jgdv import Maybe
   from typing import Final
   from typing import ClassVar, Any, LiteralString
   from typing import Never, Self, Literal
   from typing import TypeGuard
   from collections.abc import Iterable, Iterator, Callable, Generator
   from collections.abc import Sequence, MutableMapping, Hashable

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
logmod.getLogger("jgdv.structs.dkey._util.expander_stack").setLevel(logmod.INFO)
##-- end logging

# Vars:
Expanders : Final[list[type]] = [DKeyExpanderStack]
# Body:

class TestExpInst_d:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        obj = ExpInst_d(value="blah", fallback="bloo")
        assert(obj.value == "blah")
        assert(obj.rec is None)
        assert(obj.fallback == "bloo")

    def test_no_val_errors(self):
        with pytest.raises(KeyError):
            ExpInst_d(fallback="bloo")

    def test_match(self):
        match ExpInst_d(value="blah", fallback="bloo"):
            case ExpInst_d(value="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_match_fail(self):
        match ExpInst_d(value="bloo", fallback="bloo"):
            case ExpInst_d(rec=True):
                assert(False)
            case _:
                assert(True)

class TestExpInstChain_d:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

class TestSourceChain_d:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match SourceChain_d():
            case SourceChain_d():
                assert(True)
            case x:
                assert(False), x

    def test_with_base(self):
        match SourceChain_d({"a":2, "b":3}):
            case SourceChain_d():
                assert(True)
            case x:
                assert(False), x

    def test_with_specstruct_base(self):

        class SimpleSpecStruct:

            @property
            def params(self) -> dict:
                return {"blah":"aweg"}

            @property
            def args(self) -> list:
                return []

            @property
            def kwargs(self) -> dict:
                return {}

        match SourceChain_d(SimpleSpecStruct()):
            case SourceChain_d() as obj:
                assert(obj.get("blah") == "aweg")
            case x:
                assert(False), x

    def test_with_multi_base(self):
        match SourceChain_d({"a":2, "b":3}, {"blah":"bloo"}):
            case SourceChain_d():
                assert(True)
            case x:
                assert(False), x

    def test_extend(self):
        obj = SourceChain_d({"a":2, "b":3}, {"blah":"bloo"})
        match obj.extend({"blee":"aweg"}):
            case SourceChain_d() as extended:
                assert(obj is not extended)
                assert(extended.get("blee") == "aweg")
            case x:
                assert(False), x

    def test_simple_get(self):
        obj = SourceChain_d({"a":2, "b":3})
        match obj.get("b"):
            case 3:
                assert(True)
            case x:
                assert(False), x

    def test_simple_get_with_fallback(self):
        obj = SourceChain_d({"a":2, "b":3})
        match obj.get("d", 10):
            case 10:
                assert(True)
            case x:
                assert(False), x

    def test_multi_base_get(self):
        obj = SourceChain_d({"a":2, "b":3}, {"blah":"bloo"})
        match obj.get("blah"):
            case "bloo":
                assert(True)
            case x:
                assert(False), x

    def test_lookup(self):
        obj   = SourceChain_d({"a":2, "b":3}, {"blah":"bloo"})
        inst  = ExpInstChain_d(ExpInst_d(value="blah"),
                               root=DKey("blah"))
        match obj.lookup(inst):
            case ("bloo", x) if x == inst.chain[0]:
                assert(True)
            case x:
                assert(False), x

class TestInstructionFactory:

    @pytest.fixture(scope="function")
    def fac(self):
        return InstructionFactory(ctor=DKey)

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_match_protocol(self, fac):
        assert(isinstance(fac, InstructionFactory_p))

    def test_null_inst(self, fac):
        match fac.null_inst():
            case ExpInst_d(value=None):
                assert(True)
            case x:
                assert(False), x

    def test_simple_inst(self, fac):
        match fac.build_inst(DKey("{test}"), None, {}):
            case ExpInst_d(value="test"):
                assert(True)
            case x:
                assert(False), x

    def test_list_val_inst(self, fac):
        match fac.build_inst([1,2,3,4], None, {}):
            case ExpInst_d(value=[1,2,3,4], literal=True):
                assert(True)
            case x:
                assert(False), x

    def test_lift_implicit(self, fac):
        """ Because the root is indirect, the subsequent inst is lifted """
        root = fac.build_inst(DKey("{test_}"), None, {})
        match fac.build_inst("blah", root, {}):
            case ExpInst_d(value=DKey() as x, literal=False) if x == "blah":
                assert(True)
            case x:
                assert(False), x

    def test_prefer_key_hook(self, fac):

        class CustomHookKey(DKey):
            __slots__ = ()

            def exp_to_inst_h(self, root, factor, **kwargs):
                return ExpInst_d(value="test built", literal=True)

        assert(hasattr(CustomHookKey, "exp_to_inst_h"))
        key = DKey("{blah}", force=CustomHookKey)
        assert(isinstance(key, CustomHookKey))
        assert(hasattr(key, "exp_to_inst_h"))

        match fac.build_inst(key, None, {}):
            case ExpInst_d(value="test built", literal=True):
                assert(True)
            case x:
                assert(False), x

    def test_auto_lift_to_key(self, fac):
        match fac.build_inst("{test}", None, {}):
            case ExpInst_d(value=DKey() as x) if x == "test":
                assert(True)
            case x:
                assert(False), x

    def test_decrement_recursion(self, fac):
        initial = fac.build_inst(DKey("{test:e3}"), None, {}, decrement=False)
        assert(initial.rec == 3)
        match fac.build_inst(DKey("{test}"), initial, {}):
            case ExpInst_d(value="test", rec=2):
                assert(True)
            case x:
                assert(False), x

    def test_decrement_recursion_zero(self, fac):
        initial = fac.build_inst(DKey("{test:e0}"), None, {})
        assert(initial.rec == 0)
        match fac.build_inst(DKey("{test}"), initial, {}):
            case ExpInst_d(value="test", rec=0):
                assert(True)
            case x:
                assert(False), x

    def test_decrement_recursion_null(self, fac):
        initial = fac.build_inst(DKey("{test}"), None, {})
        assert(initial.rec is None)
        match fac.build_inst(DKey("{blah}"), initial, {}):
            case ExpInst_d(value="blah", rec=None):
                assert(True)
            case x:
                assert(False), x

    def test_decrement_recursion_guard(self, fac):
        initial = fac.build_inst(DKey("{test}"), None, {})
        assert(initial.rec is None)
        match fac.build_inst(DKey("{test}"), initial, {}):
            case ExpInst_d(value="test", rec=10):
                assert(True)
            case x:
                assert(False), x

    def test_basic_chain(self, fac):
        base = fac.build_inst("{blah}", None, {})
        match fac.build_chains(base, {}):
            case [ExpInstChain_d() as chain]:
                assert(len(chain) == 3)
                assert(chain[-1].value is None)
                assert(True)
            case x:
                assert(False), x

    def test_chains_dont_decrement_rec(self, fac):
        base = fac.build_inst("{blah:e5}", None, {}, decrement=False)
        assert(base.rec == 5)
        match fac.build_chains(base, {}):
            case [ExpInstChain_d() as chain]:
                assert(len(chain) == 3)
                assert(all(x.rec == 5 for x in chain[:-1]))
                assert(chain[-1].value is None)
                assert(True)
            case x:
                assert(False), x

    def test_custom_chain_hook(self, fac):

        class CustomChainHook(DKey):
            __slots__ = ()

            def exp_generate_chains_h(self, val, fac, opts):
                return [ExpInstChain_d(root=val.value)]

        key = DKey("{blah}", force=CustomChainHook)
        assert(isinstance(key, CustomChainHook))
        base = fac.build_inst(key, None, {})
        match fac.build_chains(base, {}):
            case [ExpInstChain_d() as chain]:
                assert(len(chain) == 0)
                assert(chain.root == key)
            case x:
                assert(False), x

    def test_chain_order(self, fac):
        """ Default order is [{key:d}, {key:i}, None] """

        key   = DKey("{blah}")
        base  = fac.build_inst(key, None, {})
        match fac.build_chains(base, {}):
            case [ExpInstChain_d() as chain]:
                assert(len(chain) == 3)
                assert(chain[0].value == key)
                assert(chain[1].value is not key)
                assert(chain[1].value == "blah")
                assert(isinstance(chain[1].value, IndirectKey_p))
                assert(chain.root is key)
            case x:
                assert(False), x

    def test_indirect_chain(self, fac):
        """ Indirect Keys swap the order to [{key:i}, {key:d}, None] """

        key   = DKey("{blah_}")
        base  = fac.build_inst(key, None, {})
        match fac.build_chains(base, {}):
            case [ExpInstChain_d() as chain]:
                assert(len(chain) == 3)
                assert(chain[0].value is key)
                assert(str(chain[0].value) == "blah_")
                assert(isinstance(chain[0].value, IndirectKey_p))
                assert(str(chain[1].value) == "blah")
                assert(chain.root is key)
            case x:
                assert(False), x

@pytest.mark.parametrize("ctor", Expanders)
class TestExpander:

    @pytest.fixture(scope="function")
    def source(self, mocker):
        return SourceChain_d()

    @pytest.fixture(scope="function")
    def exp(self, ctor):
        return ctor(ctor=DKey)

    def test_sanity(self, exp):
        assert(True is not False) # noqa: PLR0133

    def test_factory_access(self, ctor):
        match ctor():
            case ctor() as x:
                assert(isinstance(x._factory, InstructionFactory))
            case x:
                assert(False), x

    def test_set_ctor(self, ctor):
        obj = ctor()
        obj._factory._ctor = None
        obj.set_ctor(DKey)
        assert(obj._factory._ctor is DKey)

    def test_extra_sources(self, exp):

        class SimpleDKey(DKey):
            __slots__ = ()

            @override
            def exp_extra_sources_h(self, sources:SourceChain_d) -> SourceChain_d:
                return sources.extend([1,2,3,4])

        key = ExpInstChain_d(root=DKey("blah", force=SimpleDKey))
        assert(isinstance(key.root, SimpleDKey))
        match exp.extra_sources(key, SourceChain_d()):
            case SourceChain_d() as x:
                assert(x.sources[0] == [1,2,3,4])
            case x:
                assert(False), x

    def test_do_lookup(self, exp, source):
        key = ExpInstChain_d(ExpInst_d(value="simple"),
                             root=DKey("{simple}"),
                             )
        ext = source.extend({"simple":"blah"})
        match exp.do_lookup(key, ext, {}):
            case ExpInst_d(value="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_flatten(self, exp, source):
        obj      = exp
        obj.set_ctor(DKey)
        root = DKey("{simple}")
        vals = [
            ExpInst_d(value="simple"),
        ]
        match obj.flatten(vals, root, {}):
            case ExpInst_d() as x if x is vals[0]:
                assert(True)
            case x:
                assert(False), x

    def test_coerce_result_no_op(self, exp):
        obj      = exp
        obj.set_ctor(DKey)
        root     = DKey("{simple}")
        inst     = ExpInst_d(value="simple", rec=1)
        sources  = [{"simple":"blah"}]
        match obj.coerce_result(inst, root, {}):
            case ExpInst_d(value=str(), literal=True) as x:
                assert(True)
            case x:
                assert(False), x

    def test_coerce_result_simple(self, exp):
        obj      = exp
        obj.set_ctor(DKey)
        root = DKey("{simple}", ctor=pl.Path)
        inst     = ExpInst_d(value="simple", rec=1)
        sources  = [{"simple":"blah"}]
        match obj.coerce_result(inst, root, {}):
            case ExpInst_d(value=pl.Path(), literal=True) as x:
                assert(True)
            case x:
                assert(False), x

    @pytest.mark.skip
    def test_finalise(self, exp):
        pass

    @pytest.mark.skip
    def test_check_result(self, exp):
        pass

@pytest.mark.parametrize("ctor", Expanders)
class TestExpansion:

    @pytest.fixture(scope="function")
    def exp(self, ctor):
        return ctor(ctor=DKey)

    def test_sanity(self, exp):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self, exp):
        """ {test} -> blah """
        obj = DKey("test", implicit=True)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_basic_fail(self, exp):
        """ {aweg} -> None """
        obj    = DKey("aweg", implicit=True)
        state  = {"test": "blah"}
        match exp.expand(obj, state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_nonkey_expansion(self, exp):
        """ aweg -> aweg """
        obj = DKey("aweg")
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value="aweg"):
                assert(True)
            case x:
                assert(False), x

    def test_simple_recursive(self, exp):
        """
        {test} -> {blah} -> bloo
        """
        obj = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "bloo"}
        match exp.expand(obj, state):
            case ExpInst_d(value="bloo"):
                assert(True)
            case x:
                assert(False), x

    def test_double_recursive(self, exp):
        """
        {test} -> {blah}
        {blah} -> {aweg}/{bloo}
        {aweg}/{bloo} -> qqqq/{aweg}
        qqqq/{aweg} -> qqqq/qqqq
        """
        obj   = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}/{bloo}", "aweg":"qqqq", "bloo":"{aweg}"}
        match exp.expand(obj, state):
            case ExpInst_d(value="qqqq/qqqq"):
                assert(True)
            case x:
                assert(False), x

    def test_recursive_fail(self, exp):
        """
        {test} -> {blah}
        {blah} -> {aweg}/{bloo}
        {aweg} -> None
        {test} -> None
        """
        obj   = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}/{bloo}", "bloo":"ajqwoj"}
        match exp.expand(obj, state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_coerce_type(self, exp):
        """ test -> str(blah) -> pl.Path(blah) """
        obj   = DKey("test", implicit=True, ctor=pl.Path)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value=pl.Path()):
                assert(True)
            case x:
                assert(False), x

    def test_check_type(self, exp):
        """ {test} -> pl.Path(blah) """
        obj   = DKey("test", implicit=True, ctor=pl.Path)
        assert(f"{obj!s}" == "test")
        state = {"test": pl.Path("blah")}
        match exp.expand(obj, state):
            case ExpInst_d(value=pl.Path()):
                assert(True)
            case x:
                assert(False), x

    def test_recursion_limit(self, exp):
        obj    = DKey("test", implicit=True)
        state  = {"test": "{blah}", "blah":"{aweg}", "aweg": "bloo"}
        match exp.expand(obj, state, limit=1):
            case ExpInst_d(value=DKey() as x) if x == "blah":
                assert(True)
            case x:
                assert(False), x

    def test_expansion_cascade(self, exp):
        """
        {test} -1-> {blah},
        {test} -2-> {aweg}
        {test} -3-> qqqq
        """
        obj   = DKey("test", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}", "aweg": "qqqq"}
        assert(exp.expand(obj, state, limit=1).value == "blah")
        assert(exp.expand(obj, state, limit=2).value == "aweg")
        match exp.expand(obj, state, limit=3):
            case ExpInst_d(value=NonDKey() as x):
                assert(x == "qqqq")
            case x:
                assert(False), x

    def test_expansion_limit_format_param(self, exp):
        """
        {test:e1} -> state[test:{blah}, blah:{aweg}, aweg:qqqq] -> {bloo}
        """
        obj   = DKey("test:e1", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}", "aweg": "qqqq"}
        assert(exp.expand(obj, state).value == "blah")

    def test_expansion_limit_format_param_two(self, exp):
        """
        {test:e2} -> state[test:{blah}, blah:{aweg}, aweg:qqqq] -> {aweg}
        """
        obj   = DKey("test:e2", implicit=True)
        state = {"test": "{blah}", "blah": "{aweg}", "aweg": "qqqq"}
        assert(exp.expand(obj, state).value == "aweg")
        assert(isinstance(exp.expand(obj, state).value, DKey))

    @pytest.mark.skip("TODO")
    def test_additional_sources_recurse(self, exp):
        """ see doot test_dkey.TestDKeyExpansion.test_indirect_wrapped_expansion
        """
        assert(False)

    def test_keep_original_type_on_expansion(self, exp):
        """ {test} -> state[test:[1,2,3]] -> [1,2,3] """
        obj   = DKey("test", implicit=True)
        state = {"test": [1,2,3]}
        match exp.expand(obj, state):
            case ExpInst_d(value=list()):
                assert(True)
            case x:
                assert(False), type(x)

@pytest.mark.parametrize("ctor", Expanders)
class TestIndirection:

    @pytest.fixture(scope="function")
    def exp(self, ctor):
        return ctor(ctor=DKey)

    def test_sanity(self, exp):
        assert(True is not False) # noqa: PLR0133

    def test_hit(self, exp):
        """
        {key} -> state[key:value] -> value
        """
        obj   = DKey("test", implicit=True)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_hit_ignores_indirect(self, exp):
        """
        {key} -> state[key:value, key_:val2] -> value
        """
        obj   = DKey("test", implicit=True)
        state = {"test": "blah", "test_":"aweg"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss(self, exp):
        """
        {key} -> state[] -> None
        """
        obj   = DKey("test", implicit=True)
        state = {}
        match exp.expand(obj, state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_with_call_fallback(self, exp):
        """
        {key} -> state[] -> 25
        """
        obj   = DKey("test", implicit=True)
        state = {}
        match exp.expand(obj, state, fallback=25):
            case ExpInst_d(value=25):
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_with_ctor_fallback(self, exp):
        """
        {key} -> state[] -> 25
        """
        obj   = DKey("test", fallback=25, implicit=True)
        state = {}
        match exp.expand(obj, state):
            case ExpInst_d(value=25):
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_prefer_call_fallback_over_ctor(self, exp):
        """
        {key} -> state[] -> 25
        """
        obj   = DKey("test", fallback=10, implicit=True)
        state = {}
        match exp.expand(obj, state, fallback=25):
            case ExpInst_d(value=25):
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_indirect(self, exp):
        """
        {key_} -> state[] -> {key_}
        """
        obj = DKey("test_", implicit=True)
        assert(DKey.MarkOf(obj) == Mapping)
        state = {"test_": "blah", "blah": 25}
        match exp.expand(obj, state):
            case ExpInst_d(value=25):
                assert(True)
            case x:
                assert(False), x

    def test_soft_miss(self, exp):
        """
        {key} -> state[key_:blah] -> {blah}
        """
        target  = DKey("blah", implicit=True)
        obj     = DKey("test", implicit=True)
        state   = {"test_": "blah"}
        match exp.expand(obj, state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_soft_hit_direct(self, exp):
        """
        {key_} -> state[key:value] -> value
        """
        obj = DKey("test_", implicit=True)
        assert(DKey.MarkOf(obj) is Mapping)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah"):
                assert(True)
            case x:
                assert(False), x

    def test_soft_hit_indirect(self, exp):
        """
        {key_} -> state[key_:key2, key2:value] -> {value}
        """
        obj = DKey("test_", implicit=True)
        assert(DKey.MarkOf(obj) is Mapping)
        state = {"test_": "blah", "blah":"bloo"}
        match exp.expand(obj, state):
            case ExpInst_d(value="bloo"):
                assert(True)
            case x:
                assert(False), x

    def test_indirect_prefers_indirect_over_direct(self, exp):
        """
        {key_} -> state[key_:value, key:val2] -> {value}
        """
        obj = DKey("test_", implicit=True)
        assert(DKey.MarkOf(obj) is Mapping)
        state = {"test_": "blah", "test": "aweg", "blah":"bloo"}
        match exp.expand(obj, state):
            case ExpInst_d(value="bloo"):
                assert(True)
            case x:
                assert(False), x

@pytest.mark.parametrize("ctor", Expanders)
class TestMultiExpansion:

    @pytest.fixture(scope="function")
    def exp(self, ctor):
        return ctor(ctor=DKey)

    def test_sanity(self, exp):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self, exp):
        obj = DKey("{test} {test}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah blah"):
                assert(True)
            case x:
                assert(False), x

    def test_basic_fail(self, exp):
        obj = DKey("{test} {aweg}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_hard_miss_subkey(self, exp):
        """ {key}/{key2} -> state[key:value} -> None """
        obj = DKey("{test}/{aweg}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_soft_miss_subkey(self, exp):
        """ {key}/{key2} -> state[key:val, key2_:key] -> val/val """
        obj = DKey("{test}/{aweg}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah", "aweg_":"test"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah/blah"):
                assert(True)
            case x:
                assert(False), x

    def test_indirect_subkey(self, exp):
        """ {key}/{key2_} -> state[key:val, key2_:key] -> val/val """
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah", "aweg_":"test"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah/blah"):
                assert(True)
            case x:
                assert(False), x

    def test_direct_subkey_when_indirect_missing(self, exp):
        """ {key}/{key2_} -> state[key:val, key2:val2] -> val/val2 """
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah", "aweg":"test"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah/test"):
                assert(True)
            case x:
                assert(False), x

    def test_indirect_subkey_over_direct(self, exp):
        """ {key}/{key2_} -> state[key:val, key3:val2, key2_:key] -> val/val """
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah", "aweg":"test", "aweg_":"test"}
        match exp.expand(obj, state):
            case ExpInst_d(value="blah/blah"):
                assert(True)
            case x:
                assert(False), x

    def test_indirect_miss_subkey_remains(self, exp):
        """ {key}/{key2_} -> state[key:val] ->  """
        obj = DKey("{test}/{aweg_}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_multikey_recursion_missing_subkey(self, exp):
        obj = DKey[list]("{test}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "{blah}", "blah": "blah/{aweg_}"}
        match exp.expand(obj, state):
            case None:
                assert(True)
            case x:
                assert(False), x

    def test_multikey_recursion_depth_10(self, exp):
        obj = DKey[list]("{test}")
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "{test}"}
        match exp.expand(obj, state, limit=10):
            case ExpInst_d(value="{test}"):
                assert(True)
            case x:
                assert(False), x

    def test_multikey_individual_subkey_recursion_limit(self, exp):
        """
        Setting recursion limits with :e[digit]
        {test:e2} -> state[test:{blah}, blah:{aweg}, aweg:qqqq] -> {aweg}
        """
        obj = DKey("{test:e1} : {test:e2} : {test:e3}")
        state = {"test": "{blah}", "blah": "{aweg}", "aweg": "qqqq"}
        assert(exp.expand(obj, state).value == "{blah} : {aweg} : qqqq")

@pytest.mark.parametrize("ctor", Expanders)
class TestCoercion:

    @pytest.fixture(scope="function")
    def exp(self, ctor):
        return ctor(ctor=DKey)

    def test_sanity(self, exp):
        assert(True is not False) # noqa: PLR0133

    def test_coerce_param_path(self, exp):
        obj = DKey("{test!p}")
        state = {"test": "blah"}
        assert(obj.data.convert == "p")
        match exp.expand(obj, state):
            case ExpInst_d(value=pl.Path()):
                assert(True)
            case x:
                assert(False), x

    def test_coerce_param_int(self, exp):
        obj = DKey("{test!i}")
        state = {"test": "25"}
        assert(obj.data.convert == "i")
        match exp.expand(obj, state):
            case ExpInst_d(value=25):
                assert(True)
            case x:
                assert(False), x

    def test_coerce_param_fail(self, exp):
        obj = DKey("{test!i}")
        state = {"test": "blah"}
        assert(obj.data.convert == "i")
        assert(obj.data.convert in EXPANSION_CONVERT_MAPPING)
        with pytest.raises(ValueError):
            EXPANSION_CONVERT_MAPPING["i"]("blah")

        with pytest.raises(ValueError):
            exp.expand(obj, state)

    def test_multi_coerce_to_path(self, exp):
        obj = DKey("{test}/{test}", ctor=pl.Path)
        assert(DKey.MarkOf(obj) is list)
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value=pl.Path()):
                assert(True)
            case x:
                assert(False), x

    def test_multi_coerce_subkey(self, exp):
        obj = DKey("{test!p}/{test}")
        assert(DKey.MarkOf(obj) is list)
        assert(obj.keys()[0].data.convert == "p")
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value=str() as x):
                assert(x == str(pl.Path.cwd() / "blah/blah"))
                assert(True)
            case x:
                assert(False), x

    def test_multi_coerce_multi_subkey(self, exp):
        obj    = DKey("{test!p} : {test!p}")
        target = "".join(map(str, [(pl.Path.cwd() / "blah"), " : ", (pl.Path.cwd() / "blah")]))
        assert(DKey.MarkOf(obj) is list)
        assert(obj.keys()[0].data.convert == "p")
        state = {"test": "blah"}
        match exp.expand(obj, state):
            case ExpInst_d(value=str() as x):
                assert(x == target)
                assert(True)
            case x:
                assert(False), x

@pytest.mark.parametrize("ctor", Expanders)
class TestFallbacks:

    @pytest.fixture(scope="function")
    def exp(self, ctor):
        return ctor(ctor=DKey)

    def test_sanity(self, exp):
        assert(True is not False) # noqa: PLR0133

    def test_basic_key_fallback(self, exp):
        key = DKey("blah", implicit=True, fallback="aweg")
        match exp.expand(key):
            case ExpInst_d(value="aweg"):
                assert(True)
            case x:
                 assert(False), x

    def test_basic_expansion_fallback(self, exp):
        key = DKey("blah", implicit=True)
        match exp.expand(key, fallback="aweg"):
            case ExpInst_d(value="aweg"):
                assert(True)
            case x:
                 assert(False), x

    def test_fallback_typecheck(self, exp):
        key = DKey("blah", implicit=True, fallback="aweg", check=str)
        match exp.expand(key):
            case ExpInst_d(value="aweg"):
                assert(True)
            case x:
                 assert(False), x

    @pytest.mark.parametrize("fallback", [list, dict, set])
    def test_fallback_type_factory(self, exp, fallback):
        key = DKey("blah", implicit=True, fallback=fallback)
        match exp.expand(key):
            case ExpInst_d(value=list()|dict()|set()):
                assert(True)
            case x:
                 assert(False), x
