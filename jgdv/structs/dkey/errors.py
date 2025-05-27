#!/usr/bin/env python3
"""

"""

from __future__ import annotations

from jgdv.structs.strang.errors import StrangError

class DKeyError(StrangError):
    pass

class DecorationMismatch(DKeyError):
    pass
