#!/usr/bin/env python

# Dave McEwan 2019-08-13
#
# Run like:
#    vcd-utils info    FILEPATH.vcd [options]
#   OR
#    vcd-utils clean   FILEPATH.vcd [options]
#   OR
#    vcd-utils vcd2csv FILEPATH.vcd [options]
#   OR
#    vcd-utils csv2vcd FILEPATH.csv [options]
#
# Or use the YAML representation to diff, or make minor edits.
#    vcd-utils vcd2yml FILEPATH.vcd
# ... Diff against another .yml here...
# ... Make edits to .yml here, then, assuming PyYAML can read it in...
#    vcd-utils yml2vcd FILEPATH.vcd

# Dev notes:
#   Run fast like:
#     python3 -OO vcd-utils vcd2csv FILEPATH.vcd
#   Profile like:
#     vcd-utils --profile vcd2csv FILEPATH.vcd

from __future__ import print_function

import argparse
import re
import sys
import tempfile
import shutil

from dmppl.base import fnameAppendExt, rdLines, run, verb
from dmppl.vcd import VcdReader, VcdWriter, \
    fourStates, fourStateTypes, supportedTypes, twoStateTypes, \
    detypeVarName, vcdClean

__version__ = "0.1.0"

noneCsvStr = '-' # Unknown value or non-occurrence.
occurCsvStr = '*' # Event occurrence

def info(src, showTime): # {{{
    fnamei = fnameAppendExt(src, "vcd")

    verb("Opening file and reading header...", end='')
    with VcdReader(fnamei) as vd:
        verb("DONE")

        print("__version__", __version__)
        print("filename", vd.filename)

        vs = zip(vd.varIds, vd.varNames, vd.varSizes, vd.varTypes)
        print("<id> <name> <size> <type>:")
        for varId,varName,varSize,varType in vs:
            print(" ", varId, varName, varSize, varType)

        if showTime:
            print("<timechunkNumber> <#changes> <time>:")
            for i,tc in enumerate(vd.timechunks, start=1):
                newTime, changedVarIds, newValues = tc

                print(" ", i, len(changedVarIds), newTime)

    return 0
# }}} def info

def vcd2csv(src, delimiter): # {{{
    import csv

    fnamei = fnameAppendExt(src, "vcd")
    fnameo = fnameAppendExt(src, "csv")

    def vcdToCsvField(v, varSize, varType): # {{{
    #def vcdToCsvField(v: str, varSize: int, varType: str) -> str:
        # NOTE: Most execution time is spent here.

        assert 0 <= varSize

        if "event" == varType:
            ret = None # Events have no value.
        elif v is None:
            ret = noneCsvStr
        elif "real" == varType:
            ret = "%0.06f" % float(v) # Ensure roundtripping capability.
        elif "string" == varType:
            ret = v # GtkWave support only for string type.
        elif 1 == varSize:
            v = v.lower()
            assert v in fourStates
            ret = v # Single bits printed as-is.
        elif varType in supportedTypes:
            assert 1 < varSize, varSize
            v = v.lower()

            # Multi-bits attempt to print in hex.
            # But if there are X's or Z's then print as-is.
            assert all(c in fourStates for c in v)
            if 'x' in v or 'z' in v:
                ret = "0b" + v
            else:
                ret = hex(int(v, 2))
        else:
            assert False, varType

        return ret
    # }}} def vcdToCsvField

    # NOTE: Python3/csv requires open(..., newline='') which is not supported
    # in Python2, and Python2/csv requires open(, 'wb') which gives a bytes
    # object not supported in Python3.
    openCsvKwargs = {"mode": 'w', "newline": ''} \
                    if 2 < sys.version_info[0] else \
                    {"mode": 'wb'}
    with VcdReader(fnamei) as vd, \
         open(fnameo, **openCsvKwargs) as fdo:

        # Only create columns for unique varIds.
        varIds = vd.varIdsUnique
        varTypes    = [vd.mapVarIdToType[v]     for v in varIds]
        varSizes    = [vd.mapVarIdToSize[v]     for v in varIds]
        varNamesDt  = [detypeVarName(vd.mapVarIdToNames[v][0]) for v in varIds]
        nSrc = len(varIds)

        writer = csv.writer(fdo, delimiter=delimiter)

        # First line is types.
        # Second line is name/titles.
        writer.writerow(["Time"] + ["%s/%d" % (t,s) \
                                    for t,s in zip(varTypes, varSizes)])
        writer.writerow(["vcdTime"] + varNamesDt)

        # Initialize values to None/null/nothing/Unknown/undefined.
        prevValues = [None]*nSrc

        for tc in vd.timechunks:
            newTime, changedVarIds, newValues = tc

            # Get values for all fields, not just the ones which have been
            # updated in this timechunk.
            fieldValues = \
                [prevValues[i] if varId not in changedVarIds else \
                 newValues[changedVarIds.index(varId)] \
                 for i,varId in enumerate(varIds)]

            assert len(varIds) == len(fieldValues)

            _valIter = zip(fieldValues, varIds, varSizes, varTypes)
            fieldStrings = \
                [vcdToCsvField(v, varSize, varType) \
                    if "event" != varType else \
                    (occurCsvStr if varId in changedVarIds else noneCsvStr) \
                 for v,varId,varSize,varType in _valIter]

            writer.writerow([str(newTime)] + fieldStrings)
            prevValues = fieldValues

    return 0
