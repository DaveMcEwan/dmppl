
# Standard library imports
from functools import partial
import inspect
import os
import struct

# PyPI library imports
import toml

# Local library imports
from dmppl.base import dbg, verb, Bunch, fnameAppendExt, joinP
from dmppl.fx import *
from dmppl.math import powsineCoeffs
from dmppl.nd import *

__version__ = "0.1.0"

# Don't write .pyc or .pyo files unless it's a release.
# This doesn't affect eva_common.
# Only affects eva-exo, eva-exc, ...
if int(__version__.split('.')[-1]) != 0:
    sys.dont_write_bytecode = True

initPathsDone = False # Only expect paths.* etc to exist if this is True.
appPaths = Bunch()
paths = Bunch()
infoFlag = False

def initPaths(argsEvcPath): # {{{
    '''Populate some convenient variables from args.
    '''

    paths.fname_evc = fnameAppendExt(argsEvcPath, "evc")

    outdir = os.path.splitext(paths.fname_evc)[0] + ".eva"

    paths.outdir = outdir
    paths.fname_evcx = joinP(outdir, "evcx.toml")
    paths.fname_cfg = joinP(outdir, "config.toml")
    paths.fname_cln = joinP(outdir, "clean.vcd")
    paths.fname_mea = joinP(outdir, "measure.vcd")
    paths.dname_mea = joinP(outdir, "measure")

    #module = inspect.stack()[-1][1]
    appPaths.basemodule = os.path.basename(os.path.realpath(__file__))
    appPaths.directory = os.path.dirname(os.path.realpath(__file__))
    appPaths.share = joinP(appPaths.directory, "share")
    appPaths.configDefault = joinP(appPaths.share, "configDefault.toml")

    global initPathsDone
    initPathsDone = True

    return
# }}} def initPaths

def loadCfg(): # {{{
    '''Return config extracted from EVC and VCD.

    CFG is assumed to be sane, written by initCfg().
    '''
    assert initPathsDone

    verb("Loading CFG... ", end='')

    cfg = Bunch()
    cfg.__dict__.update(toml.load(paths.fname_cfg))

    verb("Done")

    return cfg
# }}} def loadCfg

def loadEvcx(): # {{{
    '''Return dict of measurement names to VCD hook names.
    '''
    assert initPathsDone

    verb("Loading EVCX... ", end='')

    evcx = toml.load(paths.fname_evcx)

    verb("Done")

    return evcx
# }}} def loadEvcx

def metric(name, winSize, winAlpha, nBits=0): # {{{
    '''Take attributes of a metric, return a callable implementation.

    E.g. Use like: metric("foo")(x, y)
    '''
    w = powsineCoeffs(winSize, winAlpha)

    assert 0 == nBits, "TODO: Implement fx*()"
    fs = {
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

def dsfDeltas(winSize, nReqDeltasBk, nReqDeltasFw, zoomFactor): # {{{
    '''Return a list of downsample factors and deltas (timeshifts).

    [ (<downsample factor>, <delta>), ... ]

    The downsample factor may of course be ignored, but provides a method of
    "zooming out" from a plot when there are many deltas to calculate.
    This does not choose a method of performing the downsampling.
    '''
    assert(0 <= nReqDeltasBk), nReqDeltasBk # Non-negative
    assert(1 <= nReqDeltasFw), nReqDeltasFw # Positive
    nDeltasBk = min(nReqDeltasBk, winSize // 2)
    nDeltasFw = min(nReqDeltasFw, winSize // 2)

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
    assert nDeltasBk == len([d for dsf,d in ret if d < 0])
    assert nDeltasFw == len([d for dsf,d in ret if 0 <= d])

    return ret
# }}} def dsfDeltas

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
    assert 0 <= targetTime, targetTime
    assert isinstance(precNotSucc, bool)

    hasValues = name.startswith("normal.")
    strideBytes = 8 if hasValues else 4 # [(t,v), ...] OR [t, ...]

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
                t_ = struct.unpack(">Lf" if hasValues else ">L", bs)[0]

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

            stepSize_ = (stepSize_ >> 1) if bisect_ else (stepSize_ << 1)

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

def rdEvs(names, startTime, finishTime): # {{{
    '''Read in EVent Samples the checked data written by evaInit.

    Return relevant data as NumPy array.
    '''
    assert initPathsDone

    verb("Loading EVS... ", end='')

    # TODO:
    # Read relevant timechunks and copy values into ndarray.
    # Axis0 corresponds to order of names.
    shape = (len(names), finishTime-startTime+1)
    # TODO: shape with deltas

    verb("Done")

    ret = None
    return ret
# }}} def rdEvs

