# pylint: disable=bad-whitespace
"""

Defines functions for parsers and parse -> data transform

"""
##-- imports
from __future__ import annotations

import logging as logmod

import pyparsing as pp

##-- end imports

logging = logmod.getLogger(__name__)

ATOM : str = TYPE_BASE

def strip_parse_type(s, loc, toks):
    """ Utility function to strip out parse data from return tuples,
    useful for:
    [("QUERY", actual_query)] -> [actual_query]

    NOTE: expects to be called from a group wrapping the actual parser
    """
    assert(all([isinstance(x, tuple) for x in toks[0]]))
    return [x[1] for x in toks[0]]

def deep_update_names(parser):
    logging.debug("Deep Updating Parser Names for {}", parser)
    queue = [parser]
    processed = set()

    while bool(queue):
        current = queue.pop(0)
        if current in processed:
            continue
        processed.add(current)

        if hasattr(current, "_defaultName"):
            setattr(current, "_defaultName", None)

        if hasattr(current, "expr"):
            queue.append(current.expr)
        elif hasattr(current, "exprs"):
            queue += current.exprs

def clear_parser_names(*parsers):
    logging.debug("Clearing Parser Names for: {}", parsers)
    for parser in parsers:
        # if hasattr(parser, "customName"):
        #     setattr(parser, "customName", None)

        if hasattr(parser, "_defaultName"):
            setattr(parser, "_defaultName", None)
