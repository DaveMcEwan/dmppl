#!/usr/bin/env python3

# Dave McEwan 2018-02-22
#
# Run like:
#    ./colorspace.py -v # Then look at pictures in output directory.

import argparse
from functools import partial
from itertools import product
import numpy as np
from os import sep
import sys

import png

from dmppl.base import run, verb, mkDirP

__version__ = "0.0.0"

def cs0(a, b, **kwargs): # {{{
    '''Return RGB tuple to represent bounded pair of values a,b as color.

    Most useful where a and b combine with magnitude and angle.
    Higher values of a and b are darker, which looks good on printed paper.
    Similar perception between normal color vision and protantopes.

    Implementation of colorspace in https://arxiv.org/abs/1905.06386
    '''
    assert isinstance(a, float), "type(a)=%s" % str(type(a))
    assert np.isnan(a) or 0.0 <= a <= 1.0, a
    if np.isnan(a):
        a = 0.0

    assert isinstance(b, float), "type(b)=%s" % str(type(b))
    assert np.isnan(b) or 0.0 <= b <= 1.0, b
    if np.isnan(b):
        b = 0.0

    gamma = float(kwargs.get("gamma", 1.0))

    nBits = int(kwargs.get("nBits", 8))
    assert nBits > 1

    magColor = kwargs.get("magColor", 'r').lower()
    assert magColor in ('r', 'g', 'b'), magColor

    invOrigin = bool(kwargs.get("invOrigin", False))
    if invOrigin:
        a, b = (1 - a), (1 - b)

    theta = 1.0 - (np.sqrt(a**2 + b**2) / np.sqrt(2.0))**gamma
    phi = np.arctan2(a, b)

    pi4 = 0.25 * np.pi
    fullBrightness = 2**nBits - 1

    red = int( fullBrightness * theta )
    green = int( fullBrightness * theta**(1 + max(0, phi - pi4)) )
    blue = int( fullBrightness * theta**(1 + max(0, pi4 - phi)) )

    if 'b' == magColor:
        red, green, blue = blue, green, red
    elif 'g' == magColor:
        red, green, blue = green, red, blue
    else:
        assert 'r' == magColor

    # Swap green/blue to keep purble/green in the same corners.
    if invOrigin:
        red, green, blue = red, blue, green

    return (red, green, blue)
# }}} def cs0

def makePng(f, fname, nRows=512, nCols=512): # {{{
    '''Take a colorspace callable, sweep over all values to create PNG.
    '''
    pixArray = np.ndarray((nRows, nCols), dtype=np.uint8)
    R, G, B = pixArray, pixArray.copy(), pixArray.copy()

    # NOTE: Reflect rows to match PNG coordinate system.
    for r,c in product(range(nRows), range(nCols)):
        R[r][c], G[r][c], B[r][c] = f(1 - r/nRows, c/nCols)

    w = png.Writer(height=nRows, width=nCols,
                   greyscale=False,
                   alpha=False,
                   bitdepth=8)

    with open(fname, 'wb') as fd:
        w.write(fd, np.dstack([R, G, B]).reshape((nRows, nCols*3)))
# }}} def makePng

# {{{ argparser

argparser = argparse.ArgumentParser(
    description = "colorspace - Generate colorspace plots.",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("--output-dir",
    type=str,
    default="results",
    help="Directory in which to store result files.")

argparser.add_argument("--gamma",
    type=float,
    default=1.1,
    help="Gamma correction factor for non-binary data.")

# }}} argparser

def main(args): # {{{
    '''
    '''

    mkDirP(args.output_dir)
    fdir = args.output_dir + sep

    f = partial(cs0, gamma=args.gamma)

    verb("cs0...", end='')
    makePng(f,                                          fdir+"cs0.png")
    verb("DONE")

    verb("cs0_invOrigin...", end='')
    makePng(partial(f, invOrigin=True),                 fdir+"cs0_invOrigin.png")
    verb("DONE")

    verb("cs0_magB...", end='')
    makePng(partial(f, gamma=args.gamma, magColor='b'), fdir+"cs0_magB.png")
    verb("DONE")

    verb("cs0_magG...", end='')
    makePng(partial(f, gamma=args.gamma, magColor='g'), fdir+"cs0_magG.png")
    verb("DONE")

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
