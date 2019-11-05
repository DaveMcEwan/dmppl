
# -*- coding: utf8 -*-

# Standard library imports
from math import pi

# PyPI library imports
import numpy as np

# Local library imports
from dmppl.base import dbg, info, verb, rdTxt, joinP
from dmppl.math import ptShift, ptsMkPolygon
from dmppl.color import rgb1D, rgb2D, identiconSpriteSvg

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
from dmppl.experiments.eva.eva_common import paths, measureNameParts, metric, rdEvs, \
    mapSiblingTypeToHtmlEntity

def calculateEdges(f, g, u, x, y,
                   cfg, dsfDeltas, vcdInfo): # {{{
    return None
# }}} def calculateEdges

def svgNodes(exs): # {{{

    measureNames = list(exs.keys())
    nameParts = [measureNameParts(nm) for nm in measureNames]

    _baseNames = set(bn for mt,st,bn in nameParts) # One sibgrp per base name.
    mapBaseNameToSibgrpIdx = {bn: i for i,bn in \
                              enumerate(sorted(list(_baseNames)))}

    # Identicons are embedded SVGs scaled and translated into place.
    identicons = {bn: '<g transform="translate(-18 -8) scale(0.005)">%s</g>' % \
                      rdTxt(joinP(paths.dname_identicon, bn + ".svg")) \
                  for bn in _baseNames}

    sibgrpSeparation = 100 # heuristic
    sibgrpRadius = (len(measureNames) * sibgrpSeparation) / (2 * pi)
    sibgrpCenters = list(ptsMkPolygon(nPts=len(_baseNames), radius=[sibgrpRadius]))
    #sibgrpCenters = list(ptsMkPolygon(nPts=len(_baseNames), radius=[sibgrpRadius, 0.66*sibgrpRadius]))
    globalCenters = {nm: sibgrpCenters[mapBaseNameToSibgrpIdx[bn]] \
                     for nm,(mt,st,bn) in zip(measureNames, nameParts)}


    mapSiblingTypeToLocalCenter = { # heuristic
        "measure":    (0, 0),
        "reflection": (0, 60),
        "rise":       (60, 0),
        "fall":       (60, 60),
    }
    localCenters = {nm: mapSiblingTypeToLocalCenter[st] \
                     for nm,(mt,st,bn) in zip(measureNames, nameParts)}

    nodeCenters = {nm: ptShift(globalCenters[nm], localCenters[nm]) \
                   for nm in measureNames}

    nodeFmt = ' '.join((
        '<g',
            'id="{measureName}"',
            'class="node {siblingType}"',
            'transform="translate({centerX},{centerY})"',
        '>',
          '<title>{measureName}</title>',
          '<circle class="node" fill="#{rgbValue}"/>',
          '<rect class="node {measureType}"/>',
          '<text class="sym">{symbol}</text>',
          '{identicon}',
        '</g>',
    ))

    ret = (nodeFmt.format(measureName=nm,
                          siblingType=st,
                          measureType=mt,
                          centerX=nodeCenters[nm][0],
                          centerY=nodeCenters[nm][1],
                          rgbValue=rgb1D(exs[nm]),
                          symbol=mapSiblingTypeToHtmlEntity[st],
                          identicon=identicons[bn]) \
             for nm,(mt,st,bn) in zip(measureNames, nameParts))

    return ret, sibgrpRadius, sibgrpSeparation
# }}} def svgNodes

def svgNetgraph(u, cfg, vcdInfo, edges): # {{{
    measureNames = vcdInfo["unitIntervalVarNames"]

    evs = rdEvs(measureNames, u, u + cfg.windowsize, cfg.fxbits)
    expectation = metric("Ex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    exs = {nm: expectation(evs[nm]) for nm in measureNames}

    nodes, sibgrpRadius, sibgrpSeparation = svgNodes(exs)

    svgWidth, svgHeight = \
        2*sibgrpRadius + 2*sibgrpSeparation + 35, \
        2*sibgrpRadius + 2*sibgrpSeparation + 35

    viewBoxMinX, viewBoxMinY = \
        svgWidth / -2, svgHeight / -2

    viewBoxWidth, viewBoxHeight = \
        svgWidth, svgHeight

    ret_ = []
    ret_.append('<div class="netgraph">')
    ret_.append(' '.join((
      '<svg',
        'xmlns="http://www.w3.org/2000/svg"',
        'xmlns:xlink="http://www.w3.org/1999/xlink"',
        'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"',
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
        'class="netgraph"',
        'viewBox="%d %d %d %d"' % (viewBoxMinX, viewBoxMinY, viewBoxWidth, viewBoxHeight),
        'width="%dmm"' % svgWidth,
        'height="%dmm"' % svgHeight,
      '>',
    )))
    ret_.append(' '.join((
      '<sodipodi:namedview',
        'id="base"',
        'pagecolor="#ffffff"',
        'bordercolor="#666666"',
        'borderopacity="1.0"',
        'showgrid="true"',
        'borderlayer="false"',
        'objecttolerance="10000"',
        'inkscape:pageopacity="0.0"',
        'inkscape:pageshadow="2"',
        'inkscape:document-units="mm"',
        'inkscape:current-layer="layer1"',
        'inkscape:pagecheckerboard="false"',
        'inkscape:showpageshadow="false">',
        '<inkscape:grid',
          'type="xygrid"',
          'units="mm"',
          'spacingx="1"',
          'spacingy="1"',
          'dotted="false"',
        '/>',
      '</sodipodi:namedview>',
    )))
    ret_.append(' '.join((
      '<style>',
        'g.node > circle.node { cx:0; cy:0; r:25; stroke:lime; stroke-width:0.2; stroke-opacity:1; }',
        'g.node > text.sym { x:0; y:0; font-size:10px; font-family:sans-serif; }',
        'g.node > rect.node { x:-20; y:-10; height:20px; width:40px; rx:3px; ry:3px; }',
        'g.node > rect.event { fill:white; }',
        'g.node > rect.bstate { fill:blue; }',
        'g.node > rect.threshold { fill:red; }',
        'g.node > rect.normal { fill:black; }',
        'g.node > text.sym.measure { fill:lime; }',
        'rect.event ~ text.sym { fill:#404040; }',
        'rect.bstate ~ text.sym { fill:lime; }',
        'rect.threshold ~ text.sym { fill:lime; }',
        'rect.normal ~ text.sym { fill:lime; }',
      '</style>',
    )))

    # Force background to white
    ret_.append('<rect width="100%%" height="100%%" fill="white" x="%d" y="%d"/>' \
        % (viewBoxMinX, viewBoxMinY))

    # Layer of vertice/nodes
    ret_.append(' '.join((
      '<g',
        'id="layer1"',
        'inkscape:label="Vertices"',
        'inkscape:groupmode="layer"',
      '>',
    )))
    ret_ += list(nodes)
    ret_.append('</g>')

    # TODO: Layer of self-duty for multi-sibling measures.

    # TODO: Layer of edge/connections.

    ret_.append('</svg>')
    ret_.append('</div>')
    return ret_
# }}} def svgNetgraph

if __name__ == "__main__":
    assert False, "Not a standalone script."
