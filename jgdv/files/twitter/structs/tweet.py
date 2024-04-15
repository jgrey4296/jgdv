#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class TwitterTweet:
    id_s         : str
    base_user    : str
    is_quote     : bool                          = field(default=False)
    name         : str                           = field(init=False, default="Unknown")
    hash_tags    : List[str]                     = field(init=False, default_factory=list)
    quote        : Tuple[str, str, TwitterTweet] = field(init=False, default=None)
    reply_to     : Tuple[str, str]               = field(init=False, default=None)
    date         : datetime                      = field(init=False, default_factory=datetime.datetime.now)
    media        : dict                          = field(default_factory=media_dict)
    links        : list[str]                     = field(default_factory=list)
    level        : int                           = field(default=4)

    fav          : int = 0
    retweet      : int = 0
    text         : str = ""

    permalink_f  : str =  "[[https://twitter.com/{}/status/{}][/{}/{}]]"
