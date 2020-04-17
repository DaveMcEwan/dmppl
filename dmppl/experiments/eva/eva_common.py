
# -*- coding: utf8 -*-

# Standard library imports
from functools import partial
import inspect
import os
import struct
import sys

# PyPI library imports
import toml

# Local library imports
from dmppl.base import dbg, verb, Bunch, Fragile, \
    fnameAppendExt, joinP, mkDirP, utf8NameToHtml
from dmppl.fx import *
from dmppl.math import powsineCoeffs, isEven
from dmppl.nd import *
from dmppl.vcd import VcdReader, detypeVarName

__version__ = "0.1.0"

# Don't write .pyc or .pyo files unless it's a release.
# This doesn't affect eva_common.
if int(__version__.split('.')[-1]) != 0:
    sys.dont_write_bytecode = True

appPaths = Bunch()
paths = Bunch()

def initPaths(argsEvcPath): # {{{
    '''Populate some convenient variables from args.
    '''

    #module = inspect.stack()[-1][1]
    appPaths.basemodule = os.path.basename(os.path.realpath(__file__))
    appPaths.directory = os.path.dirname(os.path.realpath(__file__))
    appPaths.share = joinP(appPaths.directory, "share")
    appPaths.configDefault = joinP(appPaths.share, "configDefault.toml")

    paths.fname_evc = fnameAppendExt(argsEvcPath, "evc")

    outdir = os.path.splitext(paths.fname_evc)[0] + ".eva"

    paths.outdir = outdir
    paths.fname_evcx = joinP(outdir, "evcx.toml")
    paths.fname_cfg = joinP(outdir, "config.toml")
    paths.fname_cln = joinP(outdir, "clean.vcd")
    paths.fname_mea = joinP(outdir, "measure.vcd")
    paths.fname_meainfo = joinP(outdir, "measure.info.toml")
    paths.dname_mea = joinP(outdir, "measure")
    paths.dname_identicon = joinP(outdir, "identicon")

    paths._INITIALIZED = True

    return
# }}} def initPaths

def loadCfg(): # {{{
    '''Return config extracted from EVC and VCD.

    CFG is assumed to be sane, written by initCfg().
    '''
    assert paths._INITIALIZED

    verb("Loading CFG... ", end='')

    cfg = Bunch()
    cfg.__dict__.update(toml.load(paths.fname_cfg))

    verb("Done")

    return cfg
# }}} def loadCfg

def loadEvcx(): # {{{
    '''Return dict of measurement names to VCD hook names.
    '''
    assert paths._INITIALIZED

    verb("Loading EVCX... ", end='')

    evcx = toml.load(paths.fname_evcx)

    verb("Done")

    return evcx
# }}} def loadEvcx

metricNames = [
    "Cex",
    "Cls",
    "Cos",
    "Cov",
    "Dep",
    "Ham",
    "Tmt",
]

def metric(name, winSize, winAlpha, nBits=0): # {{{
    '''Take attributes of a metric, return a callable implementation.

    E.g. Use like: metric("foo")(x, y)

    NOTE: Ex isn't really a metric but it's a convenient place to choose between
    implementations by nBits.
    '''
    if name is None:
        return None

    w = powsineCoeffs(winSize, winAlpha)

    assert 0 == nBits, "TODO: Implement fx*()"
    assert name in metricNames or name in ["Ex"], name
    fs = {
        "Ex":  partial(fxEx  if 0 < nBits else ndEx,  w, nBits=nBits),
        "Cex": partial(fxCex if 0 < nBits else ndCex, w, nBits=nBits),
        "Cls": partial(fxCls if 0 < nBits else ndCls, w, nBits=nBits),
        "Cos": partial(fxCos if 0 < nBits else ndCos, w, nBits=nBits),
        "Cov": partial(fxCov if 0 < nBits else ndCov, w, nBits=nBits),
        "Dep": partial(fxDep if 0 < nBits else ndDep, w, nBits=nBits),
        "Ham": partial(fxHam if 0 < nBits else ndHam, w, nBits=nBits),
        "Tmt": partial(fxTmt if 0 < nBits else ndTmt, w, nBits=nBits),
    }

    return fs[name]
