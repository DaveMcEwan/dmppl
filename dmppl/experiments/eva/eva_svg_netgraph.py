
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
    mapSiblingTypeToHtml, siblingIs1stDer, \
    metricNames, metric, mapMetricNameToHtml, \
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
    "orig": (0, 0),
    "refl": (0, sibSeparation),
    "rise": (sibSeparation, 0),
    "fall": (sibSeparation, sibSeparation),
}

# Title provides mouseover information and should apply to all elements
# representing a node.
nodeTitleFmt = '\n'.join((
  '<title>{measureName}',
  '',
  '{statsTitle}',
  '</title>',
))

# Blob (circular container) has background color representing E[x].
blobX, blobY = 0, 0
blobRadius = 25
blobStroke = 'style="stroke:black; stroke-width:0.2; stroke-opacity:1;"'
if cssProps:
    blobFmt = '<circle class="node" fill="#{blobRgb}"/>'
else:
    blobFmt = ' '.join((
      '<circle',
        'class="node"',
        'cx="%d" cy="%d"' % (blobX, blobY),
        'r="%d"' % blobRadius,
        blobStroke,
        ' fill="#{blobRgb}"',
      '/>'))

# Tombstone (colored rectangle) shows measurement type.
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
_nodeFmt = [
    '<g',
        'id="{measureName}"',
        'class="node {siblingType}"',
        'transform="translate({centerX:.3f},{centerY:.3f})"',
    '>',
      nodeTitleFmt,
      blobFmt,
      tombstoneFmt,
      symbolFmt,
    '</g>',
]
nodeFmts = {
  "orig": ' '.join(
    _nodeFmt[:-1] + [ # Insert basename at end of <g>
      '<text x="-25" y="35">{baseName}</text>',
    ] + _nodeFmt[-1:]
  ),
  "refl": ' '.join(_nodeFmt),
  "rise": ' '.join(_nodeFmt),
  "fall": ' '.join(_nodeFmt),
}

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
identiconSeparationMul = 1.2
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
      'a = {a}',
      'b = {b}',
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

def calculateEdges(a, b, u,
                   cfg, sfDeltas, vcdInfo): # {{{

    measureNames = vcdInfo["unitIntervalVarNames"]

    # Helper function to implement floats as floats or fixed point.
    implFloat = \
        (lambda x: x) \
        if 0 == cfg.fxbits else \
        functools.partial(fxFromFloat, nBits=cfg.fxbits)

    epsilonA, epsilonB = \
        implFloat(cfg.epsilon[a]), \
        implFloat(cfg.epsilon[b]) if b else None

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
            fnA = metric(a, sfWinSize, cfg.windowalpha, nBits=cfg.fxbits)
            fnB = metric(b, sfWinSize, cfg.windowalpha, nBits=cfg.fxbits) \
                if b is not None else None
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

                # Unusual structure only executes fnB() where it has a chance
                # of producing an overall significant result.
                metA = fnA(xs[nmX], ys[nmY])
                if b is None:
                    isSignificant = epsilonA < metA
                elif epsilonA < metA:
                    metB = fnB(xs[nmX], ys[nmY])
                    isSignificant = epsilonB < metB
                else:
                    isSignificant = False

                if not isSignificant:
                    continue

                edge = {nm: fnMetrics[nm](xs[nmX], ys[nmY]) \
                        for nm in metricNames}
                edge.update({
                    'a': a,
                    'b': b,
                    "dstName": nmX,
                    "srcName": nmY,
                    "srcDelta": d,
                    "sampleFactor": sf,
                    "dstEx": xsEx[nmX],
                    "srcEx": ysEx[nmY],
                })

                yield edge

# }}} def calculateEdges

