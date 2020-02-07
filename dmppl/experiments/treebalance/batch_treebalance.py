#!/usr/bin/env python

from __future__ import print_function
import sys
import os

version_help = "Python 2.7 or 3.4+ required."
if sys.version_info[0] == 2:
    assert sys.version_info[1] == 7, version_help
elif sys.version_info[0] == 3:
    assert sys.version_info[1] >= 4, version_help
else:
    assert False, version_help

from math import *
golden = (1 + 5**0.5) / 2

from treebalance import available_mappings

if __name__ == "__main__": # {{{
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--bmin",
                        type=int,
                        default=2,
                        help="Minimum base.")

    parser.add_argument("--bmax",
                        type=int,
                        default=9,
                        help="Maximum base.")

    parser.add_argument("--wmin",
                        type=int,
                        default=2,
                        help="Minimum width.")

    parser.add_argument("--wmax",
                        type=int,
                        default=2000,
                        help="Maximum width.")

    parser.add_argument("--wbatch",
                        type=int,
                        default=100,
                        help="Maximum width.")

    parser.add_argument("--amin",
                        type=float,
                        default=-2.0,
                        help="Minimum alpha.")

    parser.add_argument("--amax",
                        type=float,
                        default=2.1,
                        help="Maximum alpha.")

    parser.add_argument("--alen",
                        type=int,
                        default=41,
                        help="Number of alpha values.")

    parser.add_argument("-z", "--algorithms",
                        type=str,
                        default=','.join([nm for fn, nm in available_mappings]),
                        help="Port-mapping algorithms to use, comma separated.")


    args = parser.parse_args()

    ofmt = ''
    ofmt += "b=%d"
    ofmt += ','
    ofmt += "w=%04d_%04d"
    ofmt += ','
    ofmt += "a=%+0.0f_%+0.0f" % (args.amin, args.amax)
    ofmt += ','
    ofmt += "z=(%s)" % args.algorithms
    ofmt += ".yml"

    N_INs = range(args.wmin, args.wmax+1)
    bases = range(args.bmin, args.bmax+1)
    for b in bases:
        wlo = args.wmin
        whi = min(args.wmax, wlo+args.wbatch-1)
        while wlo <= args.wmax:
            filename = ofmt % (b, wlo, whi)

            cmd = "./treebalance.py"
            cmd += " -d"
            cmd += " -o '%s'" % filename
            cmd += " --alpha3d"
            cmd += " --alen %d" % args.alen
            cmd += " --amin %0.0f" % args.amin
            cmd += " --amax %0.0f" % args.amax
            cmd += " -b %d" % b
            cmd += " --wmin %d" % wlo
            cmd += " --wmax %d" % whi
            print(cmd)
            os.system(cmd)

            wlo += args.wbatch
            whi += min(args.wbatch, args.wmax-whi)

# }}} main
