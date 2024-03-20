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

from collections import defaultdict
from dejavu.files.twitter.writers.util import parse_date

media_dict : Final[Callable] = lambda: defaultdict(list)

@dataclass
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

    @staticmethod
    def build(base, tweet, users, tweet_lookup, level=4, is_quote=False) -> TwitterTweet:
        obj                  = TwitterTweet(tweet['id_str'], base, is_quote=is_quote, level=level)

        obj.name         = users.get(tweet.get('user', {}).get('id_str', None), {}).get('screen_name', None)
        obj.hash_tags    = [x.get('text', "") for x in tweet.get('entities', {}).get('hashtags', [])]
        obj.reply_to     = (tweet.get('in_reply_to_screen_name', None), tweet.get('in_reply_to_status_id_str', None))
        obj.fav          = str(tweet.get('favorite_count', 0))
        obj.retweet      = str(tweet.get('retweet_count', 0))
        obj.text         = tweet.get('full_text', "")
        date_str : None | str = tweet.get('created_at', None)
        if date_str:
            obj.date         = parse_date(date_str)

        urls             = tweet.get('entities', {}).get('urls', [])
        obj.links        = {x.get('expanded_url', None) for x in urls}

        try:
            quote_id         = tweet.get('quoted_status_id_str', None)
            quoted_tweet     = tweet_lookup.get(quote_id, {})
            quote_user_id    = quoted_tweet.get('user', {}).get('id_str', None)
            quoted_user_name = users.get(quote_user_id, {}).get('screen_name', "Unknown")
            quoted_tweet     = TwitterTweet.build(base, tweet_lookup[quote_id], users, tweet_lookup, level=level+1, is_quote=True)
            obj.quote        = (quoted_user_name, quote_id, quoted_tweet)
            # obj.media += quoted_tweet.media
            obj.links.update(quoted_tweet.links)
        except KeyError:
            pass

        media = TwitterTweet.get_tweet_media(tweet)
        obj.media = media
        return obj

    def __str__(self):
        output     = OrgStrBuilder()
        tags       = ""
        tag_offset = 0
        if bool(self.hash_tags):
            tags       =  ":{}:".format(":".join(self.hash_tags))
            tag_offset =  max(0, 80-len(self.at))
            tags       = (tag_offset * " ") + tags

        quote_header = ""
        if self.is_quote:
            quote_header = "Quote: "
        output.heading(self.level, quote_header, self.at, tags)

        with output.drawer("PROPERTIES") as dr:
            dr.add("PERMALINK", self.permalink(self.name, self.id_s))
            if self.reply_to is not None and self.reply_to[0] is not None:
                dr.add("REPLY_TO", self.permalink(*self.reply_to))
            if self.quote is not None:
                dr.add("QUOTE", self.permalink(*self.quote[:2]))
            dr.add("FAVOURITE_COUNT", self.fav)
            dr.add("RETWEET_COUNT", self.retweet)
            dr.add("DATE", self.date.strftime(OrgThreadWriter.date_re))
            if self.is_quote:
                dr.add("IS_QUOTE", "t")

        output.add(re.sub("\n\*", "\n-*", self.text))
        output.nl

        retarget= lambda x: OrgThreadWriter.retarget_url(self.base_user, x['url'])
        media_urls = []
        media_urls += [retarget(media) for media in self.media.get('photo', [])]
        media_urls += [retarget(media) for media in self.media.get('video', [])]

        if bool(media_urls):
            with output.drawer("MEDIA") as dr:
                dr.add_file_links(*media_urls)

        # Links
        if bool(self.links):
            with output.drawer("LINKS") as dr:
                dr.add_keyless(*self.links)

        if self.quote is not None:
            output.add(self.quote[2])

        return str(output)

    @property
    def at(self):
        return f"@{self.name}"

    @staticmethod
    def permalink(name, id_s):
        return TwitterTweet.permalink_f.format(name, id_s, name, id_s)

    @staticmethod
    def get_tweet_media(tweet) -> dict:
        media = media_dict()
        to_process = []
        to_process += tweet.get('entities', {}).get('media', [])
        to_process += tweet.get('extended_entities', {}).get('media', [])

        for ent in to_process:
            url        = ent.get('media_url_https', "")
            # filename   = pl.Path(url).name

            datum = {
                "url"          : url,
                "expanded_url" : ent.get("expanded_url", ""),
                "alt_text"     : ent.get('ext_alt_text', ""),
                "type"         : ent.get('type', "n/a"),
                }

            media[datum["type"]].append(datum)

            if datum['type'] == "video":
                video_datum = datum.copy()
                mp4s = [x for x in ent.get('video_info', {}).get('variants', []) if x.get('content_type', None) == "video/mp4"]
                best_variant = max(mp4s, key=lambda x: x.get('bitrate', 0))
                best_url = best_variant.get('url', "").split("?")[0]
                if bool(best_url):
                    video_datum['url'] = best_url
                    media['video'].append(video_datum)

        return media
