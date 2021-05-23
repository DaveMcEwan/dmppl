
# -*- coding: utf8 -*-

# Standard library imports
from itertools import product

# PyPI library imports
import numpy as np

# Local library imports
from dmppl.math import l2Norm
from dmppl.base import dbg, info, verb, joinP, rdTxt, utf8NameToHtml
from dmppl.color import rgb1D, rgb2D

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
from dmppl.experiments.eva.eva_common import \
    paths, \
    measureNameParts, measureSiblings, nSibsMax, mapSiblingTypeToHtml, \
    metricNames, metric, mapMetricNameToHtml, evaLink, \
    winStartTimes, rdEvs, timeToEvsIdx


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

def fnDisplay(a, b): # {{{
    assert a is None or isinstance(a, str), type(a)
    assert b is None or isinstance(b, str), type(b)
    assert a or b, (a, b)
    if a is not None:
        assert a in metricNames, a
    if b is not None:
        assert b in metricNames, b

    aHtml = mapMetricNameToHtml[a] if a else None
    bHtml = mapMetricNameToHtml[b] if b else None

    ret = ("{%s,%s}" % (aHtml, bHtml)) \
        if a and b else \
        (aHtml if a else bHtml)

    return ret
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

def evaTitleFmt(fnIsEx): # {{{
    ob, sep, cb = ('[', '|', ']') if fnIsEx else ('(', ',', ')')

    ret = ''.join((
        "{fn}",
        ob,
        "x={x} ",
        sep,
        " y={y}<sub>",
        utf8NameToHtml("MATHEMATICAL LEFT ANGLE BRACKET"),
        utf8NameToHtml("GREEK SMALL LETTER DELTA"),
        utf8NameToHtml("MATHEMATICAL RIGHT ANGLE BRACKET"),
        "</sub> ; u={u}",
        cb,
    ))

    return ret
# }}} def evaTitleFmt

def evaTitleText(a, b, u, x, y): # {{{
    '''Return the title of a data view as a simple string without nested markup.
    '''
    # NOTE: Assertions handled in *Display().
    fnIsEx = ("Cex" in (a, b)) and (None in (a, b)) # One is Cex, other is None.
    return evaTitleFmt(fnIsEx).format(
        fn=fnDisplay(a, b),
        x=xDisplay(x),
        y=yDisplay(y),
        u=uDisplay(u),
    )
# }}} def evaTitleText

def evaTitleAny(fn, u, x, y, fnIsEx): # {{{
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

    return evaTitleFmt(fnIsEx).format(fn=fn, x=x, y=y, u=u)
# }}} def evaTitleAny

def tableTitleRow(a, b, u, x, y, cfg, dsfDeltas, vcdInfo): # {{{
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
            evaLink(a, b, u - winStride, x, y, "prev"),
            evaLink(a, b, u + winStride, x, y, "next"),
            '</th>',
        ))

    # NOTE: a and b must be valid strings containing name of measurement.
    if a and b:
        fnLinks = [evaLink(aNm, bNm, u, x, y,
                           evaTitleText(aNm, bNm, u, x, y),
                           escapeQuotes=True) \
                   for aNm in metricNames \
                   for bNm in metricNames \
                   if aNm != a and bNm != b and aNm != bNm]
    elif a:
        fnLinks = [evaLink(aNm, None, u, x, y,
                           evaTitleText(aNm, None, u, x, y),
                           escapeQuotes=True) \
                   for aNm in metricNames \
                   if aNm != a]
    elif b:
        fnLinks = [evaLink(None, bNm, u, x, y,
                           evaTitleText(None, bNm, u, x, y),
                           escapeQuotes=True) \
                   for bNm in metricNames \
                   if bNm != b]
    else:
        assert False # Checking already performed in evaHtmlString()
    fnPopover = popoverUl(fnDisplay(a, b), fnLinks)

    xLinks = [evaLink(a, b, u, xNm, y,
                      evaTitleText(a, b, u, xNm, y),
                      escapeQuotes=True) \
              for xNm in measureNames \
              if xNm != x]
    xPopover = popoverUl(xDisplay(x), xLinks)

    yLinks = [evaLink(a, b, u, x, yNm,
                      evaTitleText(a, b, u, x, yNm),
                      escapeQuotes=True) \
              for yNm in measureNames \
              if yNm != y]
    yPopover = popoverUl(yDisplay(y), yLinks)


    fnIsEx = ("Cex" in (a, b)) and (None in (a, b)) # One is Cex, other is None.

    ret = (
        '<tr>',
        '  <th class="tabletitle" colspan="%d">' % colspanTitle,
        evaTitleAny(fnPopover, uDisplay(u), xPopover, yPopover, fnIsEx),
        '  </th>',
        navPrevNext,
        '</tr>',
    )
    return ''.join(r.strip() for r in ret)
