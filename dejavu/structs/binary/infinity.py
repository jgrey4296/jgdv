#!/usr/bin/env python3
"""
Construct.py based readers for bioware infinity engine file formats:
CHITIN.KEY
(todo) .BIF
(todo) .DLG
(todo) .TLK
(todo) .2DA
(todo) .BS
(todo) .BCS
(todo) .MAZE
(todo) .STR

https://gibberlings3.github.io/iesdp/file_formats/index.htm

Notes:
numbers are little endian
"""
##-- imports
from __future__ import annotations

import types
import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

##-- end imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import construct as C

##-- file types
infinity_file_types = {
    0x0001 : ".bmp",
    0x0002 : ".mve",
    0x0004 : ".wav",
    0x0005 : ".wfx",
    0x0006 : ".plt",
    0x03e8 : ".bam",
    0x03e9 : ".wed",
    0x03ea : ".chu",
    0x03eb : ".tis",
    0x03ec : ".mos",
    0x03ed : ".itm",
    0x03ee : ".spl",
    0x03ef : ".bcs",
    0x03f0 : ".ids",
    0x03f1 : ".cre",
    0x03f2 : ".are",
    0x03f3 : ".dlg",
    0x03f4 : ".2da",
    0x03f5 : ".gam",
    0x03f6 : ".sto",
    0x03f7 : ".wmp",
    0x03f8 : ".chr",
    0x03f9 : ".bs",
    0x03fa : ".chr",
    0x03fb : ".vvc",
    0x03fc : ".vef",
    0x03fd : ".pro",
    0x03fe : ".bio",
    0x03ff : ".wbm",
    0x0400 : ".fnt",
    0x0402 : ".gui",
    0x0403 : ".sql",
    0x0404 : ".pvrz",
    0x0405 : ".glsl",
    0x0408 : ".menu",
    0x0409 : ".menu",
    0x040a : ".ttf",
    0x040b : ".png",
    0x040c : ".bah",
    0x0802 : ".ini",
    0x0803 : ".src",
    }

##-- end file types

