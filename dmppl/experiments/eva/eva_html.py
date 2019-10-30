
# Standard library imports
from itertools import chain, product
import os
import sys
import time

# PyPI library imports
import toml
import numpy as np

# Local library imports
from dmppl.math import l2Norm
from dmppl.base import dbg, info, verb, joinP, tmdiff, rdTxt
from dmppl.color import rgb1D, rgb2D

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
import dmppl.experiments.eva.eva_common as eva

# Version-specific imports
version_help = "Python 2.7 or 3.4+ required."
if sys.version_info[0] == 2:
    assert sys.version_info[1] >= 7, version_help
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from urlparse import parse_qs
elif sys.version_info[0] == 3:
    assert sys.version_info[1] >= 4, version_help
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs
else:
    assert False, version_help

def sliderControls(): # {{{
    ret = '''\
<div class="controls">
    <input id="thr_max_slider" type="range"
           min="0.0" max="1.0"
           step="0.01" value="1.0"/>
    <p><span id="thr_min_val"></span>
       &le; Pr <span id="thr_andxor"></span> Pr &le;
       <span id="thr_max_val"></span></p>
    <input id="thr_min_slider" type="range"
           min="0.0" max="1.0"
           step="0.01" value="0.0"/>
</div>
'''
    return ret
# }}} def sliderControls

def popoverUl(ulTitle, links): # {{{
    '''Return a string for use in bootstrap popover.
    '''

    assert isinstance(ulTitle, str) and len(ulTitle), ulTitle
    for link in links:
        assert isinstance(link, str) and len(link), link

    liFmt = '<li> %s </li>'
    lis = (liFmt % link for link in links)

    fmt = '''\
<a tabindex="0"
   role="button"
   href="#"
   title="{ulTitle}"
   data-html="true"
   data-toggle="popover"
   data-trigger="click"
   data-content="<ul>{lis}</ul>">{ulTitle}</a>
'''
    return fmt.format(ulTitle=ulTitle, lis=''.join(lis)).strip()
# }}} def popoverUl

def htmlTopFmt(body, inlineJs=True, inlineCss=True): # {{{
    '''Return a string with HTML headers for JS and CSS.
    '''

    fnamesJs = (joinP(eva.appPaths.share, fname) for fname in \
                ("jquery-3.3.1.slim.min.js",
                 "bootstrap-3.3.7.min.js",
                 "eva.js"))

    fnamesCss = (joinP(eva.appPaths.share, fname) for fname in \
                 ("bootstrap-3.3.7.min.css",
                  "eva.css"))

    jsTxts = (('<script> %s </script>' % rdTxt(fname)) \
              if inlineJs else \
              ('<script type="text/javascript" src="%s"></script>' % fname)
              for fname in fnamesJs)

    cssTxts = (('<style> %s </style>' % rdTxt(fname)) \
               if inlineCss else \
               ('<link rel="stylesheet" type="text/css" href="%s">' % fname)
               for fname in fnamesCss)

    ret = (
        '<!DOCTYPE html>',
        '<html>',
        '  <head>',
        '\n'.join(chain(jsTxts, cssTxts)),
        '  </head>',
        '  <body>',
        '\n'.join(body),
        '  </body>',
        '</html>',
    )
    return '\n'.join(r.strip() for r in ret)
# }}} def htmlTopFmt

def evaLink(f, g, u, x, y, txt, escapeQuotes=False): # {{{
    '''Return the link to a data view.
    '''
    assert f is None or isinstance(f, str), type(f)
    assert g is None or isinstance(g, str), type(g)
    if f is not None:
        assert f in eva.metricNames, f
    if g is not None:
        assert g in eva.metricNames, g
    assert f or g
    assert u is None or isinstance(u, int), type(u)
    assert x is None or isinstance(x, str), type(x)
    assert y is None or isinstance(y, str), type(y)

    assert isinstance(txt, str), type(txt)

    parts_ = []

    if f is not None:
        parts_.append("f=" + str(f))

    if g is not None:
        parts_.append("g=" + str(g))

    if u is not None:
        parts_.append("u=" + str(u))

    if x is not None:
        parts_.append("x=" + str(x))

    if y is not None:
        parts_.append("y=" + str(y))

    ret = (
        '<a href=',
        '&quot;' if escapeQuotes else '"',
        './?',
        '&'.join(parts_),
        '&quot;' if escapeQuotes else '"',
        '>',
        str(txt),
        '</a>',
    )
    return ''.join(ret)
