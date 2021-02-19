#!/usr/bin/env python3

# Dave McEwan 2018-02-22
#
# Run like:
#    ./colorspace.py # Then look at pictures in output directory.

from __future__ import print_function

import argparse
from itertools import product
import numpy as np
from os import sep
import sys

import png

from dmppl.base import run, verb, mkDirP

__version__ = "0.0.0"

def cs0(args, fname="cs0.png", rows=512, cols=512,
        color_comb="BRG", invert_origin=False, invert_color=False): # {{{
    '''Generate 2D colorspace for points with both dimensions in [0, 1].
       White at origin means when printed on a white background (like paper)
       smaller values don't show.
       Large in both dimension shows as black.
       Large in one dimension will show as bluey-purple or greeny-yellow.
       Darker is more significant.
    '''

    coords = np.empty((rows, cols), dtype=np.complex_) # [0+i0, 1+i1]

    for row,col in product(range(rows), range(cols)):
        coords[row][col] = np.complex_(float(rows - row - 1)/rows + 1j* float(col)/cols)

    if invert_origin:
        coords = 1+1j - 1j*np.conjugate(coords) # Invert origin

    coords_mag = np.absolute(coords)
    coords_arg = np.angle(coords)

    # NOTE: 1.5 is a nice gamma.
    # NOTE: Larger gamma means more white at origin,
    #   intuitively that means more points are ignored.

    b = 1-(coords_mag/np.sqrt(2))**args.png_gamma
    assert np.all(np.greater_equal(b, 0))
    assert np.all(np.less_equal(b, 1))

    a = b**(np.maximum(0, coords_arg - np.pi/4)+1)
    c = b**(np.maximum(0, np.pi/4 - coords_arg)+1)
    assert np.all(np.greater_equal(a, 0))
    assert np.all(np.less_equal(a, 1))
    assert np.all(np.greater_equal(c, 0))
    assert np.all(np.less_equal(c, 1))

    if invert_color:
        a = 1 - a
        b = 1 - b
        c = 1 - c

    # Scale to 8bit depth and assign colors.
    color_comb = color_comb.upper()
    if   color_comb[0] == 'R': R = (255 * a).astype(int)
    elif color_comb[0] == 'G': G = (255 * a).astype(int)
    elif color_comb[0] == 'B': B = (255 * a).astype(int) # default
    if   color_comb[1] == 'R': R = (255 * b).astype(int) # default
    elif color_comb[1] == 'G': G = (255 * b).astype(int)
    elif color_comb[1] == 'B': B = (255 * b).astype(int)
    if   color_comb[2] == 'R': R = (255 * c).astype(int)
    elif color_comb[2] == 'G': G = (255 * c).astype(int) # default
    elif color_comb[2] == 'B': B = (255 * c).astype(int)
    assert np.all(np.greater_equal(R, 0))
    assert np.all(np.less_equal(R, 255))
    assert np.all(np.greater_equal(G, 0))
    assert np.all(np.less_equal(G, 255))
    assert np.all(np.greater_equal(B, 0))
    assert np.all(np.less_equal(B, 255))

    RGB = np.dstack([R, G, B]).reshape((rows, cols*3))

    w = png.Writer(height=rows, width=cols,
                   greyscale=False,
                   alpha=False,
                   bitdepth=8)

    mkDirP(args.output_dir)
    with open(args.output_dir + sep + fname, 'wb') as fd:
        w.write(fd, RGB)
# }}}

# {{{ argparser

argparser = argparse.ArgumentParser(
    description = "colorspace - Generate colorspace plots.",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("--output-dir",
    type=str,
    default="results",
    help="Directory in which to store result files.")

argparser.add_argument("--png-gamma",
    type=float,
    default=1.0,
    help="Gamma correction factor for non-binary data.")

# }}} argparser

def main(args): # {{{
    '''
    '''

    # NOTE: rows/cols here are opposite in PNG world so upper-left and
    # lower-right corners are swapped.
    # Therefore BRG may be the default but GRB is how it appears normally.
    cs0(args, fname="cs0_combGRB.png", color_comb="GRB")

    cs0(args, fname="cs0_combBRG.png")
    cs0(args, fname="cs0_combBRG_invcolor.png", invert_color=True)
    cs0(args, fname="cs0_combBRG_invorigin.png", invert_origin=True)
    cs0(args, fname="cs0_combRGB.png", color_comb="RGB")
    cs0(args, fname="cs0_combRBG.png", color_comb="RBG")

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
