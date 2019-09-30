
# Standard library imports
import inspect
import os

# PyPI library imports
import toml

# Local library imports
from dmppl.base import Bunch, fnameAppendExt, verb

__version__ = "0.1.0"

initDone = False # Only expect paths.* etc to exist if this is True.
appPaths = Bunch()
paths = Bunch()
infoFlag = False

def initPaths(argsEvcPath): # {{{
    '''Populate some convenient variables from args.
    '''

    paths.fname_evc = fnameAppendExt(argsEvcPath, "evc")

    outdir = os.path.splitext(paths.fname_evc)[0] + ".eva" + os.sep

    paths.outdir = outdir
    paths.fname_evcx = outdir + "evcx.toml"
    paths.fname_cfg = outdir + "config.toml"
    paths.fname_evs = outdir + "evs"
    paths.fname_evs_vcd = outdir + "evs.vcd"
    #paths.fname_bad = outdir + "bad"
    #paths.fname_bad_vcd = outdir + "bad.vcd"
    #paths.fname_ex = outdir + "ex"
    #paths.fname_ex_vcd = outdir + "ex.vcd"
    #paths.fname_cex_base = outdir + "cex.X="
    #paths.fname_dep_base = outdir + "dep.X="
    #paths.fname_cov_base = outdir + "cov.X="
    #paths.dname_net = outdir + "net" + os.sep

    module = inspect.stack()[-1][1]
    appPaths.basemodule = os.path.basename(os.path.realpath(module))
    appPaths.directory = os.path.dirname(os.path.realpath(module))
    appPaths.share = appPaths.directory + os.sep + "share" + os.sep
    appPaths.configDefault = appPaths.share + "configDefault.toml"

    global initDone
    initDone = True

    return
# }}} def initPaths

def loadCfg(): # {{{
    '''Return config extracted from EVC and VCD.

    CFG is assumed to be sane, written by initCfg().
    '''
    assert initDone

    verb("Loading CFG... ", end='')

    cfg = Bunch()
    cfg.__dict__.update(toml.load(paths.fname_cfg))

    verb("Done")

    return cfg
# }}} def loadCfg

def loadEvcx(): # {{{
    '''Return dict of measurement names to VCD hook names.
    '''
    assert initDone

    verb("Loading EVCX... ", end='')

    evcx = toml.load(paths.fname_evcx)

    verb("Done")

    return evcx
# }}} def loadEvcx

