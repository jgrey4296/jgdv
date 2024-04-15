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
class LazyComponentWriter:
    """
    An Accessor for appending data to files easily.
    comp_dir is the directory to write to
    components is the sets of tweet id's forming components

    component files are json dicts: {"tweets: [], "users": [] }

    """
    comp_dir      : pl.Path                         = field()
    components    : List[Set[str]]                  = field()

    tweet_mapping : Dict[str, set[ComponentWriter]] = field(default_factory=lambda: defaultdict(lambda: set()))
    user_mapping  : Dict[str, set[ComponentWriter]] = field(default_factory=lambda: defaultdict(lambda: set()))
    writers       : List[ComponentWriter]           = field(default_factory=list)
    missing       : Set[str]                        = field(default_factory=set)

    def __post_init__(self):
        # For each component
        for comp_set in self.components:
            # Create a writer
            comp_obj = ComponentWriter(self.comp_dir)
            assert(not comp_obj.path.exists())
            # And pair each tweet id with that writer
            self.writers.append(comp_obj)
            for x in comp_set:
                self.tweet_mapping[x].add(comp_obj)

    def __contains__(self, value):
        return value in self.tweet_mapping

    def finish(self):
        for comp_f in self.writers:
            comp_f.finish()

        self._write_summary()

    def _write_summary(self):
        summary_path = self.comp_dir / "components.summary"
        lines = [x.summary() for x in self.writers]
        summary_path.write_text("\n".join(lines))

    def add_tweets(self, data:list):
        for tweet in data:
            id_s    = tweet.get('id_str', None)
            user_id = tweet.get('user', {}).get('id_str', None)
            if id_s is None:
                continue
            if id_s not in self.tweet_mapping:
                self.missing.add(id_s)
                continue

            for comp_f in self.tweet_mapping[id_s]:
                comp_f.add(tweet)
                # Each tweet maps its user to the writer as well, for the user pass
                self.user_mapping[user_id].add(comp_f)


    def add_users(self, data:dict):
        for user_id, user in data.items():
            if user_id not in self.user_mapping:
                self.missing.add(user_id)
                continue

            for comp_f in self.user_mapping[user_id]:
                comp_f.add(user, data_type="users")

    def __enter__(self):
        return self

    def __exit__(self, atype, value, traceback):
        self.finish()
