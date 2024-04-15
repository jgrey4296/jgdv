"""
Provides the main RBTree class
"""
##-- imports
import logging as root_logger
from dataclasses import InitVar, dataclass, field
from functools import partial
from types import FunctionType
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence,
                    Set, Tuple, TypeVar, Union, cast)
##-- end imports

logging = root_logger.getLogger(__name__)

from .comparison_functions import (Directions, default_comparison, default_equality)
from .node import Node
from .operations import rb_tree_delete, rb_tree_fixup

@dataclass
class RBTreeData:
    """ A Red-Black Tree Implementation
    Properties of RBTrees:
    1) Every node is Red Or Black
    2) The root is black
    3) Every leaf is Black, leaves are null nodes
    4) If a node is red, it's children are black
    5) All paths from a node to its leaves contain the same number of black nodes
    """

    cmp_func     : Callable = field(default=default_comparison)
    eq_func      : Callable = field(default=default_equality)
    cleanup_func : Callable = field(default=lambda x: [])

    nodes : List[Node] = field(default_factory=list)
    root : Node = field(default=None)

    def __post_init__(self):
        """ Initialise the rb tree container, ie: the node list """
        #Default Comparison and Equality functions with dummy data ignored
        assert(isinstance(cmp_func, (partial, FunctionType)))
        assert(isinstance(eq_func, (partial, FunctionType)))

    def __len__(self):
        return len(self.nodes)

    def __repr__(self):
        if self.root is None:
            return "<RBTree>"

        return "<RBTree: {}>".format(len(self))
