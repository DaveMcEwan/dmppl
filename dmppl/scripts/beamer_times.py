#!/usr/bin/env python

# Beamer/LaTeX Time Reporter
# Dave McEwan 2019-09-06
#
# Run like:
#    beamer-times main.tex -o main.tex.times
#    OR
#    cat main.tex | beamer-times > main.tex.times
#
# Read in TeX, extract lines containing "\frametitle" which are annotated with
# the expected speaking time, and print a report of the times.
# This is intended to help plan and practice presentations.
#
# Assume time per frame/slide are precalculated and annotated.
# Assume all times are in the same file.
# Assume line format:
#   \begin{frame} \frametitle{TITLE} % COMMENT XmXXs
#   where
#       TITLE is what appears at the top of the slide
#       COMMENT is optional, probably a fold marker of 3 '{'
#       Xs are decimal numbers

from __future__ import print_function

import argparse
import itertools
import re
import sys

from dmppl.base import *

__version__ = "0.1.0"

def getFrametitleLines(lines): # {{{
    '''Yield (title,minutes,seconds) if line is formatted correctly.

    Lines which don't have a time in the format XmXXs at the end are allowed
    since some slides don't actually consume time.
    '''
    r = re.compile(r".*\\frametitle{(?P<title>.*)}.*\s+"
                   r"(?P<minutes>(\d+|[Xx]+))m"
                   r"(?P<seconds>(\d+|[Xx]+))s")

    for line in lines:
        m = r.match(line)
        if m is not None:
            g = m.groupdict()
            yield (g["title"], g["minutes"], g["seconds"])

# }}} def getFrametitleLines

# {{{ argparser

argparser = argparse.ArgumentParser(
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("-o", "--output",
    nargs=1,
    type=str,
    help="Output file, or STDOUT if None.")

argparser.add_argument("input",
    nargs='*',
    type=str,
    help="Beamer/LaTeX file, or STDIN if None.")

# }}} argparser

def main(args): # {{{

    # Read in one line at a time and filter out everything except lines with
    # expected format containing.
    lines = getFrametitleLines(rdLines(args.input, commentMark='%'))

    # Output times report to stream from argparse.
    fd = open(args.output[0], 'w') if args.output else sys.stdout
    try:
        print("#  Slide  Finish  Title", file=fd)
        #     "NN XXmXXs XXXmXXs Lorem Ipsum Decorum Est"

        start = 0 # Track start time as previous finish time in whole seconds.
        for i,(t,m,s) in enumerate(lines, start=1):
            try:
                m_, s_ = int(m), int(s)
            except:
                m_, s_ = 0, 0

            duration = s_ + 60*m_
            finish = duration + start

            d = divmod(duration, 60)
            f = divmod(finish, 60)

            fmtargs = [i] + list(d) + list(f) + [t]
            row = "{:<2d} {:2d}m{:02d}s {:3d}m{:02d}s {}".format(*fmtargs)
            print(row, file=fd)

            start = finish
    finally:
        fd.close()

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
