#!/usr/bin/env python3

# plotCsv - Create simple plots from a CSV file.
# Dave McEwan 2020-04-29
#
# Run like:
#    plotCsv mydata.csv
#    OR
#    cat mydata.csv | plotCsv -o myplot

import argparse
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
    help="Output file without extension.")

argparser.add_argument("input",
    type=str,
    help="CSV file, or STDIN if None.")

argparser.add_argument("--figsizeX",
    type=int,
    default=8)

argparser.add_argument("--figsizeY",
    type=int,
    default=5)

argparser.add_argument("--xlabel",
    type=str,
    default=None)

argparser.add_argument("--ylabel",
    type=str,
    default=None)

argparser.add_argument("--title",
    type=str,
    default=None)

argparser.add_argument("--pdf",
    action="store_true",
    help="Create PDF.")

argparser.add_argument("--integer",
    action="store_true",
    help="Treat all data as integers rather than reals.")

argparser.add_argument("--diffY",
    action="store_true",
    help="Plot difference rather than value.")

argparser.add_argument("--ratio",
    action="store_true",
    help="Plot ratio between x and y.")

argparser.add_argument("--x0",
    action="store_true",
    help="Subtract top-left value from all values in left column (x-axis).")

# }}} argparser

def main(args) -> int: # {{{
    '''
    '''

    fnamePng = fnameAppendExt(args.output, "png")
    fnamePdf = fnameAppendExt(args.output, "pdf")

    fignum = 0

    # figsize used to set dimensions in inches.
    # ax.set_aspect() doesn't work for KDE where Y-axis is scaled.
    figsize = (args.figsizeX, args.figsizeY)

    fig = plt.figure(fignum, figsize=figsize)

    if args.xlabel:
        plt.xlabel(args.xlabel)

    if args.ylabel:
        plt.ylabel(args.ylabel)

    if args.title:
        plt.title(args.title)

    markers = ['.', 'o', 'x', '^', 's', '*']

    dtype = np.int if args.integer else np.float
    a = np.loadtxt(args.input, delimiter=',', unpack=True, dtype=dtype)

    x = a[0]
    if args.x0:
        x -= x[0]

    ys = a[1:]

    for i,y in enumerate(ys):

        if args.diffY:
            y = np.append([0], np.diff(y))

        if args.ratio:
            y = np.array([x_ / y_ for x_,y_ in zip(x, y)])

        marker = markers[i] if i < len(markers) else ''
        plt.plot(x, y, marker=marker)

    plt.savefig(fnameAppendExt(args.output, "png"), bbox_inches="tight")

    if args.pdf:
        plt.savefig(fnameAppendExt(args.output, "pdf"), bbox_inches="tight")

    plt.close()

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

