#!/usr/bin/env python3

# EVent Analysis
#
# Run like:
#    eva.py init foo -v     # Reads foo.vcd, foo.evc.
# Write directory is ./foo.eva/

# TODO: Description and running instructions.

# Standard library imports
import argparse

# Local library imports
from dmppl.base import *

# Project imports
import eva_common as eva
from eva_init import evaInit

__version__ = eva.__version__

# {{{ argparser

argparser = argparse.ArgumentParser(
    description = "eva - EVent Analysis."
        " - Analyse event data in VCD according to configuration in EVC",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

#subparsers = argparser.add_subparsers(dest="command", required=True) # Python3.7+
subparsers = argparser.add_subparsers(dest="command") # Python2.7+
subparsers.required = True

argparser.add_argument("evc",
    type=str,
    help="'foo' reads foo.evc, foo.vcd, and writes to foo.eva/*")

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

argparser_init = subparsers.add_parser("init",
    help=("Parse VCD with EVC(YAML) to produce EVS(NumPy)."))

argparser_init.add_argument("-i", "--input",
    type=str,
    default=None,
    help="Input VCD file, STDIN if not supplied.")

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

    eva.infoFlag = args.info
    eva.initPaths(args)

    ret = {
        "init": evaInit,
        #"cov":  evaCov,
        #"dep":  evaDep,
        #"html": evaHtml,
        #"net":  evaNet,
    }[args.command](args)

    return ret
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
