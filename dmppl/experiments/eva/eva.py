#!/usr/bin/env python3
# -*- coding: utf8 -*-

# EVent Analysis
#
# Run like:
#    eva.py init foo -v     # Reads foo.vcd, foo.evc.
# Write directory is ./foo.eva/

# TODO: Description and running instructions.
# python eva.py -v init -i tst/basic2.vcd tst/basic2.evc
# python eva.py -v httpd tst/basic2.evc
# python eva.py -v init -i tst/probsys0_7k.vcd tst/basic2.evc
# python eva.py -v httpd tst/probsys0_7k.evc

# Standard library imports
import argparse
import shutil
import sys

# Local library imports
from dmppl.base import run

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
from dmppl.experiments.eva.eva_common import __version__, paths, initPaths, \
    metricNames
from eva_init import evaInit
from eva_httpd import evaHttpd

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
    help="Force removal of any existing results. "
         "Only makes sense with init, "
         "but available as a general option to prevent mistakes.")

argparser_init = subparsers.add_parser("init",
    help=("Parse VCD with EVC(YAML) to produce EVS(NumPy)."))

argparser_init.add_argument("-i", "--input",
    type=str,
    default=None,
    help="Input VCD file, STDIN if not supplied.")

def argparseHttpdPort(s): # {{{
    p = int(s)
    if not (2**10 <= p < 2**16 or 0 == p):
        msg = "%d in not a valid TCP port number." % p
        msg += " Must be in [1024, 65535]"
        msg += " OR 0 ==> STDOUT"
        raise argparse.ArgumentTypeError(msg)
    return p
# }}} def argparseHttpdPort

argparser_httpd = subparsers.add_parser("httpd",
    help=("Read in EVS files and serve HTML."))

argparser_httpd.add_argument("-p", "--httpd-port",
    type=argparseHttpdPort,
    default=8080,
    help="TCP port for server. Use 0 for STDOUT.")

argparser_httpd.add_argument("-f",
    type=str,
    default=metricNames[0],
    choices=metricNames,
    help="Function f(x|y;u)")

argparser_httpd.add_argument("-g",
    type=str,
    default=None,
    choices=metricNames,
    help="Function g(x|y;u) for 2D colorspace (f, g)")

argparser_httpd.add_argument("-x",
    type=str,
    default=None,
    help="String measurement name in f(x|y;u), e.g: event.measure.cacheMiss")

argparser_httpd.add_argument("-y",
    type=str,
    default=None,
    help="String measurement name in f(x|y;u), e.g: bstate.rise.cpuIdle")

argparser_httpd.add_argument("-u",
    type=str, # Int conversion performed later for consistency with HTTPD.
    default=None,
    help="Non-negative integer time in f(x|y;u), e.g. 9876")

# }}} argparser

def main(args): # {{{

    initPaths(args.evc)

    if args.purge:
        assert paths._INITIALIZED
        shutil.rmtree(paths.outdir)

    ret = {
        "init": evaInit,
        "httpd": evaHttpd,
    }[args.command](args)

    return ret
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
