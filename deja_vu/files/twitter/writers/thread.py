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
from dejavu.files.org.file import OrgStrBuilder
from dejavu.files.twitter.writers.util import parse_date

media_dict : Final[Callable] = lambda: defaultdict(list)

@dataclass
class OrgThreadWriter:
    """ Given a thread object, build a string representation for it
    redirecting absolute media paths to relative
    """

    user          : str
    date          : datetime.datetime
    tags          : set[str]
    main          : list[TwitterTweet]       = field(default_factory=list)
    conversations : list[List[TwitterTweet]] = field(default_factory=list)
    uses          : set[str]                 = field(default_factory=set)
    links         : set[str]                 = field(default_factory=set)
    media         : dict                     = field(default_factory=media_dict)

    redirect_url  : str = "{}_files"
    date_re       : str = r"%a %b %d %H:%M:%S +0000 %Y"
    tag_pattern   : str = ":{}:"
    tag_sep       : str = ":"
    tag_col       : int = 80
    file_link_pattern : str = "[[file:./{}][{}]]"

    @staticmethod
    def build(thread:dict, tweets:list, users:list, source_tags:dict[str, set[str]]) -> OrgThreadWriter:
        logging.info("Creating thread")

        main_thread_ids = thread['main_thread']
        sub_thread_ids  = thread['rest']
        quote_ids       = thread['quotes']
        base_user       = thread["base_user"]
        tweet_lookup    = {x['id_str'] : x for x in tweets}
        tags            = {y.strip() for x in main_thread_ids for y in source_tags[x] if x in source_tags}
        users_lookup    = {x['id_str'] : x for x in users}

        min_thread_date = min(((x,parse_date(tweet_lookup[x]['created_at'], self.date_re))
                              for x in main_thread_ids if x in tweet_lookup), key=lambda v:v[1])
        thread_date = min_thread_date[1]

        obj = OrgThreadWriter(base_user, thread_date, tags)

        # add tweets of main thread
        for x in main_thread_ids:
            if x not in tweet_lookup:
                obj.main.append(TwitterTweet("null", base_user))
                continue

            obj.add_use(x)
            tweet_obj = TwitterTweet.build(base_user, tweet_lookup[x], users_lookup, tweet_lookup)
            obj.main.append(tweet_obj)
            for key, values in tweet_obj.media.items():
                obj.media[key] += values

            obj.links.update(tweet_obj.links)

        # Add sub conversations
        for conv in sub_thread_ids:
            conv_list = []
            for x in conv:
                if x not in tweet_lookup:
                    conv_list.append(TwitterTweet("null", base_user, level=5))
                    continue
                obj.add_use(x)
                tweet_obj = TwitterTweet.build(base_user, tweet_lookup[x], users_lookup, tweet_lookup, level=5)
                conv_list.append(tweet_obj)
                obj.media.update(tweet_obj.media)
                obj.links.update(tweet_obj.links)

            obj.conversations.append(conv_list)

        return obj

    def add_use(self, value):
        """
        Record a use of a tweet id
        """
        self.uses.add(value)

    @staticmethod
    def retarget_url(base, url):
        base_p = pl.Path(OrgThreadWriter.redirect_url.format(base))
        url_p  = pl.Path(url)
        logging.debug("Retargeting URL: %s", url_p.name)
        return str(base_p / url_p.name)


    def __str__(self):
        output = OrgStrBuilder()

        heading_str = f"Thread: {self.date}"
        tags_str = ""
        if bool(self.tags):
            tags_str = self.tag_pattern.format(self.tag_sep.join(self.tags))

        tag_pad = max(0, self.tag_col - len(heading_str))
        output.heading(2, f"{heading_str}{tag_pad*' '}{tags_str}")
        output.heading(3, "Main Thread")
        output.add(*self.main)

        output.heading(3, "Conversations: ", str(len(self.conversations)))
        for conv in self.conversations:
            if not bool(conv):
                continue

            output.heading(4, conv[0].at)
            output.add(*conv)

        output.heading(3, "Links: ", str(len(self.links)))
        output.links(self.links)
        output.nl

        output.heading(3, "Media: ", str(len(self.media)))
        retarget = lambda x: (OrgThreadWriter.retarget_url(self.user, x['url']), pl.Path(x['url']).name)
        media_urls = []
        media_urls += [retarget(media) for media in self.media.get('photo', [])]
        media_urls += [retarget(media) for media in self.media.get('video', [])]

        media_local =[self.file_link_pattern.format(*x) for x in media_urls]
        output.add(*media_local)
        output.nl

        return str(output)
