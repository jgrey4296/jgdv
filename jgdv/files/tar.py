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

printer = logmod.getLogger("doot._printer")

from time import sleep
import sh
import shutil
import tomlguard as TG
import jgdv
from jgdv.keys import JGDVKey

##-- expansion keys
TO_KEY             : Final[JGDVKey] = JGDVKey.make("to")
FROM_KEY           : Final[JGDVKey] = JGDVKey.make("from")
UPDATE             : Final[JGDVKey] = JGDVKey.make("update_")
PROMPT             : Final[JGDVKey] = JGDVKey.make("prompt")
PATTERN            : Final[JGDVKey] = JGDVKey.make("pattern")
SEP                : Final[JGDVKey] = JGDVKey.make("sep")
TYPE_KEY           : Final[JGDVKey] = JGDVKey.make("type")
AS_BYTES           : Final[JGDVKey] = JGDVKey.make("as_bytes")
FILE_TARGET        : Final[JGDVKey] = JGDVKey.make("file")
RECURSIVE          : Final[JGDVKey] = JGDVKey.make("recursive")
LAX                : Final[JGDVKey] = JGDVKey.make("lax")
##-- end expansion keys

COMP_TAR_CMD  = sh.tar.bake("-cf", "-")
COMP_GZIP_CMD = sh.gzip.bake("--best")
DECOMP_CMD    = sh.tar.bake("-xf")

@jgdv.check_protocol
class TarCompressAction(Action_p):
    """ Compresses a target into a .tar.gz file """

    @JGDVKey.kwrap.paths("file")
    @JGDVKey.kwrap.paths("to", hint={"on_fail":None})
    def __call__(self, spec, state, file, to):
        target = file
        output = to or target.with_suffix(target.suffix + ".tar.gz")

        if output.exists():
            raise doot.errors.DootActionError("Compression target already exists")
        if target.is_dir():
            COMP_GZIP_CMD(_in=COMP_TAR_CMD("-C", target, ".", _piped=True), _out=output)
        else:
            COMP_GZIP_CMD(_in=COMP_TAR_CMD("-C", target.parent, target.name, _piped=True), _out=output)

@jgdv.check_protocol
class TarDecompressAction(Action_p):
    """ Decompresses a .tar.gz file """

    @JGDVKey.kwrap.paths("file", "to")
    def __call__(self, spec, state, file, to):
        target = file
        output = to
        if not ".tar.gz" in target.name:
            printer.warning("Decompression target isn't a .tar.gz", target)
            return ActionResponseEnum.FAIL

        DECOMP_CMD(target, "-C", output)


@jgdv.check_protocol
class TarListAction(Action_p):
    """ List the contents of a tar archive """

    @JGDVKey.kwrap.paths("from")
    @JGDVKey.kwrap.redirects("update_")
    def __call__(self, spec, state, _from, _update):
        target = _from
        if "".join(target.suffixes) != ".tar.gz":
            printer.warning("Trying to list the contents of a non-tar archive")
            return ActionResponseEnum.FAIL

        result = sh.tar("--list", "-f", str(target))
        lines = result.split("\n")
        return { _update : lines }


