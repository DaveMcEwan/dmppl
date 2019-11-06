
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

# {{{ Static format strings

# Experimental option to cut down on complexity of SVG code by using CSS
# properties.
# Only works with SVG2 support, so older (not really that old) still require
# attributes on each element.
cssProps = False

sibgrpSeparation = 100 # Space between groups of sibling nodes. HEURISTIC
sibSeparation = 60 # Space between sibling nodes. HEURISTIC
mapSiblingTypeToLocalCenter = { # heuristic
    "measure":    (0, 0),
    "reflection": (0, sibSeparation),
    "rise":       (sibSeparation, 0),
    "fall":       (sibSeparation, sibSeparation),
}

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
    blobFmt = ' '.join((
      '<circle',
        ' class="node"',
        ' cx="%d" cy="%d"' % (blobX, blobY),
        ' r="%d"' % blobRadius,
        ' style="stroke:lime; stroke-width:0.2; stroke-opacity:1;"',
        ' fill="#{exRgb}"',
      '/>'))

# Tombstone (colored rectangle) is quick to recognise measurement type.
tombstoneWidth, tombstoneHeight = 20, 20
tombstoneX, tombstoneY = tombstoneWidth / -2, tombstoneHeight / -2
if cssProps:
    tombstoneFmt = '<rect class="node {measureType}"/>'
else:
    tombstoneFmt = ' '.join((
      '<rect',
        ' class="node {measureType}"',
        ' rx="3px" ry="3px"',
        ' width="%d" height="%d"' % (tombstoneWidth, tombstoneHeight),
        ' x="%d" y="%d"' % (tombstoneX, tombstoneY),
        ' style="fill:{tombstoneFill}"',
      '/>'))

# Symbol (text) to be vertically centered tombstone.
symbolX, symbolY = -4, 4 # HEURISTIC
if cssProps:
    symbolFmt = '<text class="sym" x="%d" y="%d">{symbol}</text>' % \
          (symbolX, symbolY)
else:
    symbolFmt = ' '.join((
      '<text',
        ' class="sym"',
        ' x="%d" y="%d"'% (symbolX, symbolY),
        ' style="font-size:15px;font-family:sans-serif;fill:{symbolFill};"',
      '>{symbol}</text>'))

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


identiconX, identiconY = -7.5, -7.5 # HEURISTIC
identiconScale = 3.0 # 3*5=15
identiconFmt = \
    ('<g transform="translate({centerX},{centerY}) scale(%0.03f)">'
     '{identiconSvg}'
     '</g>') % identiconScale

topStyle = '' if not cssProps else ' '.join((
  '<style>',
    'g.node > circle.node {',
        'stroke:lime; stroke-width:0.2; stroke-opacity:1;',
        'cx:%d; cy:%d;' % (blobX, blobY),
        'r:%d;' % blobRadius,
    '}',
    'g.node > text.sym {',
        'font-size:15px; font-family:sans-serif;',
        'x:%d; y:%d;' % (symbolX, symbolY),
    '}',
    'g.node > rect.node {',
        'rx:3px; ry:3px;',
        'x:%d; y:%d;' % (tombstoneX, tombstoneY),
        'width:%dpx; height:%dpx;' % (tombstoneWidth, tombstoneHeight),
    '}',
    'g.node > rect.event     { fill:%s; }' % mapMeasureTypeToTombstoneFill["event"],
    'g.node > rect.bstate    { fill:%s; }' % mapMeasureTypeToTombstoneFill["bstate"],
    'g.node > rect.threshold { fill:%s; }' % mapMeasureTypeToTombstoneFill["threshold"],
    'g.node > rect.normal    { fill:%s; }' % mapMeasureTypeToTombstoneFill["normal"],
    'rect.event     ~ text.sym { fill:%s; }' % mapMeasureTypeToSymbolFill["event"],
    'rect.bstate    ~ text.sym { fill:%s; }' % mapMeasureTypeToSymbolFill["bstate"],
    'rect.threshold ~ text.sym { fill:%s; }' % mapMeasureTypeToSymbolFill["threshold"],
    'rect.normal    ~ text.sym { fill:%s; }' % mapMeasureTypeToSymbolFill["normal"],
  '</style>',
))

svgRootFmt = ' '.join((
  '<svg',
    'xmlns="http://www.w3.org/2000/svg"',
    'xmlns:xlink="http://www.w3.org/1999/xlink"',
    'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"',
    'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
    'class="netgraph"',
    'viewBox="{viewBoxMinX} {viewBoxMinY} {viewBoxWidth} {viewBoxHeight}"',
    'width="{svgWidth}"',
    'height="{svgHeight}"',
    #'transform="{svgTransform}"',
  '>',
))

