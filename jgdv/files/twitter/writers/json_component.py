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

import networkx as nx

@dataclass
class ComponentWriter:
    """
    Simple interface to buffer writing tweets to a json file
    """
    dir_s        : pl.Path   = field()
    name_stem    : str       = field(default="component_{}")
    id_s         : str       = field(default_factory=lambda: str(uuid1()))
    suffix       : str       = field(default=".json")

    stored       : list[Any] = field(default_factory=list)
    tweet_ids    : set[str]  = field(default_factory=set)
    user_ids     : set[str]  = field(default_factory=set)
    write_count  : int       = field(default=20)
    state        : str       = field(default="pre")

    write_states : ClassVar[list[str]] = ["pre", "writing_tweets", "mid", "writing_users", "finished"]

    def __hash__(self):
        return id(self)

    @property
    def path(self):
        return (self.dir_s / self.name_stem.format(self.id_s)).with_suffix(self.suffix)

    def finish(self):
        """ Add the final ] to the file """
        self._maybe_dump(force=True)
        with open(self.path, 'a') as f:
            f.write("\n    ]\n}")
        self.state = "finished"

    def add(self, data, data_type="tweets"):
        """ Add a tweet lazily into the component file """
        match self.state, data_type:
            case "pre" | "writing_tweets", "tweets":
                self.stored.append(data)
                self.tweet_ids.add(data['id_str'])
                self._maybe_dump()
            case "pre" | "writing_tweets", "users":
                logging.debug("Switching Writer to users")
                self._maybe_dump(force=True)
                self.state = "mid"
                self.user_ids.add(data['id_str'])
                self.stored.append(data)
                self._maybe_dump()
            case "mid" | "writing_users", "users":
                self.stored.append(data)
                self.user_ids.add(data['id_str'])
                self._maybe_dump()
            case _:
                raise TypeError("Unexpected State for writer", self.state, data_type)

    def _maybe_dump(self, force=False):
        """
        Dump queued tweets into the component file
        """
        assert(not self.state == "finished")
        if (not force) and len(self.stored) < self.write_count:
            return
        if not bool(self.stored):
            return

        # convert to str, chop of brackets
        write_str = json.dumps(self.stored, indent=4)[2:-2]
        with open(self.path, 'a') as f:
            match self.state:
                case "pre":
                    f.write("{\n    \"tweets\": [\n")
                    self.state = "writing_tweets"
                case "writing_tweets" | "writing_users":
                    f.write(",\n")
                case "mid":
                    f.write("\n    ],\n    \"users\": [\n")
                    self.state = "writing_users"

            f.write(write_str)

        self.stored.clear()

    def summary(self):
        tweet_ids = " ".join(self.tweet_ids)
        user_ids  = " ".join(self.user_ids)
        comp_name = self.path.stem
        return f"Component: {comp_name} Counts: [{len(self.tweet_ids)} {len(self.user_ids)}] TweetIds: [{tweet_ids}] UserIds: [{user_ids}]"