def svgNodes(cfg, evs): # {{{

    measureNames = list(evs.keys())
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

    metEx = metric("Ex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    metCov = metric("Cov", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    metCex = metric("Cex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)

    # Each node displays blob with 2D color.
    #   orig nodes display colorspace1D( E[orig] )
    #     except normal.orig nodes which display colorspace2D( E[orig], Cov(orig,orig) )
    #   refl nodes display colorspace1D( E[refl] )
    #     except normal.refl nodes which display colorspace2D( E[refl], Cov(refl,refl) )
    #   rise nodes display colorspace2D( 2*E[rise], Cex(rise,orig) )
    #   fall nodes display colorspace2D( 2*E[fall], Cex(fall,refl) )
    # However, stats contains numbers to be displayed which are slightly
    # different.
    #   orig nodes print E[orig]
    #     normal.orig nodes also print Cov(orig,orig)
    #   refl nodes print E[refl]
    #     normal.refl nodes also print Cov(refl,refl)
    #   rise nodes print E[rise] and Cex(rise,orig)
    #   fall nodes print E[fall] and Cex(fall,refl)

    def secondStat(nm, mt, st, bn): # {{{
        # NOTE: Logic paired with statsToBlobRgb().
        # NOTE: Logic paired with statsToTitle().
        if "normal" == mt:
            ret = metCov(evs[nm], evs[nm])
        elif siblingIs1stDer(st):
            assert mt in ("bstate", "threshold")
            assert st in ("rise", "fall")
            partner = {
                "rise": '.'.join([mt, "orig", bn]),
                "fall": '.'.join([mt, "refl", bn]),
            }[st]
            ret = metCex(evs[nm], evs[partner])
        else:
            ret = None

        return ret
    # }}} def secondStat

    stats = {nm: ( metEx(evs[nm]), secondStat(nm, mt, st, bn) ) \
             for nm,(mt,st,bn) in zip(measureNames, nameParts)}

    def statsToBlobRgb(nm, mt, st, bn): # {{{
        statA, statB = stats[nm]
        assert 0 <= statA <= 1, statA

        # NOTE: Logic paired with secondStat().
        # NOTE: Logic paired with statsToTitle().
        if "normal" == mt:
            assert 0 <= statB <= 1, statB
            ret = rgb2D(statA, statB)
        elif siblingIs1stDer(st):
            # stat = ( E[rise], E[rise | orig] )
            #   OR   ( E[fall], E[fall | refl] )
            assert mt in ("bstate", "threshold")
            assert st in ("rise", "fall")
            assert 0 <= statA <= 0.5
            assert 0 <= statB <= 1, statB
            ret = rgb2D(2*statA, statB)
        else:
            assert mt in ("event", "bstate", "threshold")
            assert st in ("orig", "refl")
            assert statB is None
            ret = rgb1D(statA)

        return ret
    # }}} def statsToBlobRgb

    def statsToTitle(nm, mt, st, bn): # {{{
        statA, statB = stats[nm]
        assert 0 <= statA <= 1, statA

        # NOTE: Logic paired with secondStat().
        # NOTE: Logic paired with statsToBlobRgb().
        if "normal" == mt:
            assert 0 <= statB <= 1, statB

            # E[rise] = 12.34%
            # Cov[rise|rise] = 45.67%
            ret = '\n'.join((
                "%s[%s] = %.2f%%" % (
                    mapMetricNameToHtml["Ex"],
                    mapSiblingTypeToHtml[st],
                    100*statA,
                ),
                "%s(%s,%s) = %.2f%%" % (
                    mapMetricNameToHtml["Cov"],
                    mapSiblingTypeToHtml[st],
                    mapSiblingTypeToHtml[st],
                    100*statB,
                ),
            ))
        elif siblingIs1stDer(st):
            # stat = ( E[rise], E[rise | orig] )
            #   OR   ( E[fall], E[fall | refl] )
            assert mt in ("bstate", "threshold")
            assert st in ("rise", "fall")
            assert 0 <= statA <= 0.5
            assert 0 <= statB <= 1, statB

            # E[rise] = 12.34%
            # E[rise|orig] = 45.67%
            ret = '\n'.join((
                "%s[%s] = %.2f%%" % (
                    mapMetricNameToHtml["Ex"],
                    mapSiblingTypeToHtml[st],
                    100*statA
                ),
                "%s[%s|%s] = %.2f%%" % (
                    mapMetricNameToHtml["Cex"],
                    mapSiblingTypeToHtml[st],
                    mapSiblingTypeToHtml[{"rise": "orig", "fall": "refl"}[st]],
                    100*statB,
                ),
            ))
        else:
            assert mt in ("event", "bstate", "threshold")
            assert st in ("orig", "refl")
            assert statB is None
            # E[orig] = 12.34%
            ret = "%s[%s] = %.2f%%" % (
                mapMetricNameToHtml["Ex"],
                mapSiblingTypeToHtml[st],
                100*statA,
            )

        return ret
    # }}} def statsToBlobRgb

    nodes = \
        (nodeFmts[st].format(
            measureName=nm,
            siblingType=st,
            measureType=mt,
            baseName=bn,
            centerX=nodeCenters[nm][0],
            centerY=nodeCenters[nm][1],
            symbolFill=mapMeasureTypeToSymbolFill[mt],
            tombstoneFill=mapMeasureTypeToTombstoneFill[mt],
            blobRgb=statsToBlobRgb(nm, mt, st, bn),
            statsTitle=statsToTitle(nm, mt, st, bn),
            symbol=mapSiblingTypeToHtml[st]) \
         for nm,(mt,st,bn) in zip(measureNames, nameParts))

    # }}} nodes

    # {{{ identicons
    # One per sibling group.
    identiconRadius = sibgrpRadius + identiconSeparationMul*sibgrpSeparation

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
        a, b = edge['a'], edge['b']
        metA, metB = edge[a], edge[b] if b else None

        normAB = l2Norm(metA, metB) if b else metA

        style = ';'.join((
            'stroke: #%s' % (rgb2D(metA, metB) if b else rgb1D(metA)),
            'stroke-width: %0.2f' % normAB * 1,
            'stroke-opacity: %0.2f' % normAB * 1,
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

    nodeStrs, (canvasWidth, canvasHeight), nodeCenters = svgNodes(cfg, evs)

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

    ret_.append('</svg>')
    return ret_
# }}} def svgNetgraph

if __name__ == "__main__":
    assert False, "Not a standalone script."