sodipodiNamedview = ' '.join((
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
))

# }}} Static format strings

def calculateEdges(f, g, u, x, y,
                   cfg, dsfDeltas, vcdInfo): # {{{
    return None
# }}} def calculateEdges

def svgNodes(exs): # {{{

    measureNames = list(exs.keys())
    nameParts = [measureNameParts(nm) for nm in measureNames]

    baseNames = set(bn for mt,st,bn in nameParts) # One sibgrp per base name.

    mapBaseNameToSibgrpIdx = \
        {bn: i for i,bn in enumerate(sorted(list(baseNames)))}

    # {{{ nodes

    sibgrpRadius = (len(measureNames) * sibgrpSeparation) / (2 * pi)

    sibgrpCenters = \
        list(ptsMkPolygon(nPts=len(baseNames), radius=[sibgrpRadius]))

    nodeSibgrpCenters = \
        {nm: sibgrpCenters[mapBaseNameToSibgrpIdx[bn]] \
         for nm,(mt,st,bn) in zip(measureNames, nameParts)}

    nodeLocalCenters = \
        {nm: mapSiblingTypeToLocalCenter[st] \
         for nm,(mt,st,bn) in zip(measureNames, nameParts)}

    nodeCenters = \
        {nm: ptShift(nodeSibgrpCenters[nm], nodeLocalCenters[nm]) \
         for nm in measureNames}

    nodes = \
        (nodeFmt.format(measureName=nm,
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
        list(ptsMkPolygon(nPts=len(baseNames), radius=[identiconRadius]))
    identiconCenters = \
        {bn: ptShift(_identiconCenters[mapBaseNameToSibgrpIdx[bn]],
                     (identiconX, identiconY))\
         for bn in baseNames}

    # Identicons are embedded SVGs scaled and translated into place.
    identiconSvgs = \
        {bn: rdTxt(joinP(paths.dname_identicon, bn + ".svg")) \
         for bn in baseNames}
    # Uncomment to regenerate/experiment.
    #identiconSvgs = \
    #    {bn: identiconSpriteSvg(bn) \
    #     for bn in baseNames}

    identicons = \
        (identiconFmt.format(identiconSvg=identiconSvgs[bn],
                             centerX=identiconCenters[bn][0],
                             centerY=identiconCenters[bn][1])
         for bn in baseNames)

    # }}} identicons

    canvasWidth, canvasHeight = \
        2*identiconRadius + 2*sibgrpSeparation, \
        2*identiconRadius + 2*sibgrpSeparation

    return chain(nodes, identicons), (canvasWidth, canvasHeight)
# }}} def svgNodes

def svgNetgraph(u, cfg, vcdInfo, edges): # {{{
    measureNames = vcdInfo["unitIntervalVarNames"]

    evs = rdEvs(measureNames, u, u + cfg.windowsize, cfg.fxbits)
    expectation = metric("Ex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    exs = {nm: expectation(evs[nm]) for nm in measureNames}

    nodes, (canvasWidth, canvasHeight) = svgNodes(exs)

    # Clip the max dimensions to for zooming to work with browsers.
    # 300 is just a reasonable value for 1080p screen.
    svgWidth, svgHeight = min(canvasWidth, 300), min(canvasHeight, 300)

    viewBoxMinX, viewBoxMinY = \
        canvasWidth / -2, canvasHeight / -2

    viewBoxWidth, viewBoxHeight = \
        canvasWidth, canvasHeight

    ret_ = []
    ret_.append(svgRootFmt.format(
        svgWidth="%dmm" % svgWidth,
        svgHeight="%dmm" % svgHeight,
        viewBoxMinX=viewBoxMinX,
        viewBoxMinY=viewBoxMinY,
        viewBoxWidth=viewBoxWidth,
        viewBoxHeight=viewBoxHeight,
        #svgTransform='',#"translate(-30 -30) scale(1.0)",
    ))

    ret_.append(sodipodiNamedview)

    ret_.append(topStyle)

    # Force background to white
    #ret_.append('<rect fill="white" width="100%%" height="100%%" x="%d" y="%d"/>' \
    #    % (viewBoxMinX, viewBoxMinY))
    ret_.append('<circle fill="white" r="50%" cx="0%" cy="0%"/>')

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