# }}} def vcd2csv

def csv2vcd(src, delimiter, no_names, bit_types, time_mul): # {{{
    import csv

    def intStrToBin(i): # {{{
    #def intBin(i: str) -> str:

        if i.startswith("0b"):
            intVal = int(i, 2)
        elif i.startswith("0x"):
            intVal = int(i, 16)
        else:
            intVal = int(i, 10)

        return bin(intVal)[2:]
    # }}} def intBin

    def csvFieldToVcd(f, s, t): # {{{
    #def csvFieldToVcd(f: str, s: VarSize, t: VarType) \
    #    -> Optional[str]:

        trState2 = {
            '0':        '0',
            'f':        '0',
            "false":    '0',
            'n':        '0',
            "no":       '0',
            '1':        '1',
            't':        '1',
            "true":     '1',
            'y':        '1',
            "yes":      '1',
        }
        trState4 = {
            '2':        'x',
            'x':        'x',
            "unknown":  'x',
            "neither":  'x',
            '3':        'z',
            'z':        'z',
            "highz":    'z',
            "both":     'z',
        }
        trState4.update(trState2)

        if f in ['', None, noneCsvStr]:
            return None
        elif "event" == t:
            return occurCsvStr if occurCsvStr == f else None
        elif t in twoStateTypes:
            return trState2[f.lower()] if 1 == s else intStrToBin(f)
        elif t in fourStateTypes:
            return trState4[f.lower()] if 1 == s else f.lower()
        elif t in ["integer", "parameter"]:
            return intStrToBin(f)
        elif "real" == t:
            return float(f)
        elif "string" == t:
            return str(f)
        else:
            assert False, t
            return None
    # }}} def csvFieldToVcd

    def mkHeader(colTypes, colNames): # {{{
    #def mkHeader(colTypes: List[str], colNames: List[str]) \
    #    -> Tuple[Header, List[VarType], List[int]]:

        #colVarTypes: List[str] = \
        colVarTypes = [t.split('/')[0] for t in colTypes]

        #colIsSrc: List[bool] = \
        colIsSrc = \
            [(t in supportedTypes) for t in colVarTypes]

        #varNames: List[VarName] = \
        varNames = \
            [nm for nm,isSrc in zip(colNames, colIsSrc) if isSrc]

        #varSizes: List[VarSize] = \
        varSizes = \
            [int(t.split('/')[1]) \
             for t,isSrc in zip(colTypes, colIsSrc) if isSrc]

        #varTypes: List[VarType] = \
        varTypes = \
            [t for t,isSrc in zip(colVarTypes, colIsSrc) if isSrc]

        #varCols: List[int] = \
        varCols = [i for i,isSrc in enumerate(colIsSrc) if isSrc]
        assert len(varTypes) == len(varNames)
        assert len(varTypes) == len(varCols)

        #h: Header = (
        h = (
            varNames,
            varSizes,
            varTypes,
        )
        return h, varCols
    # }}} def mkHeader

    def mkTimechunk(newTime, prevRow, row, h, varIds, varCols): # {{{
    #def mkTimechunk(newTime: int,
    #                prevRow: List[str],
    #                row: List[str],
    #                varTypes: List[VarType],
    #                varCols: List[int]):
        _, varSizes, varTypes = h

        #prevRowData: List[Optional[str]] = \
        prevRowData = \
            [csvFieldToVcd(prevRow[c],s,t) for c,s,t in zip(varCols, varSizes, varTypes)]

        #rowData: List[Optional[str]] = \
        rowData = \
            [csvFieldToVcd(row[c],s,t) for c,s,t in zip(varCols, varSizes, varTypes)]

        #changedVarIds: List[VarId] = \
        changedVarIds = \
            [i for p,r,i,t in zip(prevRowData, rowData, varIds, varTypes) \
             if ("event" != t and p != r) or \
                ("event" == t and occurCsvStr == r)]

        newValues = \
            tuple([r for r,i,t in zip(rowData, varIds, varTypes) \
                   if i in changedVarIds])

        tc = (
            newTime,
            changedVarIds,
            newValues,
        )
        return tc
    # }}} def mkTimechunk

    fnamei = fnameAppendExt(src, "csv")
    fnameo = fnameAppendExt(src, "vcd")

    # Manipulate constant in VCD module for type convenience.
    # Relies on (t in twoStateTypes) being tested first in csvFieldToVcd.
    for t in bit_types:
        assert t in supportedTypes
        twoStateTypes.append(t)

    # Ignore columns by giving them None type.
    # Specify one column to use as time with Time type, otherwise rowNum is
    # used for calculating time.
    colTypeNames = supportedTypes + ["Time", "None"]

    reader = csv.reader(rdLines(fnamei, expandTabs=False), delimiter=delimiter)
    with VcdWriter(fnameo) as vd:

        for rowNum,row in enumerate(reader):

            # Take first line as type description.
            if 0 == rowNum:
                # Check column types are usable.
                #colTypes: List[str] = row
                colTypes = row
                assert all((c.split('/')[0] in colTypeNames) for c in row), \
                    (row, colTypeNames)
                n_col = len(row)

                assert 2 > row.count("Time"), "Only 1 time column allowed."
                timeCol = row.index("Time") if "Time" in row else None

                prevRow = [None]*n_col

                # Auto-assign source names.
                # Sources are allocated IDs in column order.
                if no_names:
                    #colNames: List[str] = ["col%d" % i for i in range(n_col)]
                    colNames = ["col%d" % i for i in range(n_col)]

                    # Calculate VCD header information.
                    h, varCols = mkHeader(colTypes, colNames)

                    #varlist: Varlist = list(zip(*h))
                    varlist = list(zip(*h))
                    vd.wrHeader(varlist)

                continue
            elif 1 == rowNum and not no_names:
                # Take names from this row.
                #colNames: List[str] = list(row)
                colNames = list(row)
                assert len(colNames) >= len(colTypes)

                # Calculate VCD header information.
                h, varCols = mkHeader(colTypes, colNames)

                #varlist: Varlist = list(zip(*h))
                varlist = list(zip(*h))
                vd.wrHeader(varlist)
                continue
            else:
                pass # No continue to avoid indent.

            # Give row and varCols, get list of (id, newvalue)
            newTime = int(float(row[timeCol]) * time_mul) \
                if timeCol is not None else \
                (rowNum - (1 if no_names else 2))

            tc = mkTimechunk(newTime, prevRow, row, h, vd.varIds, varCols)
            prevRow = row
            vd.wrTimechunk(tc)

    return 0
    # }}} def csv2vcd