# }}} def evaLink

def fnDisplay(f, g): # {{{
    assert f is None or isinstance(f, str), type(f)
    assert g is None or isinstance(g, str), type(g)
    if f is not None:
        assert f in eva.metricNames, f
    if g is not None:
        assert g in eva.metricNames, g
    assert f or g, (f, g)
    return ("{%s,%s}" % (f, g)) if f and g else (f if f else g)
# }}} def fnDisplay

def uDisplay(u): # {{{
    assert u is None or isinstance(u, int), type(u)
    return "..." if u is None else str(u)
# }}} def uDisplay

def xDisplay(x): # {{{
    assert x is None or isinstance(x, str), type(x)
    return "..." if x is None else x
# }}} def xDisplay

def yDisplay(y): # {{{
    assert y is None or isinstance(y, str), type(y)
    return "..." if y is None else y
# }}} def yDisplay

evaTitleFmt = "{fn}(x={x} | y={y}<sub>&lang;&delta;&rang;</sub> ; u={u})"

def evaTitleText(f, g, u, x, y): # {{{
    '''Return the title of a data view as a simple string without nested markup.
    '''
    # NOTE: Assertions handled in *Display().
    return evaTitleFmt.format(fn=fnDisplay(f, g),
                              x=xDisplay(x),
                              y=yDisplay(y),
                              u=uDisplay(u))
# }}} def evaTitleText

def evaTitleAny(fn, u, x, y): # {{{
    '''Return the title of a data view substituing in arbitary markup strings.
    '''
    assert isinstance(fn, str), type(fn)
    assert isinstance(u, str), type(u)
    assert isinstance(x, str), type(x)
    assert isinstance(y, str), type(y)
    assert 0 < len(fn), fn
    assert 0 < len(u), u
    assert 0 < len(x), x
    assert 0 < len(y), y

    return evaTitleFmt.format(fn=fn, x=x, y=y, u=u)
# }}} def evaTitleAny

def tableTitleRow(f, g, u, x, y, cfg, dsfDeltas, vcdInfo): # {{{
    '''Return a string with HTML <tr>.
    '''
    measureNames = vcdInfo["unitIntervalVarNames"]
    winStride = cfg.windowsize - cfg.windowoverlap
    nDeltas = len(dsfDeltas)

    # NOTE: u may be 0 --> Cannot use "if u".
    if u is None:
        # Possibly overestimate colspanTitle but browsers handle it properly.
        # No need for prev/next navigation since u varies over rows.
        colspanTitle = 8 + nDeltas

        navPrevNext = ''
    else:
        assert isinstance(u, int), type(u)
        # Exactly choose colspan of whole table, then take off some to make
        # room for prev/next navigation links.
        # TODO: Exact number (first 7) is from number of columns from sibling
        # measurements - Need to correct when siblings are implemented.
        colspanTitle = 7 + nDeltas - 7

        navPrevNext = ' '.join((
            '<th class="nav_u" colspan="5">',
            evaLink(f, g, u - winStride, x, y, "prev"),
            evaLink(f, g, u + winStride, x, y, "next"),
            '</th>',
        ))

    # NOTE: f and g must be valid strings containing name of measurement.
    if f and g:
        fnLinks = [evaLink(fNm, gNm, u, x, y,
                           evaTitleText(fNm, gNm, u, x, y),
                           escapeQuotes=True) \
                   for fNm in eva.metricNames \
                   for gNm in eva.metricNames \
                   if fNm != f and gNm != g and fNm != gNm]
    elif f:
        fnLinks = [evaLink(fNm, None, u, x, y,
                           evaTitleText(fNm, None, u, x, y),
                           escapeQuotes=True) \
                   for fNm in eva.metricNames \
                   if fNm != f]
    elif g:
        fnLinks = [evaLink(None, gNm, u, x, y,
                           evaTitleText(None, gNm, u, x, y),
                           escapeQuotes=True) \
                   for gNm in eva.metricNames \
                   if gNm != g]
    else:
        assert False # Checking already performed in evaHtmlString()
    fnPopover = popoverUl(fnDisplay(f, g), fnLinks)

    xLinks = [evaLink(f, g, u, xNm, y,
                      evaTitleText(f, g, u, xNm, y),
                      escapeQuotes=True) \
              for xNm in measureNames \
              if xNm != x]
    xPopover = popoverUl(xDisplay(x), xLinks)

    yLinks = [evaLink(f, g, u, x, yNm,
                      evaTitleText(f, g, u, x, yNm),
                      escapeQuotes=True) \
              for yNm in measureNames \
              if yNm != y]
    yPopover = popoverUl(yDisplay(y), yLinks)


    ret = (
        '<tr>',
        '  <th class="tabletitle" colspan="%d">' % colspanTitle,
        evaTitleAny(fnPopover, uDisplay(u), xPopover, yPopover),
        '  </th>',
        navPrevNext,
        '</tr>',
    )
    return ''.join(r.strip() for r in ret)
