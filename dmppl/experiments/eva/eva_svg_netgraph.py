
# -*- coding: utf8 -*-

# Standard library imports

# PyPI library imports
import numpy as np

# Local library imports
from dmppl.base import dbg, info, verb
from dmppl.math import ptShift, ptsMkPolygon

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

    baseNames = sorted(list(set(bn for mt,st,bn in nameParts))) # One sibGrp per base name.

    evs = eva.rdEvs(measureNames, u, u + cfg.windowsize, cfg.fxbits)
    expectation = eva.metric("Ex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    exs = [expectation(evs[nm]) for nm in measureNames]
    # TODO: background-color by Ex

    # TODO: correct radius
    sibGrpCenters = list(ptsMkPolygon(nPts=len(baseNames), radius=[100.0]))
    globalCenters = [sibGrpCenters[baseNames.index(bn)] for mt,st,bn in nameParts]

    mapSiblingTypeToLocalCenter = {
        "measure":    (0, 0),
        "reflection": (30, 0),
        "rise":       (0, 30),
        "fall":       (30, 30),
    }
    localCenters = [mapSiblingTypeToLocalCenter[st] for mt,st,bn in nameParts]

    assert len(globalCenters) == len(localCenters), \
        (len(globalCenters), len(localCenters))
    nodeCenters = [ptShift(gc, lc) for gc,lc in zip(globalCenters, localCenters)]

    nodeFmt = ' '.join((
        '<g',
            'id="%s"', # measureName
            'class="node %s"',   # siblingType
            'transform="translate(%f,%f)"', # centerX,centerY
        '>',
          '<circle/>', # Radius, center, style defined in CSS.
          '<rect/>', # Width, height, x, y defined in CSS.
          # TODO: identicon
          # TODO: symbol
        '</g>',
    ))

    # TODO: Sibling group internals

    viewBoxWidth, viewBoxHeight = 1000, 1000 # TODO: correct viewBox

    # 0,0 is top-left of 100x100 box
    viewBoxMinX, viewBoxMinY = -500, -500 # TODO: correct viewBox

    svgClassList = ["netgraph"]

    ret_ = []
    ret_.append('<div class="netgraph">')
    ret_.append(' '.join((
        '<svg',
          'xmlns="http://www.w3.org/2000/svg"',
          'xmlns:xlink="http://www.w3.org/1999/xlink"',
          'viewBox="%d %d %d %d"' % (viewBoxMinX, viewBoxMinY, viewBoxWidth, viewBoxHeight),
          'class="%s"' % ' '.join(svgClassList),
          '>',
    )))
    ret_ += [nodeFmt % (nm, st, pt[0], pt[1]) \
             for nm,(mt,st,bn),pt in zip(measureNames,
                                         nameParts,
                                         nodeCenters)]
    ret_.append(  '</svg>')
    ret_.append('</div>')
    return ret_
# }}} def svgNetgraph

if __name__ == "__main__":
    assert False, "Not a standalone script."
