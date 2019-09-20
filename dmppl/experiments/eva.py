#!/usr/bin/env python3

# EVent Analysis
#
# Run like:
#    eva.py vcd2evs foo -v     # Reads foo.vcd, foo.evc.
# Write directory is ./foo.eva/

# TODO: Description and running instructions.

import argparse
import yaml

from dmppl.base import *
from dmppl.math import *
from dmppl.nd import *
from dmppl.yaml import *

__version__ = "0.1.0"

paths = Bunch()

def initPaths(args): # {{{
    '''Populate some convenient variables from args.
    '''

    dataname = os.path.splitext(args.dataname)[0] # Ignore file extension.
    paths.dataname = dataname
    paths.basename = os.path.basename(dataname)

    paths.fname_evc = dataname + ".evc"
    paths.fname_vcd = dataname + ".vcd"

    outdir = dataname + ".eva" + os.sep
    paths.outdir = outdir
    paths.fname_evcx = outdir + "evcx.yml"
    paths.fname_cfg = outdir + "config.yml"
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

    return
# }}} def initPaths

cfg = Bunch()

def initCfg(evcCfg, vcd): # {{{
    '''Fill in then save CFG.
    '''
    verb("Initializing CFG... ", end='')

    # vcd2evs defaults.
    cfg.vcdhierprefix = "module:TOP."
    cfg.vcdtimestep = 10

    # eva-analyse defaults.
    cfg.fxbits = 0 # Fixed point processing. 0=float.
    cfg.powsinealpha = 0 # 0=Rectangular, 1=Sine, 2=Hann
    cfg.windowsize = 64
    cfg.windowoverlap = 0
    cfg.deltabk = 64
    cfg.deltafw = 1
    cfg.zoomdelta = max(cfg_dict["deltabk"], cfg_dict["deltafw"]) # Default to no zooming.
    cfg.depepsilon = 0.1
    cfg.covepsilon = 0.1
    cfg.jacepsilon = 0.1
    cfg.cosepsilon = 0.1
    cfg.clsepsilon = 0.1

    # Respin config to enable YAML representer.
    evcCfg = {str(k): (str(v) if isinstance(v, str) else v) for k,v in evcCfg.items()}
    evcCfg = {str(k): (int(v) if isinstance(v, int) else v) for k,v in evcCfg.items()}
    evcCfg = {str(k): (float(v) if isinstance(v, float) else v) for k,v in evcCfg.items()}
    cfg.__dict__.update(evcCfg)

    # Add VCD information.
    # TODO: vcd.VcdReader
    start_t = vcd["starttime"]
    finish_t = vcd["finishtime"]
    t_step = cfg.vcdtimestep

    assert isinstance(start_t, (int, long))
    assert isinstance(finish_t, (int, long))
    assert isinstance(t_step, (int, long))

    t_offset = start_t // t_step
    n_times = (finish_t - start_t) // t_step + 1

    cfg.t_offset = t_offset
    cfg.n_times = n_times
    assert n_times > 0, "n_times=%d" % n_times

    verb("Saving... ", end='')
    with open(paths.fname_cfg, 'w') as fd:
        yaml.safe_dump(cfg_dict, fd)

    verb("Done")

    return cfg
# }}} def initCfg

def loadCfg(): # {{{
    '''Return config extracted from EVC and VCD.

    CFG is assumed to be sane, written by initCfg().
    '''
    verb("Loading CFG... ", end='')

    with open(paths.fname_cfg, 'r') as fd:
        cfg.__dict__.update(yaml.safe_load(fd))

    verb("Done")

    return cfg
# }}} def loadCfg

def loadEvcx(): # {{{
    '''Return associative array of measurement names to VCD path names.
    '''
    verb("Loading EVCX... ", end='')

    with open(paths.fname_evcx, 'r') as fd:
        evcx = yaml.safe_load(fd)

    verb("Done")

    return evcx
# }}} def loadEvcx

# {{{ argparser

argparser = argparse.ArgumentParser(
    description = "eva - EVent Analysis."
        " - Analyse event data in VCD according to configuration in EVC",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

#subparsers = argparser.add_subparsers(dest="command", required=True) # Python3.7+
subparsers = argparser.add_subparsers(dest="command") # Python2.7+
subparsers.required = True

argparser.add_argument("dataname",
    type=str,
    help="'foo' reads foo.vcd, foo.evc, and writes to foo.eva/*")

argparser.add_argument("--info",
    default=False,
    action='store_true',
    help="Print additional information about results.")

argparser.add_argument("-j", "--n_jobs",
    type=int,
    default=-2,
    help="Number of parallel jobs.")

argparser.add_argument("-r", "--purge",
    default=False,
    action='store_true',
    help="Force removal of any existing results.")

argparser.add_argument("--savetxt",
    default=False,
    action='store_true',
    help="Save results in text format.")

argparser.add_argument("--savevcd",
    default=False,
    action='store_true',
    help="Save results in VCD format.")

argparser_vcd2evs = subparsers.add_parser("vcd2evs",
    help=("Parse VCD with EVC(YAML) to produce EVS(NumPy)."))

argparser_cov = subparsers.add_parser("cov",
    help=("Apply Cov(X,Y) to EVent Samples."))

argparser_dep = subparsers.add_parser("dep",
    help=("Apply Dep(X,Y) to EVent Samples."))


def argparseHttpdPort(s): # {{{
    val = int(s)
    if not 2**10 <= val < 2**16:
        msg = "{} in not a valid TCP port number.".format(s)
        msg += " (1024 <= p < 65535)"
        raise argparse.ArgumentTypeError(msg)
    return val
# }}} def argparseHttpdPort

argparser_html = subparsers.add_parser("html",
    help=("Read in EVS files and serve HTML."))

argparser_html.add_argument("-p", "--httpd-port",
    type=argparseHttpdPort,
    default=8080,
    help="TCP port for HTTP server. Use 0 for STDOUT.")

argparser_html.add_argument("--leads",
    default="x-given-y",
    choices=["to-X-at-u", "from-Y-at-u"],
    help="F(X|...;u) or F(...|Y;u) instead of F(X|Y;...")

argparser_html.add_argument("-F", "--F",
    type=str,
    default="E",
    choices=["E", "Dep", "Cov", "DepCov", "Ham", "Tmt", "Cls", "Cos"],
    help="Analysis type.")

argparser_html.add_argument("-X", "--X",
    type=str,
    default=None,
    help="F(X|Y;U), e.g. f_b.axi.ar")

argparser_html.add_argument("-Y", "--Y",
    type=str,
    default=None,
    help="F(X|Y;U), e.g. gp_r.rail.voltage")

argparser_html.add_argument("-U", "--U",
    type=int,
    default=None,
    help="F(X|Y;U), e.g. 9876")

# }}} argparser

def main(args): # {{{
    '''
    '''

    initPaths(args)

    print(paths.outdir)
    #mkDirP(paths.outdir)


    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