def vcd2yml(src): # {{{
    import math
    import yaml

    fnamei = fnameAppendExt(src, "vcd")
    fnameo = fnameAppendExt(src, "yml")

    def ymlStrEscape(s):
        assert isinstance(s, str), (type(s), s)
        return yaml.safe_dump(s, default_style='"')[:-1]

    with VcdReader(fnamei) as vd, \
         open(fnameo, 'w') as fdo:
        print("# Generated by vcd2yml %s" % __version__, file=fdo)

        print("varlist:", file=fdo)
        usedVarIds = []
        aliasVarStrs = []
        for i,n,s,t in zip(vd.varIds, vd.varNames, vd.varSizes, vd.varTypes):
            i_ = ymlStrEscape(i)
            n_ = ymlStrEscape(n)

            if i not in usedVarIds:
                usedVarIds.append(i)
                varStr = "  - [%s, %d, %s, %s]" % (n_, s, t, i_)
                print(varStr, file=fdo)
            else:
                r = ymlStrEscape(vd.mapVarIdToNames[i][0])
                aliasStr = "  - [%s, %s, %s]" % (r, n_, t)
                aliasVarStrs.append(aliasStr)

        print("varaliases:", file=fdo)
        for s in aliasVarStrs:
            print(s, file=fdo)

        print("timechunks:", file=fdo)
        for tc in vd.timechunks:
            newTime, changedIds, newValues = tc

            print("  %d:" % newTime, file=fdo)
            for i, v in zip(changedIds, newValues):

                if v is None: # event
                    s = occurCsvStr
                elif isinstance(v, int):
                    s = str(v)
                elif isinstance(v, float):
                    if math.isnan(v) or math.isinf(v):
                        s = ymlStrEscape(v)
                    else:
                        s = str(v)
                elif isinstance(v, str):
                    s = ymlStrEscape(v)
                else:
                    assert False, (type(v), v)

                print("    - [%s, %s]" % (ymlStrEscape(i), s), file=fdo)

    return 0
# }}} def vcd2yml

