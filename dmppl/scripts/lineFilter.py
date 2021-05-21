#!/usr/bin/env python3

# lineFilter
# Dave McEwan 2020-10-03
#
# Take lines from STDIN, filter out lines, and print remaining lines on STDOUT.
# Run like:
#    cat foo.txt | python lineFilter.py fileOfRegexs > bar.txt
#
# mypy --ignore-missing-imports lineFilter.py

# Standard library
import argparse
import re
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, \
    Tuple, Union, cast

# git clone https://github.com/DaveMcEwan/dmppl.git && pip install -e ./dmppl
from dmppl.base import run, verb, dbg, \
    rdLines

__version__ = "0.1.0"

# {{{ argparser

argparser = argparse.ArgumentParser(
    description = \
        ("Take lines from STDIN,"
        " filter out lines according to a set of regexs,"
        " then print remaining lines on STDOUT."),
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("-t", "--expand-tabs",
    action="store_true",
    help="Expand tab characters in input to 1..8 spaces each.")

argparser.add_argument("-s", "--deduplicate-spaces",
    action="store_true",
    help="Deduplicate spaces in input. Applied after optional tab expansion.")

argparser.add_argument("-l", "--left-strip",
    action="store_true",
    help="Remove leading whitespace from input lines.")

argparser.add_argument("-r", "--right-strip",
    action="store_true",
    help="Remove trailing whitespace from input lines.")

argparser.add_argument("-c", "--case-fold",
    action="store_true",
    help="Convert input lines to lower case.")

argparser.add_argument("-i", "--invert-match",
    action="store_true",
    help="Print lines which *do* match a filter.")

argparser.add_argument("filterFile",
    type=str,
    nargs='?',
    default="lineFilter.regex",
    help="Text file containing one regex per line."
         " Input lines matching any given regex are filtered from output."
         " Lines beginning with '#' are ignored.")

# }}} argparser

def main(args) -> int: # {{{
    '''
    1. Read in all regexs and precompile filters into memory.
    2. Read STDIN line by line.
    3. If line does not match any regex then print on STDOUT.
    '''

    verb("Reading and compiling regex filters ...", end='')
    regexLines:Iterable = \
        rdLines(args.filterFile,
                commentLines=True,
                commentMark='#',
                expandTabs=True,
                deduplicateSpaces=True,
                leftStrip=True,
                rightStrip=True,
                caseFold=False,
                raiseIOError=True)
    regexes:List = [re.compile(line) for line in regexLines if len(line) > 0]
    verb("Done")

    verb("Opening STDIN with optional whitespace preprocessing ...", end='')
    inputLines:Iterable = \
        rdLines(None, # STDIN
                commentLines=False,
                expandTabs=args.expand_tabs,
                deduplicateSpaces=args.deduplicate_spaces,
                leftStrip=args.left_strip,
                rightStrip=args.right_strip,
                caseFold=args.case_fold)
    verb("Done")

    verb("Filtering ...", end='')
    for line in inputLines:
        reMatch:bool = any(r.search(line) for r in regexes)

        if reMatch == args.invert_match:
            print(line, end='')
    verb("Done")

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

