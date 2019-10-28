
# Standard library imports
from itertools import chain
import os
import sys
import time

# PyPI library imports
import toml

# Local library imports
from dmppl.base import dbg, info, verb, joinP, tmdiff, rdTxt
from dmppl.color import rgb1D

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

def htmlTopFmt(inlineJs=True, inlineCss=True): # {{{
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
        '    {}',
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

def tableTitleRow(f, g, u, x, y, measureNames, dsfDeltas, winStride): # {{{
    '''Return a string with HTML <tr>.
    '''
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

    xLinks = [evaLink(f, g, u, xNm, None,
                      evaTitleText(f, g, u, xNm, None),
                      escapeQuotes=True) \
              for xNm in measureNames \
              if xNm != x]
    xPopover = popoverUl(xDisplay(x), xLinks)

    yLinks = [evaLink(f, g, u, None, yNm,
                      evaTitleText(f, g, u, None, yNm),
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

def tableHeaderRows(f, g, u, x, y, dsfDeltas, rowVar): # {{{
    '''Return a string with HTML one or more <tr>.
    '''
    assert isinstance(rowVar, str), type(rowVar)
    assert rowVar in ['u', 'x', 'y'], rowVar

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
            #assert len(values) == len(siblings) # TODO: uncomment


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
            ['<br/> %0.02f' % v \
             for v in values] if values is not None else \
            ['' for _ in siblings]



        fmt = '<th {attrs}> {partA} {partB} </th>'

        ret = [fmt.format(attrs=attrsStr, partA=linkStr, partB=valueStr) \
               for attrsStr,linkStr,valueStr in zip(sibAttrs,
                                                    sibLinks,
                                                    sibValueTxts)]
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

    # TODO: Use proper values
    sibValuesTODO_rm = [0.1, 0.2, 0.3, 0.4, 0.5]
    xSibValues = sibValuesTODO_rm
    ySibValues = sibValuesTODO_rm

    if x and y:
        assert u is None and rowVar == 'u', (u, rowVar)
        #     +--------+--------+--------+--------+--------+--------+--------+--------+
        # hi  |        |        |        |        |        |        |        |        |
        #     + E[.]_x + E[¬]_x + E[↑]_x + E[↓]_x + E[.]_y + E[¬]_y + E[↑]_y + E[↓]_y +
        # lo  |        |        |        |        |        |        |        |        |
        #     +--------+--------+--------+--------+--------+--------+--------+--------+
        #
        # Expectation of sibling measurements in each window,
        # Span both rows.

        xSibHiThs, ySibHiThs = \
            sibHiThs(x, True,  2, xSibValues), \
            sibHiThs(y, False, 2, ySibValues)
        xSibLoThs, ySibLoThs = [], []

    elif x:
        # x is constant but y is varying
        assert y is None and rowVar == 'y', (y, rowVar)

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

        xSibHiThs, ySibHiThs = sibHiThs(x, True, 1, xSibValues), []
        xSibLoThs, ySibLoThs = [], sibLoThs(False)

    elif y:
        # y is constant but x is varying
        assert x is None and rowVar == 'x', (x, rowVar)

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

        xSibHiThs, ySibHiThs = [], sibHiThs(y, False, 1, ySibValues)
        xSibLoThs, ySibLoThs = sibLoThs(True), []

    else:
        assert False

    hiSibThs = xSibHiThs + ySibHiThs
    loSibThs = xSibLoThs + ySibLoThs


    # Sort by delta value, not by downsampling factor.
    dsfDeltas.sort(key=lambda dsf_d: dsf_d[1])

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

def calculateTableData(f, g, u, x, y, cfg, dsfDeltas, measureNames, lastTime): # {{{
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
          [u-bkdelta, u+windowsize+fwdelta)
    '''

    # Read in all relevant data to one structure.
    _names = (measureSiblings(x) + measureSiblings(y)) \
        if u is None else measureNames
    _timeStart = 0 if u is None else (u - cfg.bkdelta)
    _timeFinish = (lastTime if u is None else (u + cfg.fwdelta)) + 1
    evs = rdEvs(_names, _timeStart, _timeFinish, cfg.fxbits)

    # Each row in evs is guaranteed to be of the same correct length.
    for nm,row in evs.items():
        assert nm in measureNames, (nm, measureNames)
        assert row.shape == (_timeFinish - _timeStart,), \
            (row.shape, _timeStart, _timeFinish)

    fMetric = eva.metric(f, cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    gMetric = eva.metric(g, cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits) \
        if g is not None else None


    nRows = len(measureNames) if u is None else lastTime
    nDeltas = len(dsfDeltas)
    nSibsMax = len(mapSiblingTypeToHtmlEntity.keys())
    nSibsX = len(measureSiblings(x))
    nSibsY = len(measureSiblings(y))

    xExShape = (1 if x else nRows, nSibsX if x and y else nSibsMax)
    yExShape = (1 if y else nRows, nSibsY if x and y else nSibsMax)
    fnUXYShape = (nRows, nDeltas, 2 if g else 1)

    # Each element in the tables (xEx, yEx) will contain a result:
    # calculation with a view of data [startIdx:finishIdx].
    #   Ex ( evs[X][startIdxX:finishIdxX] )
    # ... Or similar for y.
    # Each element in the table fnUXY will contain a result of:
    #   f ( evs[X][startIdxX:finishIdxX], evs[Y][startIdxY:finishIdxY] )
    # ... Or similar for g.

    # TODO: Construct tables of the start and finish EVS indexes
    # TODO: xExIdxs, yExIdxs, fnUXYIdxs
    # For xEx each cell (rowNum, colNum) needs 3 values:
    #  - X string
    #  - startIdxX integer
    #  - finishIdxX integer
    # ... And the same for yEx.
    #
    # For fnUXY each cell (rowNum, colNum) needs 6 values:
    #  - XKey::String
    #  - startIdxX::Integer
    #  - finishIdxX::Integer
    #  - YKey::String
    #  - startIdxY::Integer
    #  - finishIdxY::Integer

    mainXKeys = [[(x if x else nm) for _ in range(nDeltas)] for nm in measureNames]
    if x is None:
        assert len(measureNames) == nRows

    # TODO
    xEx = None
    yEx = None
    fnUXY = None

    return xEx, yEx, fnUXY
# }}} def calculateTableData

def tableDataRows(f, g, u, x, y, cfg, dsfDeltas, measureNames, lastTime): # {{{

    xEx, yEx, fnUXY = \
        calculateTableData(f, g, u, x, y, cfg, dsfDeltas, measureNames, lastTime)

    if gXY is not None:
        assert fXY.shape == gXY.shape, (fXY.shape, gXY.shape)

    if x and y:
        # x and y are constant, u is varying
        assert u is None, (u,)
        #     +--------+--------+--------+--------+--------+--------+--------+--------+
        #     | E[.]_x | E[¬]_x | E[↑]_x | E[↓]_x | E[.]_y | E[¬]_y | E[↑]_y | E[↓]_y |
        #     +--------+--------+--------+--------+--------+--------+--------+--------+
        #

    elif x:
        # x and u are constant, y is varying
        assert y is None, (y,)

        # 1. CASE: y has max number of siblings.
        #     +--------+--------+--------+--------+
        #     | E[.]_y | E[¬]_y | E[↑]_y | E[↓]_y |
        #     +--------+--------+--------+--------+
        #
        # 2. CASE: y has fewer siblings than max.
        #     +--------+--------+--------+--------+
        #     | E[.]_y |        |        |        |
        #     +--------+--------+--------+--------+

    elif y:
        # y and u are constant, x is varying
        assert x is None, (x,)

        # 1. CASE: x has max number of siblings.
        #     +--------+--------+--------+--------+
        #     | E[.]_x | E[¬]_x | E[↑]_x | E[↓]_x |
        #     +--------+--------+--------+--------+
        #
        # 2. CASE: x has fewer siblings than max.
        #     +--------+--------+--------+--------+
        #     | E[.]_x |        |        |        |
        #     +--------+--------+--------+--------+

    else:
        assert False

    # TODO

    def tableDataRow(row): # {{{
        ret = (
            '<tr>',
              '\n'.join(sibExTds),
              varTd,
              '\n'.join(fnTds),
            '</tr>',
        )
        return '\n'.join(ret)
    # }}} def tableDataRow

    return '\n'.join(tableDataRow(row) for row in rows)
# }}} def tableDataRows

def evaHtmlString(args, cfg, evcx, request): # {{{
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
        rowVar = 'u'

    elif isinstance(u, str) and x is None and y is None:
        # Network graph
        tableNotNetwork = False
        rowVar = None # Not a table with rows.

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and x is None and isinstance(y, str):
        # Table varying x over rows, delta over columns
        tableNotNetwork = True
        rowVar = 'x'

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and isinstance(x, str) and y is None:
        # Table varying y over rows, delta over columns
        tableNotNetwork = True
        rowVar = 'y'

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and isinstance(x, str) and isinstance(y, str):
        # Table row varying delta over columns
        tableNotNetwork = True
        rowVar = None # Only one row.

        u = int(u)
        assert 0 <= u, u

    else:
        assert False, "Invalid combination of u,x,y." \
                      " (u=%s, x=%s, y=%s)" % (u, x, y)

    vcdInfo = toml.load(eva.paths.fname_meainfo)
    measureNames = vcdInfo["unitIntervalVarNames"]
    assert vcdInfo["timechunkTimes"][0] == 0, vcdInfo
    lastTime = vcdInfo["timechunkTimes"][-1]

    # Every view varies delta - tables by horizontal, networks by edges.
    dsfDeltas = eva.cfgDsfDeltas(cfg) # [(<downsample factor>, <delta>), ...]

    body_ = []
    if tableNotNetwork:
        winStride = cfg.windowsize - cfg.windowoverlap

        body_.append(sliderControls())
        body_.append("<table>")

        # Top-most row with title (with nav popovers), and prev/next.
        body_.append(tableTitleRow(f, g, u, x, y,
                                   measureNames, dsfDeltas, winStride))

        # Column headers with delta values. Both hi and lo rows.
        body_.append(tableHeaderRows(f, g, u, x, y,
                                     dsfDeltas, rowVar))

        # TODO: Data rows.
        #body_.append(tableDataRows(f, g, u, x, y,
        #                           cfg, dsfDeltas, measureNames, lastTime))

        body_.append("</table>")
    else:
        body_.append("TODO: networkNotTable") # TODO: Holder for SVG

    # Avoid inline JS or CSS for browser caching, but use for standalone files.
    inlineHead = (args.httpd_port == 0)

    return htmlTopFmt(inlineHead, inlineHead).format('\n'.join(body_))
# }}} def evaHtmlString

class EvaHTMLException(Exception): # {{{
    pass
# }}} class EvaHTMLException

class EvaHTTPServer(HTTPServer): # {{{
    def serve_forever(self, args, cfg, evcx):
        self.RequestHandlerClass.args = args
        self.RequestHandlerClass.cfg = cfg
        self.RequestHandlerClass.evcx = evcx
        HTTPServer.serve_forever(self)
# }}} class EvaHTTPServer

class EvaHTTPRequestHandler(BaseHTTPRequestHandler): # {{{

    # These are initialized by EvaHTTPServer.serve_forever()
    args, cfg, evcx = None, None, None

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
                response = evaHtmlString(self.args, self.cfg, self.evcx,
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

def runHttpDaemon(args, cfg, evcx): # {{{
    '''Run local HTTP/HTML daemon serving data visualization pages on request.
    '''

    verb("Starting HTTPD on TCP port %d..." % args.httpd_port, end='')

    httpd = EvaHTTPServer(('', args.httpd_port), EvaHTTPRequestHandler)

    verb("Running...")

    try:
        tm_start = time.time()
        httpd.serve_forever(args, cfg, evcx)
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
        evcx = eva.loadEvcx()

        if 0 != args.httpd_port:
            runHttpDaemon(args, cfg, evcx)
        else:
            request = {'f': args.f,
                       'g': args.g,
                       'u': args.u,
                       'x': args.x,
                       'y': args.y}
            print(evaHtmlString(args, cfg, evcx, request))
    except IOError as e:
        msg = "IOError: %s: %s\n" % (e.strerror, e.filename)
        sys.stderr.write(msg)

    return 0
# }}} def evaHtml

if __name__ == "__main__":
    assert False, "Not a standalone script."
