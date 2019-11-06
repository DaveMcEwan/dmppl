
# -*- coding: utf8 -*-

# Standard library imports
from itertools import chain
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

cssProps = False

def calculateEdges(f, g, u, x, y,
                   cfg, dsfDeltas, vcdInfo): # {{{
    return None
# }}} def calculateEdges

def svgNodes(exs): # {{{

    measureNames = list(exs.keys())
    nameParts = [measureNameParts(nm) for nm in measureNames]

    _baseNames = set(bn for mt,st,bn in nameParts) # One sibgrp per base name.

    mapBaseNameToSibgrpIdx = \
        {bn: i for i,bn in enumerate(sorted(list(_baseNames)))}

    # {{{ nodes

    sibgrpSeparation = 100 # Space between groups of sibling nodes. HEURISTIC
    sibgrpRadius = (len(measureNames) * sibgrpSeparation) / (2 * pi)

    sibgrpCenters = \
        list(ptsMkPolygon(nPts=len(_baseNames), radius=[sibgrpRadius]))

    nodeSibgrpCenters = \
        {nm: sibgrpCenters[mapBaseNameToSibgrpIdx[bn]] \
         for nm,(mt,st,bn) in zip(measureNames, nameParts)}


    sibSeparation = 60 # Space between sibling nodes. HEURISTIC
    mapSiblingTypeToLocalCenter = { # heuristic
        "measure":    (0, 0),
        "reflection": (0, sibSeparation),
        "rise":       (sibSeparation, 0),
        "fall":       (sibSeparation, sibSeparation),
    }

    nodeLocalCenters = \
        {nm: mapSiblingTypeToLocalCenter[st] \
         for nm,(mt,st,bn) in zip(measureNames, nameParts)}

    nodeCenters = \
        {nm: ptShift(nodeSibgrpCenters[nm], nodeLocalCenters[nm]) \
         for nm in measureNames}


    # Title provides mouseover information and should apply to all elements
    # representing a node.
    titleFmt = '''\
<title>{measureName}

E&#x0307; = {exValue}
</title>'''

    # Blob (circular container) has background color representing E[x].
    blobX, blobY = 0, 0
    blobRadius = 25
    if cssProps:
        blobFmt = '<circle class="node" fill="#{exRgb}"/>'
    else:
        blobFmt = ('<circle'
            ' class="node"'
            ' cx="%d" cy="%d"'
            ' r="%d"'
            ' style="stroke:lime; stroke-width:0.2; stroke-opacity:1;"'
            ' fill="#{exRgb}"'
            '/>') % \
            (blobX, blobY, blobRadius)

    # Tombstone (colored rectangle) is quick to recognise measurement type.
    tombstoneWidth, tombstoneHeight = 20, 20
    tombstoneX, tombstoneY = tombstoneWidth / -2, tombstoneHeight / -2
    if cssProps:
        tombstoneFmt = '<rect class="node {measureType}"/>'
    else:
        tombstoneFmt = ('<rect'
            ' class="node {measureType}"'
            ' rx="3px" ry="3px"'
            ' width="%d" height="%d"'
            ' x="%d" y="%d"'
            ' style="fill:{tombstoneFill}"'
            '/>') % \
            (tombstoneWidth, tombstoneHeight, tombstoneX, tombstoneY)

    # Symbol (text) to be vertically centered in RHS of tombstone.
    symbolOffsetX, symbolOffsetY = -4, 4 # HEURISTIC
    if cssProps:
        symbolFmt = '<text class="sym" x="%d" y="%d">{symbol}</text>' % \
              (symbolOffsetX, symbolOffsetY)
    else:
        symbolFmt = ('<text'
            ' class="sym"'
            ' x="%d" y="%d"'
            ' style="font-size:15px;font-family:sans-serif;fill:{symbolFill};">'
            '{symbol}'
            '</text>') % \
            (symbolOffsetX, symbolOffsetY)

    # Node is the collection of all elements representing a measure.
    nodeFmt = ' '.join((
        '<g',
            'id="{measureName}"',
            'class="node {siblingType}"',
            'transform="translate({centerX},{centerY})"',
        '>',
          titleFmt,
          blobFmt,
          tombstoneFmt, # Tombstone
          symbolFmt,
        '</g>',
    ))

    mapMeasureTypeToTombstoneFill = {
        "event":     "white",
        "bstate":    "blue",
        "threshold": "red",
        "normal":    "black",
    }

    mapMeasureTypeToSymbolFill = {
        "event":     "#404040",
        "bstate":    "lime",
        "threshold": "lime",
        "normal":    "lime",
    }

    nodes = (nodeFmt.format(measureName=nm,
                          siblingType=st,
                          measureType=mt,
                          baseName=bn,
                          centerX=nodeCenters[nm][0],
                          centerY=nodeCenters[nm][1],
                          symbolFill=mapMeasureTypeToSymbolFill[mt],
                          tombstoneFill=mapMeasureTypeToTombstoneFill[mt],
                          exRgb=rgb1D(exs[nm]),
                          exValue=exs[nm],
                          symbol=mapSiblingTypeToHtmlEntity[st]) \
           for nm,(mt,st,bn) in zip(measureNames, nameParts))

    # }}} nodes

    # {{{ identicons
    # One per sibling group.

    identiconRadius = sibgrpRadius + 1.5*sibgrpSeparation

    _identiconCenters = \
        list(ptsMkPolygon(nPts=len(_baseNames), radius=[identiconRadius]))
    identiconCenters = \
        {bn: _identiconCenters[mapBaseNameToSibgrpIdx[bn]] \
         for bn in _baseNames}

    # Identicon to be vertically centered in LHS of tombstone.
    identiconOffsetX, identiconOffsetY = 0, 0 # HEURISTIC
    identiconScale = 0.025
    identiconFmt = \
        ('<g transform="translate({centerX},{centerY}) scale(%0.03f)">'
         '{identiconSvg}'
         '</g>') % identiconScale

    # Identicons are embedded SVGs scaled and translated into place.
    identiconSvgs = \
        {bn: rdTxt(joinP(paths.dname_identicon, bn + ".svg")) \
         for bn in _baseNames}

    identicons = \
        (identiconFmt.format(identiconSvg=identiconSvgs[bn],
                             centerX=identiconCenters[bn][0],
                             centerY=identiconCenters[bn][1])
         for bn in _baseNames)

    # }}} identicons

    return chain(nodes, identicons), sibgrpRadius, sibgrpSeparation
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

    if cssProps:
        ret_.append(' '.join((
          '<style>',
            'g.node > circle.node { cx:0; cy:0; r:25; stroke:lime; stroke-width:0.2; stroke-opacity:1; }',
            'g.node > text.sym { x:0; y:0; font-size:15px; font-family:sans-serif; }',
            'g.node > rect.node { x:-10; y:-10; height:20px; width:20px; rx:3px; ry:3px; }',
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
    return ret_
# }}} def svgNetgraph

if __name__ == "__main__":
    assert False, "Not a standalone script."
