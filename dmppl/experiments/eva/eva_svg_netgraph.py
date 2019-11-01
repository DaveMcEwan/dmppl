
# -*- coding: utf8 -*-

# Standard library imports

# PyPI library imports
import numpy as np

# Local library imports
from dmppl.base import dbg, info, verb

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
import dmppl.experiments.eva.eva_common as eva

def calculateEdges(f, g, u, x, y,
                   cfg, dsfDeltas, vcdInfo): # {{{
    return None
# }}} def calculateEdges

def svgNetgraph(u, cfg, vcdInfo, edges): # {{{
    ret_ = []
    ret_.append('<div class="netgraph">')
    ret_.append(  '<svg>')
    ret_.append(    '<rect width="50" height="100">TODO</rect>')
    ret_.append(  '</svg>')
    ret_.append('</div>')
    return ret_
# }}} def svgNetgraph

if __name__ == "__main__":
    assert False, "Not a standalone script."
