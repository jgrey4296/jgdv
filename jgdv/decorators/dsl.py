##-- imports
from __future__ import annotations
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Generic, Iterable,
                    Iterator, Mapping, Match, MutableMapping, Protocol,
                    Sequence, Tuple, TypeAlias, TypeGuard, TypeVar, cast)

from functools import wraps

##-- end imports

from jgdv._interfaces.decorator import DejaVuDecorator_i

T = TypeVar('T')

class EnsureDSLInit(DejaVuDecorator_i):
    """ Utility Decorator for DSLs  raising error if not initialised """

    def __call__(self, *args, **kwargs):
        if not self._parsers_initialised:
            raise RuntimeError("DSL Not Initialised")

        return self._func(self, *args, **kwargs)