# }}} def tableTitleRow

def tableHeaderRows(a, b, u, x, y, dsfDeltas, exSibRow): # {{{
    '''Return a string with HTML one or more <tr>.
    '''
    sibThTxtFmt = mapMetricNameToHtml["Ex"] + "[%s]<sub>%s</sub>" # symbol, x/y

    def sibHiThs(nm, xNotY, rowspan, values=None): # {{{

        measureType, siblingType, baseName = measureNameParts(nm)

        siblings = \
            [measureNameParts(s) \
             for s in measureSiblings(nm)]

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
            ['title="%0.05f"' % v \
             for v in values] if values is not None else \
            ['' for _ in siblings]

        sibAttrs = [' '.join(attrs) for attrs in zip(attrClasses,
                                                     attrRowspans,
                                                     attrStyles,
                                                     attrTitles)]
        sibLinkTxts = \
            [sibThTxtFmt % (mapSiblingTypeToHtml[st],
                            'x' if xNotY else 'y') \
             for mt,st,mn in siblings]

        sibLinks = \
            [evaLink(a, b, u, snm, y, txt) if xNotY else \
             evaLink(a, b, u, x, snm, txt) \
             for snm,txt in zip(sibNames, sibLinkTxts)]

        sibValueTxts = \
            ['<br/> %0.02f' % v for v in values] \
            if values is not None else \
            ['' for _ in siblings]


        padThs = ['<th></th>' \
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
            [sibThTxtFmt % (mapSiblingTypeToHtml[st],
                            'x' if xNotY else 'y') \
             for st in mapSiblingTypeToHtml.keys()]

        classes = ("xsib" if xNotY else "ysib",)

        attrClasses = \
            ['class="%s"' % ' '.join(c for c in classes)
             for _ in mapSiblingTypeToHtml.keys()]

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
    deltaThs = ('<th>%d</th>' % d for dsf,d in dsfDeltas)

    ret = (
        '<tr class="th_hi">',
          '\n'.join(hiSibThs),
          ' <th class="varying" rowspan="2">%s</th>' % rowVar,
          ' <th colspan="%d"></th>' % nLeftDeltas,
          ' <th>' + utf8NameToHtml("GREEK SMALL LETTER DELTA") + '</th>',
          ' <th colspan="%d"></th>' % nRightDeltas,
        '</tr>',
        '<tr class="th_lo">',
          '\n'.join(loSibThs),
          # varying spans both rows
          ''.join(deltaThs),
        '</tr>',
    )
    return '\n'.join(r.strip() for r in ret)
# }}} def tableHeaderRows

def calculateTableData(a, b, u, x, y, cfg, dsfDeltas, vcdInfo): # {{{
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

    winUs = winStartTimes(firstTime, lastTime,
                          cfg.windowsize, cfg.windowoverlap) \
                if u is None else None

    evsStartTime = (firstTime if u is None else u) - cfg.deltabk
    evsFinishTime = ((max(winUs[-1], firstTime) + cfg.windowsize) \
                      if u is None else \
                      u + cfg.windowsize) + cfg.deltafw + 1

    # Read in all relevant data to one structure.
    evsNames = (measureSiblings(x) + measureSiblings(y)) \
        if u is None else measureNames
    evs = rdEvs(evsNames, evsStartTime, evsFinishTime, cfg.fxbits)

    evsExpectedLen = evsFinishTime - evsStartTime # debug only
    for nm,row in evs.items():
        assert 1 == len(row.shape), (nm, row.shape)
        assert evsExpectedLen == row.shape[0], (nm, evsExpectedLen, row.shape)

    # Each row in evs is guaranteed to be of the same correct length.
    for nm,row in evs.items():
        assert nm in measureNames, (nm, measureNames)
        assert row.shape == (evsFinishTime - evsStartTime,), \
            (row.shape, evsStartTime, evsFinishTime)

    aMetric, bMetric = \
        metric(a, cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits), \
        metric(b, cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)
    fns = (aMetric, bMetric) if b else (aMetric,)
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
        startIdxX = timeToEvsIdx(winUs[rowNum] if u is None else u,
                                     evsStartTime)
        startIdxY = startIdxX + delta
        finishIdxX, finishIdxY = \
            (startIdxX + cfg.windowsize), \
            (startIdxY + cfg.windowsize)

        _idxs = (startIdxX, startIdxY, finishIdxX, finishIdxY)
        assert all(isinstance(i, int) for i in _idxs), \
            tuple(type(i) for i in _idxs)
        assert 0 <= startIdxX < finishIdxX < evsExpectedLen, \
            (startIdxX, finishIdxX, evsExpectedLen)
        assert 0 <= startIdxY < finishIdxY < evsExpectedLen, \
            (startIdxY, finishIdxY, evsExpectedLen)
        assert cfg.windowsize == (finishIdxX - startIdxX), \
            (cfg.windowsize, startIdxX, finishIdxX)
        assert cfg.windowsize == (finishIdxY - startIdxY), \
            (cfg.windowsize, startIdxY, finishIdxY)

        evsX, evsY = \
            evs[keyX][startIdxX:finishIdxX], \
            evs[keyY][startIdxY:finishIdxY]
        assert 1 == len(evsX.shape) == len(evsY.shape), \
            (evsX.shape, evsY.shape)
        assert evsX.shape == evsY.shape, (evsX.shape, evsY.shape, startIdxX, finishIdxX)

        fnUXY[fnNum][rowNum][colNum] = fns[fnNum](evsX, evsY)

    expectation = metric("Ex", cfg.windowsize, cfg.windowalpha, nBits=cfg.fxbits)

    def sibEx(s): # {{{
        '''Allocate then fill a sibling expectation array.

        s must be either x or y
        '''
        assert s in [x, y], (s, x, y)

        siblings = measureSiblings(s) if s else None

        nRowsEx = 1 if s and not (x and y) else nRows
        nColsEx = len(siblings) if s else nSibsMax

        arr = np.empty((nRowsEx, nColsEx), dtype=dtype)
        sibExIter = product(range(nRowsEx), range(nColsEx))

        for rowNum,colNum in sibExIter:

            if s:
                key = siblings[colNum]
            else:
                rowSiblings = measureSiblings(measureNames[rowNum])

                # Measures have different numbers of siblings.
                if colNum < len(rowSiblings):
                    key = rowSiblings[colNum]
                else:
                    # NOTE: The uninitialized value should never be used.
                    continue

            startIdx = timeToEvsIdx(winUs[rowNum] if u is None else u,
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
        assert xEx.shape == (nRows, len(measureSiblings(x))), xEx.shape
        assert yEx.shape == (nRows, len(measureSiblings(y))), yEx.shape
    elif x:
        assert xEx.shape == (1, len(measureSiblings(x))), xEx.shape
        assert yEx.shape == (nRows, nSibsMax), yEx.shape
    elif y:
        assert xEx.shape == (nRows, nSibsMax), xEx.shape
        assert yEx.shape == (1, len(measureSiblings(y))), yEx.shape
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
        ('title="%0.05f,%0.05f"' % (fValue, gValue)) \
        if is2D else \
        ('title="%0.05f"' % (fValue))

    # NOTE: L2norm is just for the slider controls which require a scalar.
    attrValue = \
        ('value="%0.05f"' % l2Norm(fValue, gValue)) \
        if is2D else \
        ('value="%0.05f"' % (fValue))

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
    attrTitle = 'title="%0.05f"' % value
    attrValue = 'value="%0.05f"' % value
    attrs = ' '.join((attrClass, attrStyle, attrTitle, attrValue))

    txt = '%0.02f' % value

    return fmt % (attrs, txt)
# }}} def tdCellExSib

def measureCompactHtml(name): # {{{
    '''Return a compact representation of a measure name.

    Identicon and symbol on colored background.
    '''
    spanFmt = '<span class="compact %s">%s%s</span>'

    mt, st, bn = measureNameParts(name)
    icon = rdTxt(joinP(paths.dname_identicon, bn + ".svg"))

    return spanFmt % (mt, icon, mapSiblingTypeToHtml[st])
# }}} def measureCompactHtml

def tableDataRows(a, b, u, x, y, cfg, vcdInfo, exSib, varCol, fnUXY): # {{{
    measureNames = vcdInfo["unitIntervalVarNames"]

    if x and y:
      assert exSib.shape[1] <= 2*nSibsMax, \
          (exSib.shape, mapSiblingTypeToHtml)
    else:
      assert exSib.shape[1] <= nSibsMax, \
          (exSib.shape, mapSiblingTypeToHtml)

    assert fnUXY.shape[0] in [1, 2], \
        fnUXY.shape

    assert exSib.shape[0] == len(varCol) == fnUXY.shape[1], \
        (exSib.shape, len(varCol), fnUXY.shape)
    nRows = exSib.shape[0]

    def varColTds(values, timesNotNames): # {{{

        if timesNotNames:
            ret = ['<td class="varying"> %s </td>' % str(v+cfg.timestart) \
                   for v in values]
        else: # Represent measureType.siblingType compactly.
            texts = [bn if "orig" == st else '' \
                     for mt,st,bn in [measureNameParts(v) \
                                      for v in values]]
            compacts = [measureCompactHtml(v) for v in values]

            ret = ['<td class="varying"> %s %s </td>' % (c, t) \
                   for c,t in zip(compacts, texts)]

        return ret
    # }}} def varColTds

    varTds = varColTds(varCol, (u is None))

    def tableDataRow(rowNum): # {{{
        rowNSibs = 2*nSibsMax \
                   if x and y else \
                   len(measureSiblings(measureNames[rowNum]))

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

def htmlTable(a, b, u, x, y,
              cfg, dsfDeltas, vcdInfo,
              exSibRow, exSib, varCol, fnUXY): # {{{
    ret_ = []
    ret_.append(sliderControls())
    ret_.append('<table>')

    # Top-most row with title (with nav popovers), and prev/next.
    ret_.append(tableTitleRow(a, b, u, x, y,
                              cfg, dsfDeltas, vcdInfo))

    # Column headers with delta values. Both hi and lo rows.
    ret_.append(tableHeaderRows(a, b, u, x, y,
                                dsfDeltas,
                                exSibRow))

    # Main data rows.
    ret_.append(tableDataRows(a, b, u, x, y,
                              cfg, vcdInfo,
                              exSib, varCol, fnUXY))

    ret_.append('</table>')

    return ret_
# }}} def htmlTable

if __name__ == "__main__":
    assert False, "Not a standalone script."
