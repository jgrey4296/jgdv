""" Utilities for Cairo and DCEL """
##-- imports
from __future__ import annotations
import logging as root_logger
import pickle
from os.path import join, exists

##-- end imports

import pathlib as pl

logging = root_logger.getLogger(__name__)

def pickle_graph(node_dict, nx_graph, fpath:pl.Path):
    """
    Given a graph and dictionary of nodes,
    pickle it to the specified fpath
    """
    fpath.with_suffix(".graph.pickle".write_text(pickle.dumps(nx_graph))
    fpath.with_suffix(".nodes.pickle").write_text(pickle.dumps(node_dict))

def load_pickled_graph(fpath):
    """
    Given a fpath, load a pickled graph and
    its dictionary of nodes
    """
    node_dict = pickle.loads(fpath.with_suffix(".graph.pickle").read_text())
    nx_graph  = pickle.loads(fpath.with_suffix(".nodes.pickle").tead_text())
    return (node_dict, nx_graph)


def pickle_graph(node_dict, nx_graph, filename, directory="."):
    """ Given a graph and dictionary of nodes,
    pickle it to the specified filename """
    if not exists(directory):
        raise Exception("Directory not found: {}".format(directory))
    with open(join(directory, "{}_nxgraph.pickle".format(filename)), 'wb') as f:
        pickle.dump(nx_graph, f)
    with open(join(directory, "{}_node_dict.pickle".format(filename)), 'wb') as f:
        pickle.dump(node_dict, f)

def load_pickled_graph(filename, directory="."):
    """ Given a filename, load a pickled graph and
    its dictionary of nodes """
    if not (exists(directory) and \
             exists(join(directory, "{}_nxgraph.pickle".format(filename))) and \
             exists(join(directory, "{}_node_dict.pickle".format(filename)))):
        raise Exception("Missing file or directory for reconstruction")
    node_dict = None
    nx_graph = None
    with open(join(directory, "{}_nxgraph.pickle".format(filename)), 'rb') as f:
        nx_graph = pickle.load(f)
    with open(join(directory, "{}_node_dict.pickle".format(filename)), 'rb') as f:
        node_dict = pickle.load(f)
    return (node_dict, nx_graph)
