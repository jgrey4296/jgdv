"""

"""
from __future__ import annotations

import logging as logmod
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)

logging = logmod.getLogger(__name__)

@dataclass
class ReplState:
    """ Data used for control of the repl """
    prompt        : str                            =  field(default="Prompt: ")
    prompt_ml     : str                            =  field(default="MLPrompt: ")
    prompt_bkup   : str                            =  field(default="")
    ctxs          : ContextSet_i                   =  field(default=None)
    collect_str   : list[str]                      =  field(default_factory=list)
    echo          : bool                           =  field(default=False)
    in_multi_line : bool                           =  field(default=False)
    indent        : int                            =  field(default=0)
    debug_data    : Any                            =  field(default=None)
    debugger      : Any                            =  field(default=None)
    last_err      : Any                            =  field(default=None)
    # run in alphabetical order:
    post_cmds     : dict[str, Callable[..., None]] =  field(default_factory=dict)