class BioWareInfinityBinaryMixin:
    """
    Mixin for building parts of infinity engine file formats

    """
    Word   = C.Int16ul
    DWord  = C.Int32ul
    file_types = infinity_file_types

    ##-- top level
    def build_key_v1_format(self) -> C.Struct:
        """
        Build a construct parser for infinity engine KEY format file
        Structure:
        header, [bif descriptions], [resource descriptions]

        see:
        https://gibberlings3.github.io/iesdp/file_formats/ie_formats/key_v1.htm
        """
        return C.Struct("header" / self._key_v1_header,
                        C.Seek(C.this.header.bif_offset),
                        "bif_descs" / self._key_v1_bif_description[C.this.header.bif_num],
                        C.Seek(C.this.header.res_offset),
                        "res_descs" / self._key_v1_resource_description[C.this.header.res_num]
                        )

    def build_bif_v1_format(self) -> C.Struct:
        """
        https://gibberlings3.github.io/iesdp/file_formats/ie_formats/bif_v1.htm
        """
        return C.Struct("header" / self._bif_v1_header,
                        C.Seek(C.this.header.offset),
                        "file_entries" / self._bif_v1_entry[C.this.header.file_entries_count],
                        C.Check(C.len_(C.this.file_entries) == C.this.header.file_entries_count),
                        "tileset_entries" / self._bif_v1_tileset[C.this.header.tileset_entries_count],
                        C.Check(C.len_(C.this.tileset_entries) == C.this.header.tileset_entries_count),
                        )

    def build_bifc_v1_format(self) -> C.Struct:
        return C.Struct("header" / self._bif_compressed_v1_header,
                        "blocks" / C.GreedyRange(self._bif_compressed_v1_block),
                        )

    def build_tlk_v1_format(self) -> C.Struct:
        """
        https://gibberlings3.github.io/iesdp/file_formats/ie_formats/tlk_v1.htm
        """
        return C.Struct("header" / self._tlk_v1_header,
                        C.Seek(18),
                        "entries" / self._tlk_v1_entries[C.this.header.entry_count],
                        )

    def build_dlg_v1_format(self) -> C.Struct:
        """
        https://gibberlings3.github.io/iesdp/file_formats/ie_formats/dlg_v1.htm
        """
        return C.Struct("header"              / self._dlg_v1_header,
                        "state_table"         / C.Pointer(C.this.header.state_offset,              self._dlg_v1_state[C.this.header.state_count]),
                        "transition_table"    / C.Pointer(C.this.header.transition_offset,         self._dlg_v1_transition[C.this.header.transition_count]),
                        "state_triggers"      / C.Pointer(C.this.header.state_trigger_offset,      self._dlg_v1_data[C.this.header.state_trigger_count]),
                        "transition_triggers" / C.Pointer(C.this.header.transition_trigger_offset, self._dlg_v1_data[C.this.header.transition_trigger_count]),
                        "actions"             / C.Pointer(C.this.header.action_offset,             self._dlg_v1_data[C.this.header.action_count])
                        )

    def build_2da_format(self) -> C.Struct:
        """
        https://gibberlings3.github.io/iesdp/file_formats/ie_formats/2da.htm
        TODO detect 0xff for encryption
        """
        raise NotImplementedError()

    def build_src_format(self) -> C.Struct:
        """
        https://gibberlings3.github.io/iesdp/file_formats/ie_formats/src.htm
        """
        return C.Struct("entry_count" / self.DWord,
                        "entries" / C.Struct("str_ref" / self.DWord,
                                             "weight"  / self.DWord)[C.this.entry_count]
                        )

    ##-- end top level

    ##-- components

    @property
    def _key_v1_header(self) -> C.Struct:
        return C.Struct(C.Const(b"KEY"), C.Padding(1),
                        "version"    / C.FixedSized(4, C.NullStripped(C.GreedyString("ascii"))),
                        "bif_num"    / self.DWord,
                        "res_num"    / self.DWord,
                        "bif_offset" / self.DWord,
                        "res_offset" / self.DWord,
                        )

    @property
    def _key_v1_bif_description(self) -> C.Struct:
        return C.Struct("pos" / C.Tell,
                        "id" / C.Computed(C.this._index),
                        "file_len"    / self.DWord,
                        "name_offset" / self.DWord,
                        "name"        / C.Pointer(C.this._.name_offset, C.CString("ascii")),
                        "name_len"    / self.Word,
                        "location"    / C.FlagsEnum(self.Word, data=1, cache=2, cd1=4, cd2=8, cd3=16, cd5=24, cd6=32),
                        )

    @property
    def _key_v1_resource_description(self) -> C.Struct:
        return C.Struct("id"           / C.Computed(C.this._index),
                        "name"         / C.PaddedString(8, "ascii"),
                        "type"         / self.Word,
                        "resource_key" / self._key_v1_resource_key
                        )

    @property
    def _key_v1_resource_key(self) -> C.Struct:
        return C.ByteSwapped(C.BitStruct(
            "bif"  / C.BitsInteger(12),
            "tile" / C.BitsInteger(6),
            "file" / C.BitsInteger(14)
        ))

    @property
    def _bif_v1_header(self) -> C.Struct:
        return C.Struct(C.Const(b"BIFF"), C.Const(b'V1  '),
                        "file_entries_count"    / self.DWord,
                        "tileset_entries_count" / self.DWord,
                        "offset"                / self.DWord, # from start of file
                        )

    @property
    def _bif_v1_entry(self) -> C.Struct:
        return C.Struct("resource_key" / self._key_v1_resource_key,
                        "offset"       / self.DWord, # from start of file
                        "size"         / self.DWord,
                        "type"         / self.Word,
                        self.Word,
                        "data"         / C.Pointer(C.this.offset, C.Array(C.this.size, C.Byte)),
                        )

    @property
    def _bif_v1_tileset(self) -> C.Struct:
        return C.Struct("resource_key" / self._key_v1_resource_key,
                        "offset"       / self.DWord,
                        "count"        / self.DWord,
                        "size"         / self.DWord,
                        "type"         / C.Const(b'\x3eb'),
                        self.Word
                        # Data is ignored for now
                        )

    @property
    def _bif_compressed_v1_header(self) -> C.Struct:
        return C.Struct(C.Const(b"BIFC"), c.Const(b'V1.0'),
                        "size" / self.DWord
                        )

    @property
    def _bif_compressed_v1_block(self) -> C.Struct:
        return C.Struct("decompressed_size" / self.DWord,
                        "compressed_size"   / self.DWord,
                        "data"              / C.FixedSized(C.this.compressed_size, C.Compressed(C.GreedyBytes, "zlib")),
                        )

    @property
    def _tlk_v1_header(self) -> C.Struct:
        # 4 dword : offset from SoF to string data
        return C.Struct(C.Const(b"TLK "), C.Const(b"V1  "),
                        "language"      / self.Word,
                        "entry_count"   / self.DWord,
                        "string_offset" / self.DWord,
                        )

    @property
    def _tlk_v1_entries(self) -> C.Struct:
        metadata = C.FlagsEnum(self.Word,
                               message_data=1,
                               sound=2,
                               standard_message=4,
                               token=8
                               )

        return C.Struct("index"           / C.Computed(C.this._index),
                        "position"        / C.Tell,
                        "metadata"        / metadata,
                        "sound"           / self._tlk_v1_resref,
                        "volume"          / self.DWord,
                        "pitch"           / self.DWord,
                        "relative_offset" / self.DWord,
                        "length"          / self.DWord,
                        "full_offset"     / C.Computed(C.this._.header.string_offset + C.this.relative_offset),
                        # C.Probe(),
                        "data"            / C.Pointer(C.this.full_offset, C.FixedSized(C.this.length, C.NullStripped(C.GreedyString("utf-8")))),
                        # C.Probe(C.this.data),
                        )

    @property
    def _tlk_v1_strref(self) -> C.Struct:
        return C.Array(4, C.Byte)

    @property
    def _tlk_v1_resref(self) -> C.Struct:
        return C.FixedSized(8, C.Byte)

    @property
    def _dlg_v1_header(self) -> C.Struct:
       return C.Struct(C.Const(b"DLG "), C.Const(b"V1.0"),
                       "state_count"               / self.DWord,
                       "state_offset"              / self.DWord,
                       "transition_count"          / self.DWord,
                       "transition_offset"         / self.DWord,
                       "state_trigger_offset"      / self.DWord,
                       "state_trigger_count"       / self.DWord,
                       "transition_trigger_offset" / self.DWord,
                       "transition_trigger_count"  / self.DWord,
                       "action_offset"             / self.DWord,
                       "action_count"              / self.DWord,
                       # "interruption"              / C.Enum(self.DWord, ),
                    )

    @property
    def _dlg_v1_state(self) -> C.Struct:
        return C.Struct("actor_response_string_reference" / self._tlk_v1_strref,
                        "transition_index"  / self.DWord,
                        "transition_count"  / self.DWord, # state transitions = transition_index -> (transition_index + transition_count) - 1
                        "trigger_index"     / self.DWord) # 0xFFFFFFFF if no triggers

    @property
    def _dlg_v1_transition(self) -> C.Struct:
        metadata = C.FlagsEnum(self.DWord,
                               associated_text=1,
                               trigger=2,
                               action=4,
                               terminates=8,
                               journal=16,
                               interrupt=32,
                               add_unsolved_quest_journal=64,
                               add_journal=128,
                               add_solved_quest_journal=256,
                               delayed_script_execution=512,
                               clear_actions=1024,
                               )

        return C.Struct(
            "metadata"                    / metadata,
            "transition_string_reference" / self._tlk_v1_strref,
            "journal_string_reference"    / self._tlk_v1_strref,
            "trigger_index"               / self.DWord,
            "action_index"                / self.DWord,
            "next_dlg_resource_ref"       / self._tlk_v1_resref,
            "next_state_index"            / self.DWord
        )

    @property
    def _dlg_v1_data(self) -> C.Struct:
        # state trigger / transition triggr / action
        return C.Struct("offset" / self.DWord,
                        "length" / self.DWord,
                        "text"   / C.Pointer(C.this.offset, C.FixedSized(C.this.length, C.NullStripped(C.GreedyString("ascii")))),
                        )

    ##-- end components
