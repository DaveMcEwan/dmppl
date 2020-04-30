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
    help="Output filepath, without extension.")

argparser.add_argument("input",
    type=str,
    help="CSV file, or STDIN if None.")

argparser.add_argument("--title",
    type=str,
    default=None)

argparser.add_argument("--pdf",
    action="store_true",
    help="Create PDF instead of PNG.")

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
    default=None,
    help="Limits for X-axis like '0.1,5.5'.")

argparser.add_argument("--ylim",
    type=str,
    default=None,
    help="Limits for Y-axis like '0.1,5.5'.")

argparser.add_argument("--baseX",
    action="store_true",
    help="Set --addX to negative top value of left column.")

argparser.add_argument("--baseY",
    action="store_true",
    help="Set --addY to negative top value of right column.")

argparser.add_argument("--addX",
    type=float,
    default=None,
    help="Add constant to left column.")

argparser.add_argument("--addY",
    type=float,
    default=None,
    help="Add constant to right column(s).")

argparser.add_argument("--mulX",
    type=float,
    default=None,
    help="Multiply left column.")

argparser.add_argument("--mulY",
    type=float,
    default=None,
    help="Multiply right column(s).")

argparser.add_argument("--intX",
    action="store_true",
    help="Treat left column as integers rather than reals.")

argparser.add_argument("--intY",
    action="store_true",
    help="Treat right column as integers rather than reals.")

argparser.add_argument("--product",
    action="store_true",
    help="Plot product of x and y, after manipulation, on Y-axis.")

argparser.add_argument("--diffX",
    action="store_true",
    help="Difference x for plotting product.")

argparser.add_argument("--diffY",
    action="store_true",
    help="Difference y for plotting product.")

argparser.add_argument("--invX",
    action="store_true",
    help="Inverse x for plotting product.")

argparser.add_argument("--invY",
    action="store_true",
    help="Inverse y for plotting product.")

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

    if args.xlim:
        xLo, xHi = args.xlim.split(',')
        plt.xlim(float(xLo), float(xHi))

    if args.ylim:
        yLo, yHi = args.ylim.split(',')
        plt.ylim(float(yLo), float(yHi))

    if args.title:
        plt.title(args.title)

    markers = list(args.markers)

    a = np.loadtxt(args.input, delimiter=',', unpack=True)

    x = a[0]

    if args.baseX:
        args.addX = x[0] * -1

    if args.addX:
        verb("Add constant to X axis. (+ %0.05f)" % args.addX)
        x += args.addX

    if args.mulX:
        verb("Multiply X axis by constant. (* %0.05f)" % args.mulX)
        x *= args.mulX

    if args.intX:
        verb("Reduce X axis to integers.")
        x = x.astype(np.int)

    if args.product:
        prdX = np.copy(x)

        if args.diffX:
            verb("Product difference X axis.")
            tmpX = np.zeros(prdX.shape)
            tmpX[1:] = np.diff(prdX)
            prdX = tmpX

        if args.invX:
            verb("Product X**-1 axis.")
            prdX = prdX.astype(np.float)
            prdX **= -1

    ys = a[1:]
    for i,y in enumerate(ys):
        marker = markers[i] if i < len(markers) else ''

        if args.baseY:
            args.addY = y[0] * -1

        if args.addY:
            verb("Add constant to Y axis[%d]. (+ %0.05f)" % (i, args.addY))
            y += args.addY

        if args.mulY:
            verb("Multiply Y axis (%d) by constant. (%0.05f)" % (i, args.mulY))
            y *= args.mulY

        if args.intY:
            verb("Reduce Y axis (%d) to integers.")
            y = y.astype(np.int)

        if args.product:
            prdY = np.copy(y)

            if args.diffY:
                verb("Product difference Y axis.")
                tmpY = np.zeros(prdY.shape)
                tmpY[1:] = np.diff(prdY)
                prdY = tmpY

            if args.invY:
                verb("Product Y**-1 axis.")
                prdY = prdY.astype(np.float)
                prdY **= -1

            y = prdX * prdY

        plt.plot(x, y, marker=marker)


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