# }}} def tableTitleRow

mapSiblingTypeToHtmlEntity = {
    "measure":      "&#xb7;",   # MIDDLE DOT
    "reflection":   "&#x00ac;", # NOT SIGN
    "rise":         "&#x2191;", # UPWARDS ARROW
    "fall":         "&#x2193;", # DOWNWARDS ARROW
}
nSibsMax = len(mapSiblingTypeToHtmlEntity.keys())

def tableHeaderRows(f, g, u, x, y, dsfDeltas, exSibRow): # {{{
    '''Return a string with HTML one or more <tr>.
    '''
    sibThTxtFmt = "E[%s]<sub>%s</sub>" # symbol, x/y

    def sibHiThs(nm, xNotY, rowspan, values=None): # {{{

        measureType, siblingType, baseName = eva.measureNameParts(nm)

        siblings = \
            [eva.measureNameParts(s) \
             for s in eva.measureSiblings(nm)]

        sibNames = \
            ['.'.join((mt,st,mn)) \
             for mt,st,mn in siblings]

        if values is not None:
            assert isinstance(values, (list, tuple)), type(values)
            assert len(values) == len(siblings)

        possibleClasses = ("sibsel", "th_d", "xsib" if xNotY else "ysib")

        classLists = \
            [possibleClasses[(0 if st == siblingType else 1):] \
             for mt,st,mn in siblings]

        attrClasses = \
            ['class="%s"' % ' '.join(c for c in cs)
             for cs in classLists]

        attrRowspans = \
            [('rowspan="%d"' % rowspan) if 1 < rowspan else '' \
             for _ in siblings]

        attrStyles = \
            ['style="background-color:#%s"' % rgb1D(v) \
             for v in values] if values is not None else \
            ['' for _ in siblings]

        attrTitles = \
            ['title="%0.02f"' % v \
             for v in values] if values is not None else \
            ['' for _ in siblings]

        sibAttrs = [' '.join(attrs) for attrs in zip(attrClasses,
                                                     attrRowspans,
                                                     attrStyles,
                                                     attrTitles)]
        sibLinkTxts = \
            [sibThTxtFmt % (mapSiblingTypeToHtmlEntity[st],
                            'x' if xNotY else 'y') \
             for mt,st,mn in siblings]

        sibLinks = \
            [evaLink(f, g, u, fnm, y, txt) if xNotY else \
             evaLink(f, g, u, x, fnm, txt) \
             for fnm,txt in zip(sibNames, sibLinkTxts)]

        sibValueTxts = \
            ['<br/> %0.02f' % v for v in values] \
            if values is not None else \
            ['' for _ in siblings]


        padThs = ['<th class="th_d"></th>' \
                  for _ in range(nSibsMax - len(siblings)) \
                  if values is not None]

        fmt = '<th {attrs}> {partA} {partB} </th>'
        ret = [fmt.format(attrs=attrsStr, partA=linkStr, partB=valueStr) \
               for attrsStr,linkStr,valueStr in zip(sibAttrs,
                                                    sibLinks,
                                                    sibValueTxts)] + padThs

        return ret
    # }}} sibHiThs

    def sibLoThs(xNotY): # {{{

        sibTxts = \
            [sibThTxtFmt % (mapSiblingTypeToHtmlEntity[st],
                            'x' if xNotY else 'y') \
             for st in mapSiblingTypeToHtmlEntity.keys()]

        classes = ("th_d", "xsib" if xNotY else "ysib")

        attrClasses = \
            ['class="%s"' % ' '.join(c for c in classes)
             for _ in mapSiblingTypeToHtmlEntity.keys()]

        fmt = '<th {attrs}> {partA} </th>'

        ret = [fmt.format(attrs=attrsStr, partA=txt) \
               for attrsStr,txt in zip(attrClasses, sibTxts)]
        return ret
    # }}} sibLoThs

    if x and y:
        assert u is None, u
        rowVar = 'u'
        #     +--------+--------+--------+--------+--------+--------+--------+--------+
        # hi  |        |        |        |        |        |        |        |        |
        #     + E[.]_x + E[¬]_x + E[↑]_x + E[↓]_x + E[.]_y + E[¬]_y + E[↑]_y + E[↓]_y +
        # lo  |        |        |        |        |        |        |        |        |
        #     +--------+--------+--------+--------+--------+--------+--------+--------+
        #
        # Expectation of sibling measurements in each window,
        # Span both rows.

        xSibHiThs, ySibHiThs = \
            sibHiThs(x, True,  2), \
            sibHiThs(y, False, 2)
        xSibLoThs, ySibLoThs = [], []

    elif x:
        # x is constant but y is varying
        assert y is None, y
        rowVar = 'y'

        # 1. CASE: x has max number of siblings.
        #     +--------+--------+--------+--------+
        # hi  + E[.]_x | E[¬]_x | E[↑]_x | E[↓]_x | clickable, to x siblings
        #     + 0.1234 | 0.1234 | 0.1234 | 0.1234 |
        #     +--------+--------+--------+--------+
        # lo  | E[.]_y | E[¬]_y | E[↑]_y | E[↓]_y | non-clickable column heads
        #     +--------+--------+--------+--------+
        #
        # 2. CASE: x has fewer siblings than max.
        #     +--------+--------+--------+--------+
        # hi  + E[.]_x |                          |  clickable, to x siblings
        #     + 0.1234 |                          |
        #     +--------+--------+--------+--------+
        # lo  | E[.]_y | E[¬]_y | E[↑]_y | E[↓]_y | non-clickable column heads
        #     +--------+--------+--------+--------+
        #
        # NOTE: Values of x sibling's expectation by number and bgcolor.

        xSibHiThs, ySibHiThs = sibHiThs(x, True, 1, values=exSibRow), []
        xSibLoThs, ySibLoThs = [], sibLoThs(False)

    elif y:
        # y is constant but x is varying
        assert x is None, x
        rowVar = 'x'

        # 1. CASE: y has max number of siblings.
        #     +--------+--------+--------+--------+
        # hi  + E[.]_y | E[¬]_y | E[↑]_y | E[↓]_y | clickable, to y siblings
        #     + 0.1234 | 0.1234 | 0.1234 | 0.1234 |
        #     +--------+--------+--------+--------+
        # lo  | E[.]_x | E[¬]_x | E[↑]_x | E[↓]_x | non-clickable column heads
        #     +--------+--------+--------+--------+
        #
        # 2. CASE: y has fewer siblings than max.
        #     +--------+--------+--------+--------+
        # hi  + E[.]_y |                          |  clickable, to y siblings
        #     + 0.1234 |                          |
        #     +--------+--------+--------+--------+
        # lo  | E[.]_x | E[¬]_x | E[↑]_x | E[↓]_x | non-clickable column heads
        #     +--------+--------+--------+--------+
        #
        # NOTE: Values of y sibling's expectation by number and bgcolor.

        xSibHiThs, ySibHiThs = [], sibHiThs(y, False, 1, values=exSibRow)
        xSibLoThs, ySibLoThs = sibLoThs(True), []

    else:
        assert False

    hiSibThs = xSibHiThs + ySibHiThs
    loSibThs = xSibLoThs + ySibLoThs

    nDeltas = len(dsfDeltas)
    nLeftDeltas, nRightDeltas = nDeltas // 2, nDeltas // 2 - 1
    deltaThs = ('<th class="th_d">%d</th>' % d for dsf,d in dsfDeltas)

    ret = (
        '<tr>',
          '\n'.join(hiSibThs),
          ' <th class="varying" rowspan="2">%s</th>' % rowVar,
          ' <th colspan="%d"></th>' % nLeftDeltas,
          ' <th>&delta;</th>',
          ' <th colspan="%d"></th>' % nRightDeltas,
        '</tr>',
        '<tr>',
          '\n'.join(loSibThs),
          # varying spans both rows
          ''.join(deltaThs),
        '</tr>',
    )
    return '\n'.join(r.strip() for r in ret)
