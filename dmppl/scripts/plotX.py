#!/usr/bin/env python3

# plotX - Create simple plots from Python expressions of variable x.
# Dave McEwan 2020-05-21
#
# Run like:
#    plotX "x**2 + 0.5*x + pi*cos(x)"
#    plotX -vn 1000 "cos(x)" "sqrt(x)" "arctan(x)"

import argparse
import functools
import matplotlib
matplotlib.use("Agg") # Don't require X11.
import matplotlib.pyplot as plt
import numpy as np
import sys

# NOTE: Importing everything from math, rather than specific functions, is
# intentional allow eval() to use cos, sin, pi, etc.
from math import *
from numpy import *

from dmppl.base import fnameAppendExt, run, verb, argparse_positiveInteger

__version__ = "0.1.0"


# {{{ argparser

argparser = argparse.ArgumentParser(
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("-o", "--output",
    type=str,
    default="plot",
    help="Output filepath, without extension.")

argparser.add_argument("expr",
    nargs='+',
    help="Expression to plot.")

argparser.add_argument("--pdf",
    action="store_true",
    help="Create PDF instead of PNG.")

argparser.add_argument("--figsize",
    type=str,
    default="16,10",
    help="Horizontal,vertical (inches).")

argparser.add_argument("-n", "--nsamples",
    type=functools.partial(argparse_positiveInteger, "nsamples"),
    default=100,
    help="Number of samples of x.")

argparser.add_argument("--markers",
    type=str,
    default=".ox^s*",
    help="Markers in matplotlib notation.")

argparser.add_argument("--title",
    type=str,
    default=None)

argparser.add_argument("--xlabel",
    type=str,
    default=None)

argparser.add_argument("--ylabel",
    type=str,
    default=None)

argparser.add_argument("--xlim",
    type=str,
    default="0,255",
    help="Limits for X-axis like '0.1,5.5'.")

argparser.add_argument("--ylim",
    type=str,
    default=None,
    help="Limits for Y-axis like '0.1,5.5'.")

argparser.add_argument("--vlines",
    type=str,
    default=None,
    help="Vertical lines like '0,1.8'.")

argparser.add_argument("--hlines",
    type=str,
    default=None,
    help="Horizontal lines like '0,1.8'.")

# }}} argparser

def main(args) -> int: # {{{
    '''
    '''

    ###########################################################################
    # 1. Setup plot
    ###########################################################################

    fignum = 0

    # figsize used to set dimensions in inches.
    # ax.set_aspect() doesn't work for KDE where Y-axis is scaled.
    figsize = tuple(int(a) for a in args.figsize.split(','))
    assert 2 == len(figsize)
    assert all(0 < i for i in figsize)

    fig = plt.figure(fignum, figsize=figsize)

    if args.xlabel:
        plt.xlabel(args.xlabel)

    if args.ylabel:
        plt.ylabel(args.ylabel)

    if args.title:
        plt.title(args.title)

    if args.xlim:
        xLo, xHi = args.xlim.split(',')
        plt.xlim(float(xLo), float(xHi))

    _xLo, _xHi = args.xlim.split(',')
    xLo, xHi = float(_xLo), float(_xHi)
    plt.xlim(xLo, xHi)

    if args.ylim:
        yLo, yHi = args.ylim.split(',')
        plt.ylim(float(yLo), float(yHi))

    if args.title:
        plt.title(args.title)

    markers = list(args.markers)


    ###########################################################################
    # 2. Populate data
    ###########################################################################

    x = np.linspace(xLo, xHi, args.nsamples)
    ys = (np.apply_along_axis(eval("lambda x: " + e), 0, x) for e in args.expr)


    ###########################################################################
    # 3. Draw plot
    ###########################################################################

    for i,y in enumerate(ys):
        verb("Plotting `%s`" % args.expr[i])
        marker = markers[i] if i < len(markers) else ''
        label = args.expr[i]

        kwargsPlot = {"marker": marker}
        if label is not None:
            kwargsPlot.update({"label": label})

        plt.plot(x, y, **kwargsPlot)

    plt.legend()

    if args.vlines:
         for line in args.vlines.split(','):
            plt.axvline(y=float(line), color="green", linestyle='-', linewidth=1)

    if args.hlines:
         for line in args.hlines.split(','):
            plt.axhline(y=float(line), color="green", linestyle='-', linewidth=1)


    ###########################################################################
    # 4. Save plot to file
    ###########################################################################

    if args.pdf:
        plt.savefig(fnameAppendExt(args.output, "pdf"), bbox_inches="tight")
    else:
        plt.savefig(fnameAppendExt(args.output, "png"), bbox_inches="tight")

    plt.close()

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

