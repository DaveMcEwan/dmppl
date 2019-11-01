
# -*- coding: utf8 -*-

# Standard library imports

# PyPI library imports
import numpy as np

# Local library imports
from dmppl.base import dbg, info, verb
from dmppl.math import ptsMkPolygon

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
import dmppl.experiments.eva.eva_common as eva

def calculateEdges(f, g, u, x, y,
                   cfg, dsfDeltas, vcdInfo): # {{{
    return None
# }}} def calculateEdges

def svgNetgraph(u, cfg, vcdInfo, edges): # {{{
    measureNames = vcdInfo["unitIntervalVarNames"]
    nameParts = [eva.measureNameParts(nm) for nm in measureNames]

    baseNames = set(bn for mt,st,bn in nameParts) # One sibGrp per base name.

    evs = eva.rdEvs(measureNames, u, u + cfg.windowsize, cfg.fxbits)
    expectation = eva.metric("Ex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    exs = [expectation(evs[nm]) for nm in measureNames]

    mapSiblingTypeToOffset = {
        "measure":    (0, 0),
        "reflection": (30, 0),
        "rise":       (0, 30),
        "fall":       (30, 30),
    }
    localCenters = [mapSiblingTypeToOffset[st] for mt,st,bn in nameParts]

    sibGrpCenters = ptsMkPolygon(nPts=len(baseNames)) # TODO: pair with full names.

    # TODO
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