def yml2vcd(src): # {{{
    import yaml

    fnamei = fnameAppendExt(src, "yml")
    fnameo = fnameAppendExt(src, "vcd")

    with open(fnamei, 'r') as fdi, \
         VcdWriter(fnameo) as vd:

        # Read in entire YAML document to memory.
        # NOTE: This may explode and is not implemented efficiently like
        # the custom dumper in vcd2yml().
        y = yaml.safe_load(fdi)

        varlist = [v[:3] for v in y["varlist"]]
        varaliases = y["varaliases"]
        vd.wrHeader(varlist, varaliases=varaliases)

        yVarIdsUnique = [v[3] for v in y["varlist"]]
        vVarIdsUnique = vd.varIdsUnique
        mapYToV = {y: v for y,v in zip(yVarIdsUnique, vVarIdsUnique)}

        timechunks = [] if y["timechunks"] is None else y["timechunks"]

        for newTime,changes in timechunks.items():
            changedYVarIds, newValues = list(zip(*changes))
            changedVarIds = [mapYToV[i] for i in changedYVarIds]

            #tc: Timechunk = \
            tc = (
                newTime,
                changedVarIds,
                newValues,
            )
            vd.wrTimechunk(tc)

    return 0 # }}} yml2vch

# {{{ argparser
argparser = argparse.ArgumentParser(
    description = "vcd-utils - Value Change Dump (Verilog IEEE1364) utilities.",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

#subparsers = argparser.add_subparsers(dest="command", required=True) # Python3.7+
subparsers = argparser.add_subparsers(dest="command") # Python2.7+
subparsers.required = True

argparser.add_argument("input",
    nargs=1,
    type=str,
    help=("Input file."
    " Output file (CSV, VCD, YML) will have matching name except for the"
    " file extension."
    " E.g. 1) 'vcd-utils vcd2csv foo' will take 'foo.vcd' as input and give"
    " 'foo.csv' as output."
    " E.g. 2) 'vcd-utils vcd2csv bar.vcd' will take 'bar.vcd' as input and give"
    " 'bar.vcd.csv' as output."))

argparser_info = subparsers.add_parser("info",
    help=("Print information about VCD file."))
argparser_info.add_argument("-t", "--time",
    default=False,
    action='store_true',
    help="Read through entire file printing time information.")

argparser_clean = subparsers.add_parser("clean",
    help=("Clean a VCD file. foo.vcd --> foo.clean.vcd"))

argparser_vcd2yml = subparsers.add_parser("vcd2yml",
    help=("Convert VCD to YAML. Best for diffing. foo.vcd -> foo.yml"))

argparser_yml2vcd = subparsers.add_parser("yml2vcd",
    help=("Convert YAML to VCD. foo.yml -> foo.vcd"))

argparser_vcd2csv = subparsers.add_parser("vcd2csv",
    help=("Convert VCD to Comma Separated Values. foo.vcd -> foo.csv"))
argparser_vcd2csv.add_argument("-d", "--delimiter",
    type=str,
    default=',',
    help="String separating columns.")

argparser_csv2vcd = subparsers.add_parser("csv2vcd",
    help=("Convert Comma Separated Values to VCD. foo.csv -> foo.vcd"))
argparser_csv2vcd.add_argument("-d", "--delimiter",
    type=str,
    default=',',
    help="String separating columns.")
argparser_csv2vcd.add_argument("--no-names",
    default=False,
    action='store_true',
    help="Second non-comment row is not source name/titles.")
argparser_csv2vcd.add_argument("-2", "--bit-types",
    type=str,
    default=["reg", "logic"], # Treat wire as 4s by default.
    choices=["reg", "logic", "wire"],
    nargs='*',
    help="Four state VCD types to treat as binary, allow values in hex, and decimal.")
argparser_csv2vcd.add_argument("-t", "--time-mul",
    type=float,
    default=1.0,
    help="Time multiplier.")

# }}} argparser

def main(args): # {{{

    src = args.input[0] # Force to single element

    if "info" == args.command:
        ret = info(src, args.time)
    elif "clean" == args.command:
        dst = fnameAppendExt(src, "clean.vcd")
        cleanComment = "<<< Cleaned by vcd-utils %s >>>" % __version__
        ret = vcdClean(src, dst, comment=cleanComment)
    elif "vcd2csv" == args.command:
        ret = vcd2csv(src, args.delimiter)
    elif "csv2vcd" == args.command:
        ret = csv2vcd(src, args.delimiter,
                      args.no_names, args.bit_types, args.time_mul)
    elif "vcd2yml" == args.command:
        ret = vcd2yml(src)
    elif "yml2vcd" == args.command:
        ret = yml2vcd(src)
    else:
        assert False

    return ret
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

