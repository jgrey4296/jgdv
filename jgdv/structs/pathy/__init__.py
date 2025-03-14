"""

"""
from __future__ import annotations

import sys
from typing import Final

PATH_REFACTORED_MINOR_VER : Final[int] = 12

if sys.version_info.minor < PATH_REFACTORED_MINOR_VER:
    msg = "Pathy needs 3.12+"
    raise RuntimeError(msg)

from .pathy import Pathy, Pure, Real, File, Dir, Wild
