#!/usr/bin/env python3
"""

"""
# ruff: noqa: PLR0912
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
import types
import weakref
from collections.abc import Callable, Generator, Iterable, Iterator, Mapping, MutableMapping, Sequence
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 1st party imports
from jgdv import Maybe
from jgdv.enums import LoopControl_e
from jgdv.structs.dkey import DKey
# ##-- end 1st party imports

from jgdv import identity_fn

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType, Never
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

MARKER       : Final[str]        = ".marker"
walk_ignores : Final[list[str]]  = ['.git', '.DS_Store', "__pycache__"] # TODO use a .ignore file
walk_halts   : Final[list[str]]  = [".doot_ignore"]

class PathManip_m:
    """
      A Mixin for common path manipulations
    """

    def _calc_path_parts(self, fpath:pl.Path, roots:list[pl.Path]) -> dict:
        """ take a path, and get a dict of bits which aren't methods of Path
          if no roots are provided use cwd
        """
        assert(fpath is not None)
        assert(isinstance(roots, list))

        temp_stem  = fpath
        # This handles "a/b/c.tar.gz"
        while temp_stem.stem != temp_stem.with_suffix("").stem:
            temp_stem = temp_stem.with_suffix("")

        return {
            'rpath'   : self._get_relative(fpath, roots),
            'fstem'   : temp_stem.stem,
            'fparent' : fpath.parent,
            'fname'   : fpath.name,
            'fext'    : fpath.suffix,
            'pstem'   : fpath.parent.stem,
            }

    def _build_roots(self, *sources:Mapping, roots:Maybe[list[str|DKey]]=None) -> list[pl.Path]:
        """
        convert roots from keys to paths
        """
        roots   = roots or []
        results = []
        for root in roots:
            root_key = DKey(root, fallback=root, mark=DKey.Mark.PATH)
            results.append(root_key.expand(*sources))
        else:
            return results

    def _get_relative(self, fpath:pl.Path, roots:Maybe[list[pl.Path]]=None) -> pl.Path:
        """ Get relative path of fpath.
          if no roots are provided, default to using cwd
        """
        logging.debug("Finding Relative Path of: %s using %s", fpath, roots)
        if not fpath.is_absolute():
            return fpath

        roots = roots or [pl.Path.cwd()]

        for root_path in roots:
            try:
                return fpath.relative_to(root_path)
            except ValueError:
                continue

        msg = f"{fpath} is not able to be made relative"
        raise ValueError(msg, roots)

    def _shadow_path(self, rpath:pl.Path, shadow_root:pl.Path) -> pl.Path:
        """ take a relative path, apply it onto a root to create a shadowed location """
        raise NotImplementedError()

    def _find_parent_marker(self, fpath:pl.Path, marker:Maybe[str]=None) -> Maybe[pl.Path]:
        """ Go up the parent list to find a marker file, return the dir its in """
        marker = marker or MARKER
        for p in fpath.parents:
            if (p / marker).exists():
                return p

        return None

    def _normalize(self, path:pl.Path, *, root:Maybe[pl.Path]=None, symlinks:bool=False) -> pl.Path:
        """
          a basic path normalization
          expands user, and resolves the location to be absolute
        """
        result : pl.Path = path
        if symlinks and path.is_symlink():
            msg = "symlink normalization"
            raise NotImplementedError(msg, path)

        match result.parts:
            case ["~", *_]:
                result = result.expanduser().resolve()
            case ["/", *_]:
                pass
            case _ if root:
                result = (root / path).expanduser().resolve()
            case _:
                pass

        return result

class Walker_m:
    """ A Mixin for walking directories,
      written for py<3.12
      """
    control_e = LoopControl_e

    def walk_all(self, roots:list[pl.Path], *, exts:Maybe[list[str]]=None, rec:bool=False, fn:Maybe[Callable]=None) -> list[dict]:
        """
        walk all available targets,
        and generate unique names for them
        """
        result : list = []
        exts          = exts or []
        match rec:
            case True:
                for root in roots:
                    result += self.walk_target_deep(root, exts=exts, fn=fn)
            case False:
                for root in roots:
                    result += self.walk_target_shallow(root, exts=exts, fn=fn)

        return result

    def walk_target_deep(self, target:pl.Path, *, exts:Maybe[list[str]]=None, fn:Maybe[Callable]=None) -> Generator[pl.Path]:
        logging.info("Deep Walking Target: %s : exts=%s", target, exts)
        exts = exts or []
        fn   = fn or identity_fn
        if not target.exists():
            return None

        queue = [target]
        while bool(queue):
            current = queue.pop()
            if not current.exists():
                continue
            if current.name in walk_ignores:
                continue
            if current.is_dir() and any((current / x).exists() for x in walk_halts):
                continue
            if bool(exts) and current.is_file() and current.suffix not in exts:
                continue
            match fn(current):
                case self.control_e.yes:
                    yield current
                case True if current.is_dir():
                    queue += sorted(current.iterdir())
                case True | self.control_e.yesAnd:
                    yield current
                    if current.is_dir():
                        queue += sorted(current.iterdir())
                case False | self.control_e.noBut if current.is_dir():
                    queue += sorted(current.iterdir())
                case None | False:
                    continue
                case self.control_e.no | self.control_e.noBut:
                    continue
                case _ as x:
                    msg = "Unexpected filter value"
                    raise TypeError(msg, x)

    def walk_target_shallow(self, target:pl.Path, *, exts:Maybe[list[str]]=None, fn:Maybe[Callable]=None) -> Generator:
        logging.debug("Shallow Walking Target: %s", target)
        exts = exts or []
        fn = fn or identity_fn
        if target.is_file():
            fn_fail = fn(target) in [None, False, self.control_e.no, self.control_e.noBut]
            ignore  = target.name in walk_ignores
            bad_ext = (bool(exts) and target.suffix in exts)
            if not (fn_fail or ignore or bad_ext):
                yield target
            return None

        for x in target.iterdir():
            fn_fail = fn(x) in [None, False, self.control_e.no, self.control_e.noBut]
            ignore  = x.name in walk_ignores
            bad_ext = bool(exts) and x.is_file() and x.suffix not in exts
            if not (fn_fail or ignore or bad_ext):
                yield x
