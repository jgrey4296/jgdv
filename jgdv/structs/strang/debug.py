#!/usr/bin/env python3
"""

"""
# ruff: noqa: PLW0211, ARG004

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from .strang import Strang
from . import errors

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol

if typing.TYPE_CHECKING:
    from uuid import UUID
    from . import _interface as API # noqa: N812

    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class StrangDebug:

    @staticmethod
    def debug(cls:type[API.Strang_p], text:str) -> str:
        """ Return a str of details about a str -> strang """
        hooks         = [x for x in dir(cls) if x.endswith("_h")]
        abs_sections  = StrangDebug._describe_section_specs(cls._sections)
        ang           = cls(text)
        sections      = StrangDebug._describe_text(cls, ang)
        raw_data      = StrangDebug._describe_raw_data(cls, ang)
        result        = [
            "",
            f"** Strang Debug of: {text} **",
            f"Type: {cls.__module__} : {cls.__qualname__}",
            f"Hooks: {hooks}",
            *abs_sections,
            *StrangDebug._describe_pre_process_results(cls, text),
            *StrangDebug._describe_process_results(cls, ang),
            *StrangDebug._describe_post_process_results(cls, ang),
            *sections,
            *raw_data,
            "----",
            "Result:",
            f"type(ang)  = {type(ang)}",
            f"str(ang)   = {ang:s}",
            f"ang[:]     = {ang[:]}",
            f"ang[:,:]   = {ang[:,:]}",
            "Formatting: ",
            f"ang:u     = {ang:u}",
            f"ang:a-    = {ang:a-}",
            f"ang:a     = {ang:a}",
            f"ang:a+    = {ang:a+}",
            f"{text} -> {ang}",
        ]
        return "\n".join(result)

    @staticmethod
    def _describe_pre_process_results(cls:type[API.Strang_p], text:str) -> list[str]:
        preproc  = cls._processor.pre_process(cls, text)
        result   = [
            "---- Pre-Process:",
            f"{text} -> {preproc}",
            "",
        ]
        return result

    @staticmethod
    def _describe_process_results(cls:type[API.Strang_p], actual:API.Strang_p) -> list[str]:
        section_slices  = [(x.start, x.stop) for x in actual.data.sections]
        word_slices     = [(x.start, x.stop) for x in actual.data.words]
        result          = [
            "---- Process: ",
            f"Sections:   {section_slices}",
            f"SecWords:   {actual.data.sec_words}",
            f"FlatIdx:    {actual.data.flat_idx}",
            f"Words:      {word_slices}",
            "",
        ]
        return result

    @staticmethod
    def _describe_post_process_results(cls:type[API.Strang_p], actual:API.Strang_p) -> list[str]:
        result = [
            "---- Post-Process:",

            "",
        ]
        return result

    @staticmethod
    def _describe_section_specs(secs:API.Sections_d) -> list[str]:
        result = [
            "---- Section Specs:",
            *(f"- {x.idx} : {x.name}. Case: ({x.case} {x.end}). " for x in secs),
            "",
        ]
        return result

    @staticmethod
    def _describe_text(cls:type[API.Strang_p], actual:API.Strang_p) -> list[str]:
        result = [
            "---- Section Text:",
            "Format: ..-(index[sec], index[word]) : FlatIndex : word : (meta, type[meta])",
        ]

        for i,sec in enumerate(actual.data.sec_words):
            result.append(f"- {actual.section(i).name}:")
            for j,idx in enumerate(sec):
                sl    = actual.data.words[idx]
                word  = actual[sl]
                match actual.data.meta[idx]:
                    case None:
                        meta = ""
                    case x:
                        meta = f"({x}, {type(x)})"

                result.append(f"..- ({i},{j}) : {idx} : {word} : {meta}")
        else:
            args_text       = actual[actual.data.args_start:]
            arg_len  : int  = len(actual.data.args) if actual.data.args else 0
            result += [
                "",
                f"- args ({arg_len}). Position: {actual.data.args_start}:",
                f"..- {args_text}",
                "",
            ]
            return result


    @staticmethod
    def _describe_raw_data(cls:type[API.Strang_p], actual:API.Strang_p) -> list[str]:
        result = [
            "---- Raw Data:",
            f"Meta:    {actual.data.meta}",
            f"UUID:    {actual.data.uuid}",
            "",
            ]
        return result

    @staticmethod
    def diff_uuids(this:UUID, that:UUID) -> str:
        this_ing : str = str(this)
        that_ing : str = str(that)
        result = [y if x==y else "_" for x,y in zip(this_ing, that_ing, strict=True)]
        return "".join(result)
