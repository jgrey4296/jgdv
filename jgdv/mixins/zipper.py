#!/usr/bin/env python3
"""

"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import abc
import sys
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
from random import randint
import re
import time
import types
import zipfile
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Match,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    final,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Maybe

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


zip_name_default         : Final[str]                   = "default"
zip_overwrite_default    : Final[bool]                  = False
zip_compression_default  : Final[str]                   = "ZIP_DEFLATED"
zip_level_default        : Final[int]                   = 4

zip_choices              : Final[list[tuple[str, str]]] = [
    ("none", "No compression"),
    ("zip", "Default Zip Compression"),
    ("bzip2", "bzip2 Compression"),
    ("lzma", "lzma compression")
]

class Zipper_m:
    """
    Add methods for manipulating zip files.
    Can set a self.zip_root path, where added files with be relative to
    """
    zip_name            : str                   = zip_name_default
    zip_overwrite       : bool                  = zip_overwrite_default
    zip_root            : Maybe[pl.Path]        = None
    _zip_compression    : str                   = zip_compression_default
    _zip_compress_level : int                   = zip_level_default

    def _zip_get_compression_settings(self) -> tuple[int, int]:
        match self.args:
            case { "compression": "none", "level": x }:
                return zipfile.ZIP_STORED, x
            case { "compression": "zip", "level": x }:
                return zipfile.ZIP_DEFLATED, x
            case { "compression": "bzip2", "level": x }:
                return zipfile.ZIP_BZIP2, x
            case { "compression" : "lzma", "level": x}:
                return zipfile.ZIP_LZMA, x
            case _:
                return self._zip_compression, self._zip_compress_level

    def zip_set_root(self, fpath:pl.Path):
        """ set the filesystem that acts as the root for paths to be added to the zip file """
        self.zip_root = fpath

    def zip_create(self, fpath:pl.Path):
        """ Create a new zipfile. will overwrite an existing zip if 'zip_overwrite' is set """
        assert(fpath.suffix== ".zip")
        if self.zip_overwrite and fpath.exists():
            fpath.unlink()
        elif fpath.exists():
            return

        logging.info("Creating Zip File: %s", fpath)
        now = datetime.datetime.strftime(datetime.datetime.now(), "%Y:%m:%d::%H:%M:%S")
        record_str = f"Zip File created at {now} for doot task: {self.basename}"
        compress_type, compress_level = self._zip_get_compression_settings()

        with zipfile.ZipFile(fpath, mode='w', compression=compress_type, compresslevel=compress_level, allowZip64=True ) as targ:
            targ.writestr(".taskrecord", record_str)

    def zip_add_paths(self, fpath:pl.Path, *args:pl.Path):
        """
        Add specific files to the zip.
          Will Create the zip if it doesn't exist
        """
        logging.info("Adding to Zipfile: %s : %s", fpath, args)
        assert(fpath.suffix == ".zip")
        self.zip_create(fpath)

        root = self.zip_root or pl.Path()
        paths = [pl.Path(x) for x in args]
        compress_type, compress_level = self._zip_get_compression_settings()
        with zipfile.ZipFile(fpath, mode='a', compression=compress_type, compresslevel=compress_level, allowZip64=True ) as targ:
            for file_to_add in paths:
                try:
                    relpath = file_to_add.relative_to(root)
                    attempts = 0
                    write_as = relpath
                    while str(write_as) in targ.namelist():
                        if attempts > 10:
                            logging.warning(f"Couldn't settle on a de-duplicated name for: {file_to_add}")
                            break
                        logging.debug(f"Attempted Name Duplication: {relpath}", file=sys.stderr)
                        write_as = relpath.with_stem(f"{relpath.stem}_{hex(randint(1,100))}")
                        attempts += 1

                    targ.write(str(file_to_add), write_as)

                except ValueError:
                    relpath = root / pl.Path(file_to_add).name
                except FileNotFoundError as err:
                    logging.warning(f"Adding File to Zip {fpath} failed: {err}", file=sys.stderr)

    def zip_globs(self, fpath:pl.Path, *globs:str, ignore_dots=False):
        """
        Add files chosen by globs to the zip, relative to the cwd
        """
        logging.debug("Zip Globbing: %s : %s", fpath, globs)
        assert(fpath.suffix == ".zip")
        self.zip_create(fpath)

        root                          = self.zip_root or pl.Path()
        compress_type, compress_level = self._zip_get_compression_settings()
        with zipfile.ZipFile(fpath, mode='a', compression=compress_type, compresslevel=compress_level, allowZip64=True) as targ:
            for globstr in globs:
                result = list(root.glob(globstr))
                logging.info(f"Globbed: {root}/{globstr} : {len(result)}")
                for globf in result:
                    try:
                        if globf.stem[0] == "." and ignore_dots:
                            continue
                        relpath = pl.Path(globf).relative_to(root)
                        match str(relpath) in targ.namelist():
                            case True:
                                logging.warning("Duplication Attempt: %s -> %s", globf, relpath)
                            case False:
                                targ.write(str(globf), relpath)
                    except FileNotFoundError as err:
                        logging.warning(f"Adding File to Zip {fpath} failed: {err}", file=sys.stderr)

    def zip_add_str(self, fpath:pl.Path, fname:str, text:str):
        """ add a string of text to a zip file as a new file """
        assert(fpath.suffix == ".zip")
        self.zip_create(fpath)

        compress_type, compress_level = self._zip_get_compression_settings()
        with zipfile.ZipFile(fpath, mode='a', compression=compress_type, compresslevel=compress_level, allowZip64=True) as targ:
            match fname in targ.namelist():
                case True:
                    logging.warning("Duplication Attempt: %s -> %s", fpath, fname)
                case False:
                    targ.writestr(fname, text)


    def zip_get_contents(self, fpath:pl.Path) -> list[str]:
        with zipfile.Zipfile(fpath):
            return zipfile.namelist()


    def zip_unzip_to(self, fpath:pl.Path, *zips:pl.Path, fn=None):
        """
        extract everything or everything that returns true from fn, from all zips given
        into subdirs of fpath
        """
        fn = fn or (lambda x: True)

        for zipf in zips:
            logging.debug("Extracting: %s (%s) to %s", zipf, fn, fpath)
            (fpath / zipf.stem).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zipf) as targ:
                subset = [x for x in targ.namelist() if fn(x)]
                targ.extractall(fpath / zipf.stem, members=subset)

    def zip_unzip_concat(self, fpath:pl.Path, *zips:pl.Path, member=None, header=b"\n\n#------\n\n", footer=b"\n\n#------\n\n"):
        """ Unzip a member file in a multiple zip files,
          append their text contents into a single file """
        assert(member is not None)
        with open(fpath, "ab") as out:
            for zipf in zips:
                try:
                    logging.debug("Concating: %s (%s) to %s", zipf, member, fpath)
                    with zipfile.ZipFile(zipf) as targ:
                        data = targ.read(member)
                        if header:
                            out.write(header)
                        out.write(data)
                        if footer:
                            out.write(footer)

                except Exception as err:
                    logging.warning("Issue reading: %s : %s", zipf, err)

    def zip_test(self, *zips:pl.Path):
        """ Test the validity of zip files """
        for zipf in zips:
            with zipfile.ZipFile(zipf) as targ:
                result = targ.testzip()
                if result is not None:
                    logging.warning("Issue with %s : %s", zipf, targ)


    def zip_contains(self, zip:pl.Path, *names:str|pl.Path) -> bool:
        """ test that a zip file contains multiple filenames"""
        with zipfile.ZipFile(zip, "r") as zipf:
            contents = zipf.namelist()

        missing = [x for x in names if x not in contents]
        if bool(missing):
            logging.info("Zip file %s is missing : %s", zip, missing)

        return bool(missing)
