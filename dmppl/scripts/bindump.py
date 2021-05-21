#!/usr/bin/env python

# Dave McEwan 2021-05-13
# Simple binary dumper, which is a bit more convenient than hexdump,od,xxd.
# All printed fields are valid Python expressions.
#
# Run like:
#    bindump [options] <filepath>
#
# E.g. To print numbered little-endian (LSByte first) 32-bit unsigned integers:
#   bindump -ne -f u32  myfile
#
# E.g. To print unnumbered big-endian (MSByte first) 16-bit signed integers:
#   bindump -n -f i16  myfile
#
# E.g. To print binary values of each byte index:
#   bindump -nwfb8  myfile

from __future__ import print_function

import argparse
import functools
import struct
import sys

from dmppl.base import run, argparse_positiveInteger

__version__ = "0.1.0"

mapFormatToStructFmt = {
    "b8": 'B',  "b16": 'H',  "b32": 'I',  "b64": 'Q', # Binary
    "x8": 'B',  "x16": 'H',  "x32": 'I',  "x64": 'Q', # Hexadecimal
    "u8": 'B',  "u16": 'H',  "u32": 'I',  "u64": 'Q', # Decimal unsigned
    "i8": 'b',  "i16": 'h',  "i32": 'i',  "i64": 'q', # Decimal signed
                "f16": 'e',  "f32": 'f',  "f64": 'd', # Decimal float
}

# {{{ argparser
argparser = argparse.ArgumentParser(
    description = "bindump - Binary dump in numerical formats.",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("-e", "--little-endian",
    default=False,
    action='store_true',
    help="Little-endian (least significant byte first).")

argparser.add_argument("-f",
    type=str,
    choices=list(mapFormatToStructFmt.keys()),
    default='x8',
    help="Numerical format.")

argparser.add_argument("-n", "--index-numbers",
    default=False,
    action='store_true',
    help="Prefix each output line with index, starting at 0.")

argparser.add_argument("-s", "--stride",
    type=functools.partial(argparse_positiveInteger, "stride"),
    default=1,
    help="Number of values to print per line.")

argparser.add_argument("-w", "--wide",
    default=False,
    action='store_true',
    help="Print full width of binary or hexadecimal values.")

argparser.add_argument("input",
    nargs=1,
    type=str,
    help="Input filepath.")
# }}} argparser

def main(args): # {{{
    fBase = args.f[0]
    assert fBase in ('b', 'x', 'u', 'i', 'f'), fBase

    structFmt = ('>' if args.little_endian else '<') + \
        mapFormatToStructFmt[args.f]

    fWidthBits = int(args.f[1:])
    bitFmt = ''.join((
        '0',
        fBase,
        '{:',
        '0' if args.wide else '',
        str(fWidthBits if 'b' == fBase else fWidthBits // 4) \
            if args.wide else '',
        fBase,
        '}',
    ))

    with open(args.input[0], 'rb') as fd:
        for i,value in enumerate(struct.iter_unpack(structFmt, fd.read())):
            if args.index_numbers and 0 == (i % args.stride):
                print(i, end=' ')

            fn = bitFmt.format if fBase in ('b', 'x') else repr
            print(fn(value[0]),
                  end='\n' if args.stride == (i % args.stride + 1) else ' ')

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