# }}} def tableHeaderRows

def calculateTableData(f, g, u, x, y, cfg, dsfDeltas, vcdInfo): # {{{
    '''Read in relevant portion of EVS and calculate values for table cells.

    Relevant names:
      varying u, fixed x, fixed y:
          x siblings
          y siblings
      varying x or y, fixed u:
          all

    Relevant times:
      varying u, fixed x, fixed y:
          all
      varying x or y, fixed u:
          [u-deltabk, u+windowsize+deltafw)
    '''
    measureNames = vcdInfo["unitIntervalVarNames"]

    firstTime = vcdInfo["timechunkTimes"][0]
    lastTime = vcdInfo["timechunkTimes"][-1]
    evsStartTime = (firstTime if u is None else u) - cfg.deltabk
    evsFinishTime = (max(lastTime, firstTime + cfg.windowsize) \
                     if u is None else \
                     u + cfg.windowsize) + cfg.deltafw + 1

    winUs = eva.winStartTimes(firstTime, lastTime,
                                  cfg.windowsize, cfg.windowoverlap) \
                if u is None else None

    # Read in all relevant data to one structure.
    evsNames = (eva.measureSiblings(x) + eva.measureSiblings(y)) \
        if u is None else measureNames
    evs = eva.rdEvs(evsNames, evsStartTime, evsFinishTime, cfg.fxbits)

    # Each row in evs is guaranteed to be of the same correct length.
    for nm,row in evs.items():
        assert nm in measureNames, (nm, measureNames)
        assert row.shape == (evsFinishTime - evsStartTime,), \
            (row.shape, evsStartTime, evsFinishTime)

    fMetric, gMetric = \
        eva.metric(f, cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits), \
        eva.metric(g, cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    fns = (fMetric, gMetric,) if g else (fMetric,)
    nFns = len(fns)

    nRows = len(winUs) if u is None else len(measureNames)
    nCols = len(dsfDeltas) # Columns in fnUXY, not the sibling sections.
    fnUXYShape = (nFns, nRows, nCols)

    # All result arrays have the same dtype.
    dtype = np.float32 if 0 == cfg.fxbits else fxDtype(cfg.fxbits)

    # Allocate then fill main result array.
    # TODO: parallelize by n_jobs
    fnUXY = np.empty(fnUXYShape, dtype=dtype)
    fnUXYIter = product(range(nFns), range(nRows), range(nCols))
    for fnNum,rowNum,colNum in fnUXYIter:

        dsf, delta = dsfDeltas[colNum]
        assert isinstance(dsf, int), type(dsf)
        assert isinstance(delta, int), type(delta)

        keyX, keyY = \
            (x if x else measureNames[rowNum]), \
            (y if y else measureNames[rowNum])

        # When u is varying, each row selects a window.
        # When u is fixed, evs only holds data for that window
        startIdxX = eva.timeToEvsIdx(winUs[rowNum] if u is None else u,
                                     evsStartTime)
        startIdxY = startIdxX + delta
        assert isinstance(startIdxX, int), type(startIdxX)
        assert isinstance(startIdxY, int), type(startIdxY)
        assert 0 <= startIdxX, startIdxX
        assert 0 <= startIdxY, startIdxY

        finishIdxX, finishIdxY = \
            (startIdxX + cfg.windowsize), \
            (startIdxY + cfg.windowsize)
        assert startIdxX < finishIdxX, (startIdxX, finishIdxX)
        assert startIdxY < finishIdxY, (startIdxY, finishIdxY)

        evsX, evsY = \
            evs[keyX][startIdxX:finishIdxX], \
            evs[keyY][startIdxY:finishIdxY]
        assert evsX.shape == evsY.shape, (evsX.shape, evsY.shape)

        fnUXY[fnNum][rowNum][colNum] = fns[fnNum](evsX, evsY)

    expectation = eva.metric("Ex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)

    def sibEx(s): # {{{
        '''Allocate then fill a sibling expectation array.

        s must be either x or y
        '''
        assert s in [x, y], (s, x, y)

        siblings = eva.measureSiblings(s) if s else None

        nRowsEx = 1 if s and not (x and y) else nRows
        nColsEx = len(siblings) if s else nSibsMax

        arr = np.empty((nRowsEx, nColsEx), dtype=dtype)
        sibExIter = product(range(nRowsEx), range(nColsEx))

        for rowNum,colNum in sibExIter:

            if s:
                key = siblings[colNum]
            else:
                rowSiblings = eva.measureSiblings(measureNames[rowNum])

                # Some measures have less siblings.
                if colNum < len(rowSiblings):
                    key = rowSiblings[colNum]
                else:
                    # NOTE: The uninitialized value should never be used.
                    continue

            startIdx = eva.timeToEvsIdx(winUs[rowNum] if u is None else u,
                                        evsStartTime)
            finishIdx = startIdx + cfg.windowsize

            evsRow = evs[key][startIdx:finishIdx]

            arr[rowNum][colNum] = expectation(evsRow)

        return arr
    # }}} def sibEx

    xEx = sibEx(x)
    yEx = sibEx(y)

    varCol = winUs if u is None else measureNames

    if x and y:
        assert xEx.shape == (nRows, len(eva.measureSiblings(x))), xEx.shape
        assert yEx.shape == (nRows, len(eva.measureSiblings(y))), yEx.shape
    elif x:
        assert xEx.shape == (1, len(eva.measureSiblings(x))), xEx.shape
        assert yEx.shape == (nRows, nSibsMax), yEx.shape
    elif y:
        assert xEx.shape == (nRows, nSibsMax), xEx.shape
        assert yEx.shape == (1, len(eva.measureSiblings(y))), yEx.shape
    else:
        assert False

    return xEx, yEx, fnUXY, varCol
# }}} def calculateTableData

def tdCellFnUXY(fnUXY, rowNum, colNum): # {{{
    assert fnUXY.shape[0] in [1, 2], fnUXY.shape
    is2D = fnUXY.shape[0] == 2

    fValue = float(fnUXY[0][rowNum][colNum])
    gValue = float(fnUXY[1][rowNum][colNum]) if is2D else None

    attrClass = 'class="%s"' % ' '.join(c for c in ("d",))

    attrStyle = \
        ('style="background-color:#%s"' % rgb2D(fValue, gValue)) \
        if is2D else \
        ('style="background-color:#%s"' % rgb1D(fValue))

    attrTitle = \
        ('title="%0.02f,%0.02f"' % (fValue, gValue)) \
        if is2D else \
        ('title="%0.02f"' % (fValue))

    # NOTE: L2norm is just for the slider controls which require a scalar.
    attrValue = \
        ('value="%0.06f"' % l2Norm(fValue, gValue)) \
        if is2D else \
        ('value="%0.06f"' % (fValue))

    attrs = ' '.join((attrClass, attrStyle, attrTitle, attrValue))

    txt = \
        ('%0.02f </br> %0.02f' % (fValue, gValue)) \
        if is2D else \
        ('%0.02f' % (fValue))

    return '<td %s> %s </td>' % (attrs, txt)
# }}} def tdCellFnUXY

def tdCellExSib(exSib, rowNum, colNum, rowNSibs): # {{{

    fmt = '<td %s> %s </td>'
    attrClass = 'class="%s"' % ' '.join(c for c in ("d",))

    # Just a padding cell as this measure doesn't have the max number of
    # siblings.
    if colNum >= rowNSibs:
        return fmt % (attrClass, '-')

    value = float(exSib[rowNum][colNum])

    attrStyle = 'style="background-color:#%s"' % rgb1D(value)
    attrTitle = 'title="%0.06f"' % value
    attrValue = 'value="%0.06f"' % value
    attrs = ' '.join((attrClass, attrStyle, attrTitle, attrValue))

    txt = '%0.02f' % value

    return fmt % (attrs, txt)
# }}} def tdCellExSib

def tableDataRows(f, g, u, x, y, vcdInfo, exSib, varCol, fnUXY): # {{{
    measureNames = vcdInfo["unitIntervalVarNames"]

    if x and y:
      assert exSib.shape[1] <= 2*nSibsMax, \
          (exSib.shape, mapSiblingTypeToHtmlEntity)
    else:
      assert exSib.shape[1] <= nSibsMax, \
          (exSib.shape, mapSiblingTypeToHtmlEntity)

    assert fnUXY.shape[0] in [1, 2], \
        fnUXY.shape

    assert exSib.shape[0] == len(varCol) == fnUXY.shape[1], \
        (exSib.shape, len(varCol), fnUXY.shape)
    nRows = exSib.shape[0]

    varTds = ['<td class="varying"> %s </td>' % str(v) for v in varCol]

    def tableDataRow(rowNum): # {{{
        rowNSibs = len(eva.measureSiblings(measureNames[rowNum])) \
                   if u else 2*nSibsMax

        sibTds = (tdCellExSib(exSib, rowNum, colNum, rowNSibs) \
                  for colNum in range(exSib.shape[1]))

        fnTds = (tdCellFnUXY(fnUXY, rowNum, colNum) \
                 for colNum in range(fnUXY.shape[2]))

        ret = (
            '<tr class="data">',
              ' '.join(sibTds),
              varTds[rowNum],
              ' '.join(fnTds),
            '</tr>',
        )
        return '\n'.join(ret)
    # }}} def tableDataRow

    return '\n'.join(tableDataRow(rowNum) for rowNum in range(nRows))
# }}} def tableDataRows

def evaHtmlString(args, cfg, request): # {{{
    '''Return a string of HTML.

    f     g     -->
    None  None  invalid
    None  Func  1D color, swap f,g
    Func  None  1D color
    Func  Func  2D color

    u     x     y     -->
    None  None  None  Default values
    None  None  Metr  invalid
    None  Metr  None  invalid
    None  Metr  Metr  Table varying u over rows, delta over columns
    Int   None  None  Network graph
    Int   None  Metr  Table varying x over rows, delta over columns
    Int   Metr  None  Table varying y over rows, delta over columns
    Int   Metr  Metr  Table row varying delta over columns
    '''
    f, g, u, x, y = \
        request['f'], request['g'], request['u'], request['x'], request['y']

    verb("{f,g}(x|y;u) <-- {%s,%s}(%s|%s;%s)" % (f, g, x, y, u))

    if f is None and isinstance(g, str):
        # 1D color
        assert g in eva.metricNames, g
        f, g = g, f
    elif isinstance(f, str) and g is None:
        # 1D color
        assert f in eva.metricNames, f
    elif isinstance(f, str) and isinstance(g, str):
        # 2D color
        assert f in eva.metricNames, f
        assert g in eva.metricNames, g
    else:
        assert False, "At least one of f,g must be string of function name." \
                      " (f%s=%s, g%s=%s)" % (type(f), f, type(g), g)

    if u is None and isinstance(x, str) and isinstance(y, str):
        # Table varying u over rows, delta over columns
        tableNotNetwork = True

    elif isinstance(u, str) and x is None and y is None:
        # Network graph
        tableNotNetwork = False

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and x is None and isinstance(y, str):
        # Table varying x over rows, delta over columns
        tableNotNetwork = True

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and isinstance(x, str) and y is None:
        # Table varying y over rows, delta over columns
        tableNotNetwork = True

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and isinstance(x, str) and isinstance(y, str):
        # Table row varying delta over columns
        tableNotNetwork = True

        u = int(u)
        assert 0 <= u, u

    else:
        assert False, "Invalid combination of u,x,y." \
                      " (u=%s, x=%s, y=%s)" % (u, x, y)

    vcdInfo = toml.load(eva.paths.fname_meainfo)

    # Every view varies delta - tables by horizontal, networks by edges.
    dsfDeltas = eva.cfgDsfDeltas(cfg) # [(<downsample factor>, <delta>), ...]

    # Sort by delta value, not by downsampling factor.
    dsfDeltas.sort(key=lambda dsf_d: dsf_d[1])

    body_ = []
    if tableNotNetwork:
        xEx, yEx, fnUXY, varCol = \
            calculateTableData(f, g, u, x, y,
                               cfg, dsfDeltas, vcdInfo)

        _exSibRow, exSib = \
            (np.empty((1, 0)),
             np.concatenate((xEx, yEx), axis=1)) if x and y else \
            (xEx, yEx) if x else \
            (yEx, xEx)

        assert _exSibRow.shape[0] == 1, _exSibRow.shape
        exSibRow = [float(v) for v in _exSibRow[0]]

        body_.append(sliderControls())
        body_.append("<table>")

        # Top-most row with title (with nav popovers), and prev/next.
        body_.append(tableTitleRow(f, g, u, x, y,
                                   cfg, dsfDeltas, vcdInfo))

        # Column headers with delta values. Both hi and lo rows.
        body_.append(tableHeaderRows(f, g, u, x, y,
                                     dsfDeltas,
                                     exSibRow))

        body_.append(tableDataRows(f, g, u, x, y,
                                   vcdInfo,
                                   exSib, varCol, fnUXY))

        body_.append("</table>")
    else:
        body_.append("TODO: networkNotTable") # TODO: Holder for SVG

    # Avoid inline JS or CSS for browser caching, but use for standalone files.
    inlineHead = (args.httpd_port == 0)

    return htmlTopFmt(body_, inlineHead, inlineHead)
# }}} def evaHtmlString

class EvaHTMLException(Exception): # {{{
    pass
# }}} class EvaHTMLException

class EvaHTTPServer(HTTPServer): # {{{
    def serve_forever(self, args, cfg):
        self.RequestHandlerClass.args = args
        self.RequestHandlerClass.cfg = cfg
        HTTPServer.serve_forever(self)
# }}} class EvaHTTPServer

class EvaHTTPRequestHandler(BaseHTTPRequestHandler): # {{{

    # These are initialized by EvaHTTPServer.serve_forever()
    args, cfg = None, None

    def parseGetRequest(self, path): # {{{
        '''Parse and sanitize GET path.
        '''
        parsed = parse_qs(path.strip("/?")) # Parse query string.
        ret = {k: (parsed[k][0] if k in parsed.keys() else None) \
               for k in ('f', 'g', 'u', 'x', 'y')}
        return ret
    # }}} def parseGetRequest

    def do_GET(self): # {{{

        # Remove leading / which is usually (always?) present.
        self.path = self.path.lstrip('/')

        # Send response.
        if len(self.path) and not self.path.startswith("?") and \
            (self.path.endswith(".css") or self.path.endswith(".js")):

            # Strip off any relative paths to only find CSS and JS files.
            fname = joinP(eva.appPaths.share, os.path.basename(self.path))

            try:
                response = rdTxt(fname)

                self.send_response(200)

                if fname.endswith(".js"):
                    self.send_header("Content-Type",
                                     "application/javascript; charset=utf-8")
                elif fname.endswith(".css"):
                    self.send_header("Content-Type",
                                     "text/css; charset=utf-8")

                responseBytes = response.encode("utf-8")

            except:
                self.send_error(404, "Invalid JS or CSS GET request!")
                return

        elif len(self.path) and self.path.endswith("favicon.ico"):
            # Bug in Chrome requests favicon.ico with every request until it
            # gets 404'd.
            # https://bugs.chromium.org/p/chromium/issues/detail?id=39402
            try:
                faviconFpath = joinP(eva.appPaths.share, "eva_logo.png")
                responseBytes = open(faviconFpath, 'rb').read()

                self.send_response(200)
                self.send_header("Content-Type", "image/x-icon")
            except:
                self.send_error(404, "Cannot read favicon!")

        elif len(self.path) and not self.path.startswith("?"):
            # Unknown requests.
            self.send_response(404)
            return

        else:

            # Generate HTML string and send OK if inputs are valid.
            try:
                response = evaHtmlString(self.args, self.cfg,
                                         self.parseGetRequest(self.path))

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")

                responseBytes = response.encode("utf-8")

            except EvaHTMLException:
                self.send_error(404, "Invalid GET request!")
                return

        # Send HTTP headers.
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers
        self.send_header("Content-Length", "%d" % len(responseBytes))
        self.end_headers()

        # Send HTML.
        self.wfile.write(responseBytes)

        return
    # }}} def do_GET

# }}} class EvaHTTPRequestHandler

def runHttpDaemon(args, cfg): # {{{
    '''Run local HTTP/HTML daemon serving data visualization pages on request.
    '''

    verb("Starting HTTPD on TCP port %d..." % args.httpd_port, end='')

    httpd = EvaHTTPServer(('', args.httpd_port), EvaHTTPRequestHandler)

    verb("Running...")

    try:
        tm_start = time.time()
        httpd.serve_forever(args, cfg)
    except KeyboardInterrupt:
        tm_stop = time.time()
        verb("Stopped HTTPD server [%s]" % \
            tmdiff(tm_stop - tm_start))

    return
# }}} def runHttpDaemon

def evaHtml(args): # {{{
    '''Read in result directory like ./foo.eva/ and serve HTML visualizations.
    '''
    assert eva.initPathsDone

    try:
        cfg = eva.loadCfg()

        if 0 != args.httpd_port:
            runHttpDaemon(args, cfg)
        else:
            request = {'f': args.f,
                       'g': args.g,
                       'u': args.u,
                       'x': args.x,
                       'y': args.y}
            print(evaHtmlString(args, cfg, request))
    except IOError as e:
        msg = "IOError: %s: %s\n" % (e.strerror, e.filename)
        sys.stderr.write(msg)

    return 0
# }}} def evaHtml

if __name__ == "__main__":
    assert False, "Not a standalone script."
