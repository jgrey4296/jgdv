"""
Utility decorators
"""
##-- imports
from __future__ import annotations

import logging as logmod
from functools import wraps
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence,
                    Set, Tuple, TypeVar, Union, cast)

logging = logmod.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # tc only imports
    pass

##-- end imports

from jgdv._interfaces.decorator import DejaVuDecorator_i

class LogReturn(DejaVuDelayDecorator_i):
    """
    Utility Decorator to log a functions return value at a set level
    """

    def __init__(self, prefix, level=logmod.DEBUG, msg=None, logger=None):
        super().__init__()
        self._prefix = prefix
        self._level  = level
        self._msg    =  msg or "{prefix} result: {result}"
        self._logger = logger or logmod.getLogger("dejavu._returns")

    def _wrapper(self, *args, **kwargs):
        result = self._func(*args, **kwargs)
        log_msg = self._msg.format(prefix=self._prefix, result=result)
        self._logger.log(level, log_msg)
        return result
