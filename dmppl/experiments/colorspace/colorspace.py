#!/usr/bin/env python2.7

# Event Analysis
# Dave McEwan 2018-02-22
#
# Run like:
#    ./colorspace2d.py # Then look at pictures in output directory.

from __future__ import print_function
import sys

version_help = "Python 2.7 or 3.4+ required."
if sys.version_info[0] == 2:
    assert sys.version_info[1] == 7, version_help
elif sys.version_info[0] == 3:
    assert sys.version_info[1] >= 4, version_help
else:
    assert False, version_help

import os
import errno
import numpy as np
import itertools
import png

verbose = False

def mkdir_p(path=""): # {{{
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
    return
# }}}

def verb(msg='', end='\n'): # {{{
    if verbose:
        print(msg, end=end)
        sys.stdout.flush()
# }}}

def dbg(x=''): # {{{
    if __debug__:
        func = sys._getframe().f_back.f_code.co_name
        line = sys._getframe().f_back.f_lineno

        if isinstance(x, list) or isinstance(x, tuple) or isinstance(x, set):
            msg = ", ".join([str(i) for i in x])
        elif isinstance(x, dict):
            msg = ", ".join(["%s: %s" % (str(k), str(x[k])) for k in x])
        else:
            msg = str(x)

        print("%s():%s: %s" % (func, line, msg))
# }}}

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

    for row,col in itertools.product(range(rows), range(cols)):
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

    mkdir_p(args.output_dir)
    with open(args.output_dir + os.sep + fname, 'wb') as fd:
        w.write(fd, RGB)
# }}}

def get_args(): # {{{
    '''Parse cmdline arguments and return seed and object from YAML config.
    '''
    import argparse

    parser = argparse.ArgumentParser(
        description = "colorspace - Generate colorspace plots.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-v", "--verbose",
                        default=False,
                        action='store_true',
                        help="Display progress messages.")

    parser.add_argument("--output-dir",
                        type=str,
                        default=".",
                        help="Directory in which to store result files.")

    parser.add_argument("--png-gamma",
                        type=float,
                        default=1.0,
                        help="Gamma correction factor for non-binary data.")

    args = parser.parse_args()

    # Global just used to keep verbose printing tidy.
    global verbose
    verbose = args.verbose

    return args
# }}}

if __name__ == "__main__":

    ret = 1
    try:
        args = get_args()

        # NOTE: rows/cols here are opposite in PNG world so upper-left and
        # lower-right corners are swapped.
        # Therefore BRG may be the default but GRB is how it appears normally.
        cs0(args, fname="cs0_combGRB.png", color_comb="GRB")

        cs0(args, fname="cs0_combBRG.png")
        cs0(args, fname="cs0_combBRG_invcolor.png", invert_color=True)
        cs0(args, fname="cs0_combBRG_invorigin.png", invert_origin=True)
        cs0(args, fname="cs0_combRGB.png", color_comb="RGB")
        cs0(args, fname="cs0_combRBG.png", color_comb="RBG")

    except IOError as e:
        msg = 'IOError: %s: %s\n' % (e.strerror, e.filename)
        sys.stderr.write(msg)
    else:
        ret = 0

    sys.exit(ret)
