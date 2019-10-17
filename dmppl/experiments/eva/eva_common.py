
# Standard library imports
from functools import partial
import inspect
import os

# PyPI library imports
import toml

# Local library imports
from dmppl.base import Bunch, fnameAppendExt, verb, joinP
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
    paths.fname_mea = joinP(outdir, "measure.vcd")
    paths.dname_timejumps = joinP(outdir, "timejumps")

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

