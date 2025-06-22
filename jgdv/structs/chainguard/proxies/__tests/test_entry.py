#!/usr/bin/env python3
"""

"""
# ruff: noqa: ERA001, ANN201
##-- imports
from __future__ import annotations

import logging as logmod
import warnings
import pathlib as pl
##-- end imports

import pytest
from jgdv.structs.chainguard.errors import GuardedAccessError
from jgdv.structs.chainguard._base import GuardBase
from jgdv.structs.chainguard import ChainGuard
from jgdv.structs.chainguard.proxies.failure import GuardFailureProxy

logging = logmod.root

class TestProxiedGuard:

    def test_initial(self):
        base = ChainGuard({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert(isinstance(proxied, GuardFailureProxy))
        assert(isinstance(proxied.doesnt_exist, GuardFailureProxy))

    def test_proxy_on_existing_key(self):
        base = ChainGuard({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert(proxied.test() == "blah")

    def test_proxy_on_bad_key(self):
        base    = ChainGuard({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert("aweg" == proxied.awehjo())

    def test_proxy_index_independence(self):
        base                      = ChainGuard({"test": "blah"})
        base_val                  = base.test
        proxied                   = base.on_fail("aweg")
        good_key                  = proxied.test
        bad_key                   = proxied.ajojo

        assert(base_val           == "blah")
        assert(base._index()      == ["<root>"])
        assert(proxied._index()   == ["<root>"])
        assert(good_key._index()  == ["<root>", "test"])
        assert(bad_key._index()   == ["<root>", "ajojo"])

    def test_proxy_multi_independence(self):
        base           = ChainGuard({"test": "blah"})
        proxied        = base.on_fail("aweg")
        proxied2       = base.on_fail("jioji")
        assert(proxied is not proxied2)
        assert("aweg"  == proxied.awehjo())
        assert("jioji" == proxied2.awjioq())

    def test_proxy_value_retrieval(self):
        base     = ChainGuard({"test": "blah"})
        proxied = base.on_fail("aweg").test
        assert(isinstance(proxied, GuardFailureProxy))
        assert(proxied() == "blah")

    def test_proxy_nested_value_retrieval(self):
        base     = ChainGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.bloo
        assert(isinstance(proxied, GuardFailureProxy))
        assert(proxied() == "final")

    def test_proxy_none_value_use_fallback(self):
        base     = ChainGuard({"test": None})
        proxied  = base.on_fail("aweg").test
        assert(isinstance(proxied, GuardFailureProxy))
        assert(base.test is None)
        assert(proxied._fallback == "aweg")
        assert(proxied() == "aweg")

    def test_proxy_nested_false_value_uses_fallback(self):
        base     = ChainGuard({"top": {"mid": {"bot": None}}})
        proxied = base.on_fail("aweg").top.mid.bot
        assert(isinstance(proxied, GuardFailureProxy))
        assert(proxied() == "aweg")

    def test_proxy_fallback(self):
        base     = ChainGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.missing
        assert(isinstance(proxied, GuardFailureProxy))
        assert(proxied() == "aweg")

    def test_no_proxy_error(self):
        base     = ChainGuard({"test": { "blah": {"bloo": "final"}}})
        with pytest.raises(GuardedAccessError):
            base.test.blah()

    def test_proxy_early_check(self):
        base     = ChainGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test
        assert(isinstance(proxied, GuardFailureProxy))

    def test_proxy_multi_use(self):
        base     = ChainGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxied = base.on_fail("aweg").test.blah
        assert(proxied.bloo() == "final")
        assert(proxied.aweg() == "joijo")

