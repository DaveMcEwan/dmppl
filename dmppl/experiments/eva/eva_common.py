
import inspect

import toml

from dmppl.base import *

__version__ = "0.1.0"

paths = Bunch()

def initPaths(args): # {{{
    '''Populate some convenient variables from args.
    '''

    paths.fname_evc = fnameAppendExt(args.evc, "evc")

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
    paths.basemodule = os.path.basename(os.path.realpath(module))
    paths.directory = os.path.dirname(os.path.realpath(module))
    paths.share = paths.directory + os.sep + "share" + os.sep

    return
# }}} def initPaths

def loadCfg(): # {{{
    '''Return config extracted from EVC and VCD.

    CFG is assumed to be sane, written by initCfg().
    '''
    verb("Loading CFG... ", end='')

    cfg = Bunch()

    with open(paths.fname_cfg, 'r') as fd:
        cfg.__dict__.update(toml.load(fd))

    verb("Done")

    return cfg
# }}} def loadCfg

def loadEvcx(): # {{{
    '''Return associative array of measurement names to VCD path names.
    '''
    verb("Loading EVCX... ", end='')

    with open(paths.fname_evcx, 'r') as fd:
        evcx = toml.load(fd)

    verb("Done")

    return evcx
# }}} def loadEvcx

