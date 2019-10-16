
# Standard library imports
import inspect
import os

# PyPI library imports
import toml

# Local library imports
from dmppl.base import Bunch, fnameAppendExt, verb, joinP

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

