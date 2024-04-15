"""

"""
##-- imports
from __future__ import annotations

import importlib
import logging as logmod
import re
import traceback
from datetime import datetime
from enum import Enum
from os.path import abspath, exists, expanduser, split, splitext

##-- end imports

logging = logmod.getLogger(__name__)
config  = acab.config

@register
def do_init(self, line):
    """
    Specify the Engine to initialise.
    Imports the module, and uses the final component as the Engine Class.
    eg: acab.modules.engines.trie_engine.TrieEngine -> TrieEngine

    A Question mark at the end of the line signals to inspect the module
    for potential constructors:
    eg: acab.modules.engines.configured?
    """
    if not bool(line.strip()):
        line = self.state.engine_str

    # if:  "init line?", then return applicable functions
    if line[-1] == "?":
        return init_inspect(line[:-1])

    logging.info("Initialising Engine: {}".format(line))

    try:
        mod_str = splitext(line)[0]
        mod = importlib.import_module(mod_str)
        # TODO ask for confirmation?
        # Note: not init_module.{} because of split*ext*
        # build engine. needs to be a 0 arg constructor
        spec        = getattr(mod, line.split(".")[-1])
        is_type     = isinstance(spec, type)
        is_sub      = is_type and issubclass(spec, AcabEngine_i)
        is_callable = callable(spec)
        if (not is_type) and isinstance(spec, AcabEngine_i):
            self.state.engine = spec
        elif (is_type and is_sub) or callable(spec):
            self.state.engine = spec()
        else:
            raise AcabConfigException(f"Unknown Engine Spec Form: {spec}")

        # TODO add bad words from repl:
        # self.state.engine.parser.set_word_exclusions(self.completenames(""))

        self.state.ctxs = None
        logging.info("Engine Initialisation Complete")
    except Exception as err:
        logging.error(f"Failed to initialise engine: {line}", exc_info=err)
