
# -*- coding: utf8 -*-

# Standard library imports
from itertools import chain
from math import pi

# PyPI library imports
import numpy as np

# Local library imports
from dmppl.base import dbg, info, verb, rdTxt, joinP, utf8NameToHtml
from dmppl.math import ptShift, ptsMkPolygon, subsample, downsample, l2Norm
from dmppl.fx import fxFromFloat
from dmppl.color import rgb1D, rgb2D, identiconSpriteSvg

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
from dmppl.experiments.eva.eva_common import paths, measureNameParts, \
    mapSiblingTypeToHtml, metricNames, metric, mapMetricNameToHtml, \
    timeToEvsIdx, rdEvs

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
nodeTitleFmt = '\n'.join((
  '<title>{measureName}',
  '',
  mapMetricNameToHtml["Ex"] + ' = {exValue:.2%}',
  '</title>',
))

# Blob (circular container) has background color representing E[x].
blobX, blobY = 0, 0
blobRadius = 25
blobStroke = 'style="stroke:black; stroke-width:0.2; stroke-opacity:1;"'
if cssProps:
    blobFmt = '<circle class="node" fill="#{exRgb}"/>'
else:
    blobFmt = ' '.join((
      '<circle',
        'class="node"',
        'cx="%d" cy="%d"' % (blobX, blobY),
        'r="%d"' % blobRadius,
        blobStroke,
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
        'transform="translate({centerX:.3f},{centerY:.3f})"',
    '>',
      nodeTitleFmt,
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
identiconFmt = ' '.join((
  '<g',
    'transform="translate({centerX:.3f},{centerY:.3f}) scale(%0.03f)"' % \
        identiconScale,
  '>',
  '<title>{baseName}</title>',
  '{identiconSvg}',
  '</g>',
))\

topStyle = '' if not cssProps else ' '.join((
  '<style>',
    'g.node > circle.node {',
        blobStroke,
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

_scrDeltaFmt = \
    utf8NameToHtml("MATHEMATICAL LEFT ANGLE BRACKET") + \
    '{srcDelta}' + \
    utf8NameToHtml("MATHEMATICAL RIGHT ANGLE BRACKET")
edgeFmt = ' '.join((
  '<path',
    'class="edge"',
    'id="{srcName}__{srcDelta}__{dstName}"',
    'd="M {srcX:.3f},{srcY:.3f} {dstX:.3f},{dstY:.3f}"',
    'style="{style}"',
    'inkscape:connector-curvature="0"',
  '>',
    '\n'.join((
      '<title>{srcName}' + \
        _scrDeltaFmt + \
        utf8NameToHtml("LONG RIGHTWARDS ARROW") + \
        ' {dstName}',
      '',
      'X = {dstName}',
      'Y = {srcName}' + _scrDeltaFmt,
      'sampleFactor = {sampleFactor:d}',
      'f = {f}',
      'g = {g}',
      '',
      mapMetricNameToHtml["Ex"] + '[X] = {dstEx:.2%}',
      mapMetricNameToHtml["Ex"] + '[Y] = {srcEx:.2%}',
      #mapMetricNameToHtml["Ex"] + '[X*Y] = {Ex_XconvY:.2%}',
      #mapMetricNameToHtml["Ex"] + '[|X-Y|] = {Ex_XabsdiffY:.2%}',
      mapMetricNameToHtml["Cex"] + '[X|Y] = {Cex:.2%}',
      mapMetricNameToHtml["Cls"] + '(X,Y) = {Cls:.2%}',
      mapMetricNameToHtml["Cos"] + '(X,Y) = {Cos:.2%}',
      mapMetricNameToHtml["Cov"] + '(X,Y) = {Cov:.2%}',
      mapMetricNameToHtml["Dep"] + '(X,Y) = {Dep:.2%}',
      mapMetricNameToHtml["Ham"] + '(X,Y) = {Ham:.2%}',
      mapMetricNameToHtml["Tmt"] + '(X,Y) = {Tmt:.2%}',
      '</title>',
    )),
  '</path>',
))
# }}} Static format strings

def calculateEdges(f, g, u,
                   cfg, sfDeltas, vcdInfo): # {{{

    measureNames = vcdInfo["unitIntervalVarNames"]

    # Helper function to implement floats as floats or fixed point.
    implFloat = \
        (lambda x: x) \
        if 0 == cfg.fxbits else \
        functools.partial(fxFromFloat, nBits=cfg.fxbits)

    epsilonF, epsilonG = \
        implFloat(cfg.epsilon[f]), \
        implFloat(cfg.epsilon[g]) if g else None

    assert isinstance(u, int), type(u)
    v = u + cfg.windowsize
    evsStartTime = u - cfg.deltabk
    evsFinishTime = v + cfg.deltafw + 1

    # Keep relevant samples in memory.
    evs = rdEvs(measureNames, evsStartTime, evsFinishTime, cfg.fxbits)

    nDeltas = len(sfDeltas)
    m = len(measureNames)
    nPossibleEdges = nDeltas * (m**2 - m) / 2 # TODO: Report progress.

    # Track downsample factor changes in order to perform the sampling only once.
    sfPrev = -1 # non-init

    for dIdx, (sf, d) in enumerate(sfDeltas):
        dU, dV = u+d, v+d

        # Ignore negative deltas where relationship can't exist yet.
        if 0 > dU:
            continue

        # Downsample EVS to get X and Y.
        if sf != sfPrev:
            sfPrev = sf

            # Each X,Y window requires exactly 3 pieces of information which are
            # derived from an integer floor division in sub/down-sampling.
            # 1. Where X starts = u -> sfU
            # 2. Where Y starts = u+d -> sfU+sfD
            # 3. Size of window = v-u -> sfV-sfU
            sfWinSize = cfg.windowsize // sf
            sfD = d // sf
            sfU = timeToEvsIdx(u, evsStartTime) // sf
            sfV = sfU + sfWinSize

            # Sub/downsample entire EVS since it will all be used.
            sfEvs = {nm: subsample(evs[nm], sf) for nm in measureNames}

            # Get metric implementations for this window.
            # TODO: LRU cache wrappers for fnEx.
            fnEx = metric("Ex", sfWinSize, cfg.windowalpha, nBits=cfg.fxbits)
            fnF = metric(f, sfWinSize, cfg.windowalpha, nBits=cfg.fxbits)
            fnG = metric(g, sfWinSize, cfg.windowalpha, nBits=cfg.fxbits) \
                if g is not None else None
            fnMetrics = \
                {nm: metric(nm, sfWinSize, cfg.windowalpha, nBits=cfg.fxbits) \
                 for nm in metricNames}

            xs = {nm: sfEvs[nm][sfU:sfV] for nm in measureNames}
            # Pre-calculate (with LRU cache).
            xsEx = {nm: fnEx(xs[nm]) for nm in measureNames}

        ys = {nm: sfEvs[nm][sfU+sfD:sfV+sfD] for nm in measureNames}
        # Pre-calculate (with LRU cache).
        ysEx = {nm: fnEx(ys[nm]) for nm in measureNames}

        for nmX in measureNames:
            mtX, stX, bnX = measureNameParts(nmX)

            for nmY in measureNames:
                mtY, stY, bnY = measureNameParts(nmY)

                if bnX == bnY:
                    continue

                # Unusual structure only executes fnG() where it has a chance
                # of producing an overall significant result.
                metF = fnF(xs[nmX], ys[nmY])
                if g is None:
                    isSignificant = epsilonF < metF
                elif epsilonF < metF:
                    metG = fnG(xs[nmX], ys[nmY])
                    isSignificant = epsilonG < metG
                else:
                    isSignificant = False

                if not isSignificant:
                    continue

                edge = {nm: fnMetrics[nm](xs[nmX], ys[nmY]) \
                        for nm in metricNames}
                edge.update({
                    'f': f,
                    'g': g,
                    "dstName": nmX,
                    "srcName": nmY,
                    "srcDelta": d,
                    "sampleFactor": sf,
                    "dstEx": xsEx[nmX],
                    "srcEx": ysEx[nmY],
                })

                yield edge

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
                        symbol=mapSiblingTypeToHtml[st]) \
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
        (identiconFmt.format(
            identiconSvg=identiconSvgs[bn],
            centerX=identiconCenters[bn][0],
            centerY=identiconCenters[bn][1],
            baseName=bn,
         ) for bn in baseNames)

    # }}} identicons

    canvasWidth, canvasHeight = \
        2*identiconRadius + 2*sibgrpSeparation, \
        2*identiconRadius + 2*sibgrpSeparation

    return chain(nodes, identicons), (canvasWidth, canvasHeight), nodeCenters
# }}} def svgNodes

def svgEdges(edges, nodeCenters): # {{{

    for edge in edges:
        f, g = edge['f'], edge['g']
        metF, metG = edge[f], edge[g] if g else None

        normFG = l2Norm(metF, metG) if g else metF

        style = ';'.join((
            'stroke: #%s' % (rgb2D(metF, metG) if g else rgb1D(metF)),
            'stroke-width: %0.2f' % normFG * 1,
            'stroke-opacity: %0.2f' % normFG * 1,
        ))

        yield edgeFmt.format(
           srcX=nodeCenters[edge["srcName"]][0],
           srcY=nodeCenters[edge["srcName"]][1],
           dstX=nodeCenters[edge["dstName"]][0],
           dstY=nodeCenters[edge["dstName"]][1],
           style=style,
           **edge,
        )
# }}} def svgEdges

def svgNetgraph(u, cfg, vcdInfo, edges): # {{{
    measureNames = vcdInfo["unitIntervalVarNames"]

    evs = rdEvs(measureNames, u, u + cfg.windowsize, cfg.fxbits)
    expectation = metric("Ex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    exs = {nm: expectation(evs[nm]) for nm in measureNames}

    nodeStrs, (canvasWidth, canvasHeight), nodeCenters = svgNodes(exs)

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
    ret_ += list(nodeStrs)
    ret_.append('</g>')

    # Layer of edge/connections.
    ret_.append(' '.join((
      '<g',
        'id="layer2"',
        'inkscape:label="Edges"',
        'inkscape:groupmode="layer"',
      '>',
    )))
    ret_ += list(svgEdges(edges, nodeCenters))
    ret_.append('</g>')

    # TODO: Layer of self-duty for multi-sibling measures.

    ret_.append('</svg>')
    return ret_
# }}} def svgNetgraph

if __name__ == "__main__":
    assert False, "Not a standalone script."
