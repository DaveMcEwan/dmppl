#!/usr/bin/env python3

# plotDistBytes - Plot the distribution of bytes values in a file.
# Dave McEwan 2020-05-07
#
# Run like:
#    plotDistBytes mydata.bin

import argparse
import seaborn as sns
import matplotlib
matplotlib.use("Agg") # Don't require X11.
import matplotlib.pyplot as plt
import numpy as np
import sys

from dmppl.base import fnameAppendExt, run, verb

__version__ = "0.1.0"

# {{{ argparser

argparser = argparse.ArgumentParser(
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("-o", "--output",
    type=str,
    default="plot",
    help="Output filepath, without extension.")

argparser.add_argument("input",
    type=str,
    help="Binary file.")

argparser.add_argument("--title",
    type=str,
    default=None)

argparser.add_argument("--pdf",
    action="store_true",
    help="Create PDF as well as PNG.")

argparser.add_argument("--svg",
    action="store_true",
    help="Create SVG as well as PNG.")

argparser.add_argument("--markers",
    type=str,
    default=".ox^s*",
    help="Markers.")

argparser.add_argument("--figsizeX",
    type=int,
    default=16,
    help="Vertical (inches).")

argparser.add_argument("--figsizeY",
    type=int,
    default=10,
    help="Horizontal (inches).")

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

# }}} argparser

def main(args) -> int: # {{{
    '''
    '''

    fignum = 0

    # figsize used to set dimensions in inches.
    # ax.set_aspect() doesn't work for KDE where Y-axis is scaled.
    figsize = (args.figsizeX, args.figsizeY)

    fig = plt.figure(fignum, figsize=figsize)

    if args.xlabel:
        plt.xlabel(args.xlabel)

    if args.ylabel:
        plt.ylabel(args.ylabel)

    _xLo, _xHi = args.xlim.split(',')
    xLo, xHi = float(_xLo), float(_xHi)
    plt.xlim(xLo, xHi)

    plt.xticks(list(range(int(xLo), int(xHi)+1, 8)))

    if args.ylim:
        yLo, yHi = args.ylim.split(',')
        plt.ylim(float(yLo), float(yHi))

    if args.title:
        plt.title(args.title)

    markers = list(args.markers)

    dataset = np.fromfile(args.input, dtype=np.uint8)

    sns.distplot(dataset, bins=list(range(256)))

    plt.savefig(fnameAppendExt(args.output, "png"), bbox_inches="tight")

    if args.pdf:
        plt.savefig(fnameAppendExt(args.output, "pdf"), bbox_inches="tight")

    if args.svg:
        plt.savefig(fnameAppendExt(args.output, "svg"), bbox_inches="tight")

    plt.close()

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

