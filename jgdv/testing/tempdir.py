#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

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
from uuid import UUID, uuid1

##-- end builtin imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import pytest
import os
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

@pytest.fixture
def wrap_tmp(tmp_path:pl.Path) -> Generator[pl.Path]:
    """ create a new temp directory, and change cwd to it,
      returning to original cwd after the test
      """
    logging.debug("Moving to temp dir")
    orig     = pl.Path().cwd()
    new_base = tmp_path / "test_root"
    new_base.mkdir()
    os.chdir(new_base)
    yield new_base
    logging.debug("Returning to original dir")
    os.chdir(orig)