# }}} def metric

mapMetricNameToHtml = {
    "Ex":   utf8NameToHtml("MATHEMATICAL DOUBLE-STRUCK CAPITAL E"), # E[x]
    "Cex":  utf8NameToHtml("MATHEMATICAL DOUBLE-STRUCK CAPITAL E"), # E[x|y]
    "Cls":  'C' + utf8NameToHtml("COMBINING DOT ABOVE") + 'ls',
    "Cos":  'C' + utf8NameToHtml("COMBINING DOT ABOVE") + 'os',
    "Cov":  'C' + utf8NameToHtml("COMBINING DOT ABOVE") + 'ov',
    "Dep":  'D' + utf8NameToHtml("COMBINING DOT ABOVE") + 'ep',
    "Ham":  'H' + utf8NameToHtml("COMBINING DOT ABOVE") + 'am',
    "Tmt":  'T' + utf8NameToHtml("COMBINING DOT ABOVE") + 'mt',
}

def dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor): # {{{
    '''Return a list of downsample factors and deltas (timeshifts).

    [ (<downsample factor>, <delta>), ... ]

    The downsample factor may of course be ignored, but provides a method of
    "zooming out" from a plot when there are many deltas to calculate.
    This does not choose a method of performing the downsampling.
    reqZoomFactor < 2 ==> zoomFactor = max(nDeltasBk, nDeltasFw)
    '''
    assert isinstance(winSize, int), type(winSize)
    assert 1 <= winSize, winSize
    assert isinstance(reqNDeltasBk, int), type(reqNDeltasBk)
    assert 0 <= reqNDeltasBk, reqNDeltasBk # Non-negative
    assert isinstance(reqNDeltasFw, int), type(reqNDeltasFw)
    assert 1 <= reqNDeltasFw, reqNDeltasFw # Positive
    assert isinstance(reqZoomFactor, int), type(reqZoomFactor)
    assert 0 <= reqZoomFactor, reqZoomFactor

    nDeltasBk = min(reqNDeltasBk, winSize // 2)
    nDeltasFw = min(reqNDeltasFw, winSize // 2)
    zoomFactor = reqZoomFactor if 1 < reqZoomFactor \
                               else max(nDeltasBk, nDeltasFw)

    # All feasible downsample factors with associated upper absdeltas.
    # 64 scaling factors is always more than enough in practice.
    # Just 32 should really be enough; 1 in 4 billion samples.
    # NOTE: 0th element is a dummy for most of these calculations which is
    # discarded.
    log2_dsf = range(64+2) # +2 <- discard 0th, range last element +1.

    # Upper delta for each downsample factor, plus 1.
    _d_hi = [sum([zoomFactor * 2**f for f in range(l2f)]) for l2f in log2_dsf]
    _d_hi_bk = [hi for hi in _d_hi if hi < nDeltasBk]
    _d_hi_fw = [hi for hi in _d_hi if hi < nDeltasFw]
    d_hi_bk = _d_hi_bk + [ min(nDeltasBk, _d_hi[len(_d_hi_bk)]) ]
    d_hi_fw = _d_hi_fw + [ min(nDeltasFw, _d_hi[len(_d_hi_fw)]) ]

    # Actual downsample factors used.
    n_dsf_bk = len(d_hi_bk)
    dsf_bk = [2**(l2f - 1) for l2f in log2_dsf[:n_dsf_bk]]
    n_dsf_fw = len(d_hi_fw)
    dsf_fw = [2**(l2f - 1) for l2f in log2_dsf[:n_dsf_fw]]

    # Lower delta for each downsample factor.
    d_lo_bk = [d_hi_bk[i-1] for i in range(n_dsf_bk)]
    assert 0 < n_dsf_bk == len(dsf_bk) == len(d_hi_bk) == len(d_lo_bk)
    d_lo_fw = [d_hi_fw[i-1] for i in range(n_dsf_fw)]
    assert 0 < n_dsf_fw == len(dsf_fw) == len(d_hi_fw) == len(d_lo_fw)

    # Actual deltas in list with format (<downsample factor>, <real delta>)
    pos_d = [(dsf_fw[i], d) \
             for i in range(1, n_dsf_fw) \
             for d in range(d_lo_fw[i], d_hi_fw[i], dsf_fw[i])]
    neg_d = [(dsf_bk[i], d) \
             for i in range(1, n_dsf_bk) \
             for d in range(-d_hi_bk[i], -d_lo_bk[i], dsf_bk[i])]
    ret = sorted(neg_d + pos_d)

    assert ret[0][0] == 1 # Unscaled deltas first.

    #nDeltas = len(ret)
    #delta0Idx = ret.index((1,0))
    if 0 == reqZoomFactor:
        assert nDeltasBk == len([d for dsf,d in ret if d < 0])
        assert nDeltasFw == len([d for dsf,d in ret if 0 <= d])

    return ret
# }}} def dsfDeltas

def cfgDsfDeltas(cfg): # {{{
    return dsfDeltas(cfg.windowsize, cfg.deltabk, cfg.deltafw, cfg.deltazoom)
# }}} def cfgDsfDeltas

def meaDtype(name): # {{{
    # [(t,v), ...] OR [t, ...]
    # timestamp: Big-endian, unsigned long (32b)

    hasValues = name.startswith("normal.")

    # Type corresponds to bit/real in measure.vcd.
    # NOTE: int is required instead of bool as newValue is given from VcdReader
    # as a string.
    # int("0") --> 0, bool(0) -- False, bool("0") --> True
    tp = float if hasValues else int

    strideBytes = 8 if hasValues else 4
    structFmt = ">Lf" if hasValues else ">L" # [(t,v), ...] OR [t, ...]

    return tp, strideBytes, structFmt
# }}} def meaDtype

def isUnitIntervalMeasure(name): # {{{
    '''All VCD::bit signals in measure.vcd are usable, but of the VCD::real
       signals, only normal.measure.* are usable.

    Other VCD::real signals are not guaranteed to be in [0, 1].
    '''
    unitEventSiblings = ("measure",)
    unitBstateSiblings = ("measure", "reflection", "rise", "fall",)
    unitThresholdSiblings = ("measure", "reflection", "rise", "fall",)
    unitNormalSiblings = ("measure",)

    measureType, siblingType, baseName = measureNameParts(name)

    ret = \
        ("event" == measureType and siblingType in unitEventSiblings) or \
        ("bstate" == measureType and siblingType in unitBstateSiblings) or \
        ("threshold" == measureType and siblingType in unitThresholdSiblings) or \
        ("normal" == measureType and siblingType in unitNormalSiblings)

    return ret
# }}} def isUnitIntervalMeasure

def meaDbFromVcd(): # {{{
    '''Apply post-processing steps to stage0.

    Extract changes from measure.vcd into fast-to-read binary form.

    measure.vcd has only 2 datatypes: bit, real

    Assume initial state for all measurements is 0.:
    All timestamps are 32b non-negative integers.
    Binary format for bit is different from that of real.
        bit: Ordered sequence of timestamps.
        real: Ordered sequence of (timestamp, value) pairs.
            All values are 32b IEEE754 floats, OR 32b(zext) fx.
    '''
    verb("Creating binary database from VCD... ", end='')

    mkDirP(paths.dname_mea)

    with VcdReader(paths.fname_mea) as vcdi:

        # Stage0 file has bijective map between varId and varName by
        # construction, so take first (only) name for convenience.
        _mapVarIdToName = {varId: detypeVarName(nms[0]) \
                           for varId,nms in vcdi.mapVarIdToNames.items()}
        mapVarIdToName = {varId: nm \
                          for varId,nm in _mapVarIdToName.items() \
                          if isUnitIntervalMeasure(nm)}

        fds = {nm: open(joinP(paths.dname_mea, nm), 'wb') \
             for varId,nm in mapVarIdToName.items()}

        prevValues = {varId: 0 for varId in mapVarIdToName.keys()}

        for newTime, changedVarIds, newValues in vcdi.timechunks:
            for varId,newValue in zip(changedVarIds, newValues):
                nm = mapVarIdToName.get(varId, None)
                if nm is None:
                    continue

                tp, _, structFmt = meaDtype(nm)
                v, p = tp(newValue), prevValues[varId]

                if v != p:
                    _packArgs = [newTime, v] if tp is float else [newTime]
                    bs = struct.pack(structFmt, *_packArgs)
                    fds[nm].write(bs)
                    prevValues[varId] = v

        for _,fd in fds.items():
            fd.close()

    verb("Done")

    return
# }}} def meaDbFromVcd

def meaSearch(name, targetTime, precNotSucc=True): # {{{
    '''Return offset of nearest timestamp.

    Offset is number of timestamps, not number of bytes.
    Search forward in exponential steps, then bisect when overstepped.

    Return offset of nearest previous/next depending on precNotSucc when an
    exact match isn't found.

    None    <-- Request succeeding timestamp after EOF
    -1      <-- Request preceeding timestamp before first
    '''

    assert isinstance(name, str), type(name)
    assert isinstance(targetTime, int), type(targetTime)
    #assert 0 <= targetTime, targetTime # Allow negative times.
    assert isinstance(precNotSucc, bool)

    _, strideBytes, structFmt = meaDtype(name)

    stepSize_ = 1
    stepDir_ = 1

    # Sticky flag tracks search phase.
    # Search forward in exponential steps, then bisect when overstepped.
    bisect_ = False

    t_, offset_ = None, -1

    with open(joinP(paths.dname_mea, name), 'rb') as fd:
        while True:
            # Offset *before* reading timestamp.
            offset_ = fd.tell() // strideBytes

            # Read timestamp.
            bs = fd.read(strideBytes)
            if len(bs) != strideBytes:
                t_ = None # Tried reading past EOF
            else:
                t_ = struct.unpack(structFmt, bs)[0]

            assert t_ is None or (0 <= t_), t_

            if t_ is None or t_ > targetTime:
                # Overstepped, continue search backwards.
                stepDir_ = -1
                bisect_ = True
            elif t_ < targetTime:
                # Understepped, continue search forwards.
                stepDir_ = 1
            else:
                assert t_ == targetTime
                break # Exact match

            stepSize_ = (stepSize_ // 2) if bisect_ else (stepSize_ * 2)

            if 0 == stepSize_:
                # No exact match exists
                break

            nextOffset = offset_ + stepSize_ * stepDir_
            fd.seek(nextOffset * strideBytes)

    # t_ is now the "closest" possible.
    if t_ is None: # EOF
        # EOF, return last/maximum offset which must preceed targetTime or
        # None if no successor is possible.
        ret = (offset_ - 1) if precNotSucc else None
    else:
        assert isinstance(t_, int)
        assert 0 <= t_
        if t_ == targetTime:
            # Simple case, exact match.
            ret = offset_
        elif t_ < targetTime:
            ret = offset_ if precNotSucc else None
        else: # t_ > targetTime:
            ret = (offset_ - 1) if precNotSucc else offset_

    # Offset of -1 when targetTime is less than the first
    # timestamp and precNotSucc is True.
    assert ret is None or (isinstance(ret, int) and -1 <= ret), ret

    ## Self-test to ensure that when ret is not None or -1, then it can be used
    ## to seek.
    #if isinstance(ret, int) and 0 <= ret:
    #    with open(joinP(paths.dname_mea, name), 'rb') as fd:
    #        fd.seek(ret)
    #        assert len(fd.read(strideBytes)) == strideBytes

    return ret
# }}} def meaSearch

def rdEvs(names, startTime, finishTime, fxbits=0): # {{{
    '''Read EVent Samples (sanitized data written by evaInit to
       foo.eva/measure/*) in [startTime, finishTime), and return as ndarrays.
    '''
    names = set(names)
    assert paths._INITIALIZED

    assert isinstance(startTime, int), type(startTime)
    assert isinstance(finishTime, int), type(finishTime)
    assert startTime < finishTime, (startTime, finishTime)
    #assert 0 <= startTime, startTime # Effectively zext with -ve startTime.
    assert 1 <= finishTime, finishTime
    sIdx, fIdx = 0, finishTime - startTime

    bNames, rNames = \
        [nm for nm in names if not nm.startswith("normal.")], \
        [nm for nm in names if nm.startswith("normal.")]

    bStartOffsets, rStartOffsets = \
        (meaSearch(nm, startTime) for nm in bNames), \
        (meaSearch(nm, startTime) for nm in rNames)

    # Axis0 corresponds to order of names.
    bShape, rShape = \
        (len(bNames), fIdx), \
        (len(rNames), fIdx)

    bDtype, rDtype = \
        np.bool, \
        np.float32 if fxbits == 0 else fxDtype(fxbits)

    # Fully allocate memory before any filling to ensure there is enough.
    bEvs, rEvs = \
        np.zeros(bShape, dtype=bDtype), \
        np.zeros(rShape, dtype=rDtype)

    bStructFmt, rStructFmt = \
        ">L", \
        ">Lf" if fxbits == 0 else ">LL"

    bStrideBytes, rStrideBytes = 4, 8

    # Fill by infer/copy bit values from measure.vcd to ndarray.
    for i,(nm,startOffset) in enumerate(zip(bNames, bStartOffsets)): # {{{
        prevIdx, prevValue = 0, False

        with Fragile(open(joinP(paths.dname_mea, nm), 'rb')) as fd:
            o_ = max(0, startOffset)
            fd.seek(o_ * bStrideBytes)

            bs = fd.read(bStrideBytes) # Read first timestamp.
            if len(bs) != bStrideBytes:
                raise Fragile.Break # Tried reading past EOF
            t,v = struct.unpack(bStructFmt, bs)[0], isEven(o_)
            tIdx = t - startTime
            o_ += 1

            while tIdx < fIdx:
                if prevValue: # Initialised to 0, only update bool if necessary.
                    bEvs[i][prevIdx:tIdx] = prevValue
                prevIdx, prevValue = tIdx, v

                bs = fd.read(bStrideBytes) # Read timestamp.
                if len(bs) != bStrideBytes:
                    raise Fragile.Break # Tried reading past EOF
                t,v = struct.unpack(bStructFmt, bs)[0], isEven(o_)
                tIdx = t - startTime
                o_ += 1

        if prevValue: # Initialised to 0, only update bool if necessary.
            bEvs[i][prevIdx:] = prevValue
    # }}} infer/copy/fill bEvs

    # Fill by infer/copy real values from measure.vcd to ndarray.
    for i,(nm,startOffset) in enumerate(zip(rNames, rStartOffsets)): # {{{
        prevIdx, prevValue = 0, 0.0

        with Fragile(open(joinP(paths.dname_mea, nm), 'rb')) as fd:
            o_ = max(0, startOffset)
            fd.seek(o_ * rStrideBytes)

            bs = fd.read(rStrideBytes) # Read first timestamp.
            if len(bs) != rStrideBytes:
                raise Fragile.Break # Tried reading past EOF
            t,v = struct.unpack(rStructFmt, bs)
            tIdx = t - startTime
            o_ += 1

            while tIdx < fIdx:
                rEvs[i][prevIdx:tIdx] = prevValue \
                    if fxbits == 0 else fxFromFloat(prevValue, nBits=fxbits)
                prevIdx, prevValue = tIdx, v

                bs = fd.read(rStrideBytes) # Read timestamp.
                if len(bs) != rStrideBytes:
                    raise Fragile.Break # Tried reading past EOF
                t,v = struct.unpack(rStructFmt, bs)
                tIdx = t - startTime
                o_ += 1

        rEvs[i][prevIdx:] = prevValue \
            if fxbits == 0 else fxFromFloat(prevValue, nBits=fxbits)
    # }}} infer/copy/fill rEvs

    mapNameToDatarow = {nm: (bEvs if bNotR else rEvs)[i]
                        for bNotR,i,nm in \
                         ([(True,  i, nm) for i, nm in enumerate(bNames)] + \
                          [(False, i, nm) for i, nm in enumerate(rNames)])}

    assert len(names) == len(mapNameToDatarow.keys()), \
        (len(names), len(mapNameToDatarow.keys()))
    assert sorted(list(names)) == sorted(list(mapNameToDatarow.keys())), \
        (names, mapNameToDatarow.keys())

    expectedLen = finishTime - startTime
    for nm,row in mapNameToDatarow.items():
        assert 1 == len(row.shape), (nm, row.shape)
        assert expectedLen == row.shape[0], (nm, expectedLen, row.shape)

    return mapNameToDatarow
# }}} def rdEvs

mapSiblingTypeToHtml = {
    "measure":      utf8NameToHtml("MIDDLE DOT"),
    "reflection":   utf8NameToHtml("NOT SIGN"),
    "rise":         utf8NameToHtml("UPWARDS ARROW"),
    "fall":         utf8NameToHtml("DOWNWARDS ARROW"),
}
nSibsMax = len(mapSiblingTypeToHtml.keys())

mapMeasureTypeToSiblingTypes = {
    "event":     ("measure",),
    "bstate":    ("measure", "reflection", "rise", "fall",),
    "threshold": ("measure", "reflection", "rise", "fall",),
    "normal":    ("measure",),
}

def measureNameParts(nm): # {{{
    '''Take a measurement name and return the measure type and sibling type.

    E.g: "bstate.reflection.foo" -> ("bstate", "reflection", "foo")
    E.g: "event.measure.foo.bar" -> ("event", "measure", "foo.bar")
    '''

    nmParts = nm.split('.')
    assert 3 <= len(nmParts), nmParts

    (measureType, siblingType), baseNameParts = nmParts[:2], nmParts[2:]

    assert measureType in mapMeasureTypeToSiblingTypes.keys(), nm

    if "normal" == measureType:
        assert siblingType in ("raw", "smooth", "measure"), nm
    else:
        assert siblingType in mapMeasureTypeToSiblingTypes[measureType], nm

    baseName = '.'.join(baseNameParts)

    return measureType, siblingType, baseName
# }}} def measureNameParts

def measureSiblings(nm): # {{{
    '''Take a measurement name and return a tuple of sibling/related
       measurements which can be used with eva metrics.

    E.g: "bstate.reflection.foo" -> ("bstate.fall.foo",
                                     "bstate.measure.foo",
                                     "bstate.reflection.foo",
                                     "bstate.rise.foo")

    E.g: "event.measure.foo" -> ("event.measure.foo",)
    '''

    measureType, siblingType, baseName = measureNameParts(nm)

    siblings = tuple('.'.join([measureType, s, baseName]) \
                     for s in mapMeasureTypeToSiblingTypes[measureType])

    return siblings
# }}} def measureSiblings

def winStartTimes(startTime, finishTime, winSize, winOverlap): # {{{
    return list(range(startTime, finishTime, winSize - winOverlap))
# }}} def winStartTimes

def timeToEvsIdx(t, evsStartTime): # {{{
    '''
    Time:
        u-#δ_bk      u                 u+winSize    u+#δfw
    <-- ...|---------|---------------------|-----------|... -->

           |< #δ_bk >|<      winSize      >|<   #δfw  >|

       evsStartTime                               evsFinishTime

    EVS index:
           0        #δ_bk            #δ_bk+winSize
           |---------|---------------------|-----------|
    '''
    return t - evsStartTime
# }}} def timeToEvsIdx

def evaLink(f, g, u, x, y, txt, escapeQuotes=False): # {{{
    '''Return the link to a data view.
    '''
    assert f is None or isinstance(f, str), type(f)
    assert g is None or isinstance(g, str), type(g)
    if f is not None:
        assert f in metricNames, f
    if g is not None:
        assert g in metricNames, g
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

