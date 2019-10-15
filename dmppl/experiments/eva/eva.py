#!/usr/bin/env python3

# EVent Analysis
#
# Run like:
#    eva.py init foo -v     # Reads foo.vcd, foo.evc.
# Write directory is ./foo.eva/

# TODO: Description and running instructions.

# Standard library imports
import argparse
import sys

# Local library imports
from dmppl.base import run, verb

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
import dmppl.experiments.eva.eva_common as eva
from eva_init import evaInit
from eva_html import evaHtml

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
    p = int(s)
    if not (2**10 <= p < 2**16 or 0 == p):
        msg = "%d in not a valid TCP port number." % p
        msg += " Must be in [1024, 65535]"
        msg += " OR 0 ==> STDOUT"
        raise argparse.ArgumentTypeError(msg)
    return p
# }}} def argparseHttpdPort

argparser_html = subparsers.add_parser("html",
    help=("Read in EVS files and serve HTML."))

argparser_html.add_argument("-p", "--httpd-port",
    type=argparseHttpdPort,
    default=8080,
    help="TCP port for server. Use 0 for STDOUT.")

argparser_html.add_argument("--vary",
    default='u',
    choices=['x', 'y', 'u'],
    help="f(x|...;u) or f(...|y;u) instead of f(x|y;...)")

fgChoices = ["Dep", "Cov", "Ham", "Tmt", "Cls", "Cos"]
argparser_html.add_argument("-f",
    type=str,
    default="Dep",
    choices=fgChoices,
    help="Function f(x|y;u)")

argparser_html.add_argument("-g",
    type=str,
    default=None,
    choices=fgChoices,
    help="Function g(x|y;u) for 2D colorspace (f, g)")

argparser_html.add_argument("-x",
    type=str,
    default=None,
    help="f(x|y;u), e.g: event.measure.cacheMiss")

argparser_html.add_argument("-y",
    type=str,
    default=None,
    help="f(x|y;u), e.g: bstate.rise.cpuIdle")

argparser_html.add_argument("-u",
    type=int,
    default=None,
    help="f(x|y;u), e.g. 9876")

# }}} argparser

def main(args): # {{{

    eva.infoFlag = args.info
    eva.initPaths(args.evc)

    ret = {
        "init": evaInit,
        #"cov":  evaCov,
        #"dep":  evaDep,
        "html": evaHtml,
        #"net":  evaNet,
    }[args.command](args)

    return ret
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
