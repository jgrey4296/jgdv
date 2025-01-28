#!/usr/bin/env python3
"""

"""

from __future__ import annotations

from jgdv import JGDVError

class DKeyError(JGDVError):
    pass

class DecorationMismatch(DKeyError):
    pass
