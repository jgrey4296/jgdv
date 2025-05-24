#!/usr/bin/env python3
"""
TEST File updated

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202, B011

# Imports
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest
# ##-- end 3rd party imports

##--|
from .. import _interface as API # noqa: N812

from ..debug import StrangDebug
from ..strang import Strang
##--|

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
# from . import _interface as API # noqa: N812
# Dataclasses:
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

#
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

@pytest.mark.xfail
class TestStrangDebug:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        result = StrangDebug.debug(Strang, "head::body")
        logging.debug(result)
        assert(False)

    def test_with_args(self):
        result = StrangDebug.debug(Strang, "head::body[test]")
        logging.debug(result)
        assert(False)

    def test_with_multi_args(self):
        result = StrangDebug.debug(Strang, "head::body[test,blah]")
        logging.debug(result)
        assert(False)

    def test_uuid(self):
        result = StrangDebug.debug(Strang, "head::body.<uuid>")
        logging.debug(result)
        assert(False)

    def test_mark(self):
        result = StrangDebug.debug(Strang, "head::body.$head$")
        logging.debug(result)
        assert(False)

    def test_type_val(self):
        result = StrangDebug.debug(Strang, "head::body.<int:10>")
        logging.debug(result)
        assert(False)

    def test_complex(self):
        result = StrangDebug.debug(Strang, "head::body.<int:10>.d.<int:4>.$head$[<uuid>]")
        logging.debug(result)
        assert(False)

