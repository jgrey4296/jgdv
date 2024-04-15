#!/usr/bin/env python3
##-- imports
from __future__ import annotations

import pathlib as pl
import datetime
import json
import logging as logmod
from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence,
                    Set, Tuple, TypeVar, Union, cast)
from uuid import uuid1

import networkx as nx
##-- end imports

class OrgBuilderBase:

    link_pattern        : str = "[[{}]]"
    named_link_pattern  : str = "[[{}][{}]]"
    named_file_pattern  : str = "[[file:{}][{}]]"

