#!/usr/bin/env python

# Use Inkscape to export SVG files to PNG.
# Dave McEwan 2019-11-15
#
# Run like:
#    svg2png hello.svg world.svg
# This will create/overwrite two files hello.png and world.png

import argparse
import subprocess

from dmppl.base import *

__version__ = "0.1.0"

# {{{ argparser

argparser = argparse.ArgumentParser(
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("--dpi",
    type=int,
    default=300,
    help="Resolution (Dots Per Inch)")

argparser.add_argument("--background",
    type=str,
    default="white",
    help="Background color")

argparser.add_argument("filenames",
    nargs='+',
    type=str,
    help="SVG filenames to convert.")

# }}} argparser

def main(args): # {{{

    fnameis = [fnameAppendExt(f, "svg") for f in args.filenames]
    fnameos = [fnameAppendExt(fnameStripExt(f, "svg"), "png") for f in fnameis]

    for fnamei,fnameo in zip(fnameis, fnameos):
        verb("Converting %s..." % fnamei, end='', sv_tm=True)

        cmd = (
            "inkscape",
            "--without-gui",
            "--export-area-drawing",
            "--export-background=%s" % args.background,
            "--export-dpi=%d" % args.dpi,
            "--export-png=%s" % fnameo,
            fnamei,
        )

        status = subprocess.run(cmd, capture_output=True).returncode

        verb(("FAIL:%d" % status) if 0 != status else "Done", rpt_tm=True)

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
