"""

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202

# Imports
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

import pytest
from jgdv.logging.logger import JGDVLogger

# Logging:
logging = logmod.root

# Type Aliases:

# Vars:

# Body:

class TestJGDVLogger:

    @pytest.fixture(scope="function")
    def install(self):
        orig = logmod.getLoggerClass()
        JGDVLogger.install()
        yield
        logmod.setLoggerClass(orig)

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        logger = JGDVLogger("basic")
        assert(isinstance(logger, logmod.getLoggerClass()))

    def test_defaults(self):
        logger = JGDVLogger("basic")
        assert(hasattr(logger, "info"))
        assert(hasattr(logger, "debug"))
        assert(hasattr(logger, "warning"))
        assert(hasattr(logger, "error"))
        assert(hasattr(logger, "critical"))

    def test_non_default_fail(self):
        logger = JGDVLogger("basic")
        with pytest.raises(AttributeError):
            getattr(logger, "blah")

        with pytest.raises(AttributeError):
            logger.blah

    def test_non_default_success(self, install, caplog):
        with caplog.at_level(logmod.DEBUG):
            logger = logmod.getLogger("basic")
            assert(isinstance(logger, JGDVLogger))
            assert(callable(logger.trace))
            logger.trace("blah")

        assert("blah" in caplog.messages)

    def test_non_default_getitem(self, install, caplog):
        with caplog.at_level(logmod.DEBUG):
            logger = logmod.getLogger("basic")
            assert(isinstance(logger, JGDVLogger))
            assert(callable(logger['trace']))
            logger['trace']("blah")

        assert("blah" in caplog.messages)

    def test_prefix(self, install, caplog):
        with caplog.at_level(logmod.DEBUG):
            logger = logmod.getLogger("basic")
            logger.trace("blah")
            logger.prefix("> ").trace("bloo")
            logger.prefix("> ").trace("qqqq")
            logger.trace("aweg")

        assert("blah" in caplog.messages)
        assert("> bloo" in caplog.messages)
        assert("> qqqq" in caplog.messages)
        assert("aweg" in caplog.messages)

    def test_callable_prefix(self, install, caplog):
        count = 0

        def the_prefix():
            nonlocal count
            count += 1
            return f"({count}) "

        with caplog.at_level(logmod.DEBUG):
            logger = logmod.getLogger("basic")
            logger.trace("blah")
            logger.prefix(the_prefix).trace("bloo")
            logger.prefix(the_prefix).trace("aweg")
            logger.trace("aweg")

        assert("blah" in caplog.messages)
        assert("(1) bloo" in caplog.messages)
        assert("(2) aweg" in caplog.messages)
        assert("aweg" in caplog.messages)
