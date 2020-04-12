#!/usr/bin/env python

# Parameter Vector Generator
# Dave McEwan 2017-10-25
#
# Run like:
#    parvec tst.yml -o tst.out
#    OR
#    cat tst.yml | parvec - > tst.out
#
# Dollars in name are substituted with *init* lists/ranges.
# Value is chosen randomly from the *last* list/range.
# Format dict may be at any location.
#
# Ranges specified like python range(<start>, <stop>[, <step>])
# <start> .. <stop> [ .. <step>]
#
# Format dict may have contain values shows by --help:
#   "fmt", "pre-name", "post-name", "pre-value", "post-value"
#
# This script is intended to be called multiple times, e.g. call 10 times to
# get 10 sets of parameters.

from __future__ import print_function

import argparse
import fileinput
import itertools
import random
import re
import sys

import yaml

from dmppl.base import run
from dmppl.yaml import loadYml, saveYml, yamlMarkedLoad

if 2 < sys.version_info[0]:
    long = int

__version__ = "0.1.0"

class ParvecCheckError(Exception): # {{{
    '''Generic format check error.
    '''
    def prefix(self):
        classname = self.__class__.__name__
        docstring = self.__doc__.rstrip()
        return '%s:\n%s' % (classname, docstring)

    def __init__(self):
        self.msg = ''

    def __str__(self):
        return self.prefix() + self.msg

class ParvecCheckError_YamlLoad(ParvecCheckError):
    '''YAML syntax error.
    '''
    def __init__(self, e):
        srcline = e.problem_mark.line + 1
        srccol = e.problem_mark.column + 1
        snippet = e.problem_mark.get_snippet()

        self.msg = '''
%s: line %d, column %d
%s
''' % (e.problem, srcline, srccol, snippet)

class ParvecCheckError_YamlTopDict(ParvecCheckError):
    '''Parameter names must be dict/map.
    '''
    def __init__(self):
        self.msg = '''
Have you missed a colon?
E.g.
    # This is good.
    foo:
        ...

    # This is bad.
    foo
        ...
'''

class ParvecCheckError_NumSubConstraints(ParvecCheckError):
    '''Wrong number of substitution constraints.
    '''
    def __init__(self, data, name, n_expected, n_got):
        srcline = data.start_mark.line + 1
        srccol = data.start_mark.column + 1

        self.msg = '''
The parameter "%s" (line %d, column %d) expects %d dollar substituions, \
plus 1 value constraint, but found %d.
''' % (name, srcline, srccol, n_expected, n_got)

class ParvecCheckError_DataType(ParvecCheckError):
    '''Data is wrong type.
    '''
    def __init__(self, data, expected):
        srcline = data.start_mark.line + 1
        srccol = data.start_mark.column + 1

        # marked_yaml adds the _node suffix to its subclassed types.
        found = str(type(data).__name__).replace('_node', '')

        assert type(expected) in [type, list, type(None)]
        if expected is None:
            expect_str = '"None"'
        elif isinstance(expected, list):
            expect_str = 'one of "%s"' % \
                '", "'.join([e.__name__ if e is not None else 'None' \
                             for e in expected])
        else:
            expect_str = '"%s"' % expected.__name__

        data_str = 'null' if isinstance(data, none_node) else str(data)

        self.msg = '''
The data "%s" (line %d, column %d) is type "%s" but is expected to be %s.
''' % (data_str, srcline, srccol, found, expect_str)

class ParvecCheckError_DataValue(ParvecCheckError):
    '''Data is unexpected value.
    '''
    def __init__(self, data, expected):
        srcline = data.start_mark.line + 1
        srccol = data.start_mark.column + 1

        expect_str = 'one of "%s"' % '", "'.join(expected)

        self.msg = '''
The data "%s" (line %d, column %d) should be one of %s.
''' % (data, srcline, srccol, expect_str)

class ParvecCheckError_DataFormat(ParvecCheckError):
    '''Data is in wrong format.
    '''
    def __init__(self, data, example=''):
        srcline = data.start_mark.line + 1
        srccol = data.start_mark.column + 1

        if len(example):
            example = 'E.g.\n%s' % example
        self.msg = '''
The data "%s" (line %d, column %d) does not match the specified format.
%s
''' % (data, srcline, srccol, example)

# }}} ParvecCheckError

def checkType(data, expected): # {{{
    '''Check user format data node is expected type.

    A list of multiple expected types may be given, or just one type.
    '''
    assert type(expected) in [type, list, type(None)]

    if expected is None:
        ok = isinstance(data, none_node)
    elif isinstance(expected, list):
        ok = True in [isinstance(data, e) if e is not None else \
                         isinstance(data, none_node) \
                         for e in expected]
    else:
        ok = isinstance(data, expected)

    if not ok:
        raise ParvecCheckError_DataType(data, expected)
# }}} def checkType

def checkValue(data, expected): # {{{
    '''Check data node is expected one of a list of expected values.
    '''
    assert isinstance(expected, list)

    if data not in expected:
        raise ParvecCheckError_DataValue(data, expected)
# }}} def checkValue

def checkYmlDsl(infmt): # {{{
    '''Raise an exception if infmt is not formatted correctly.
    '''

    # <start>..<stop> [.. <step>]
    range_re = re.compile(r'[+-]?\d+\s*\.\.\s*[+-]?\d+\s*(\.\.\s*[+-]?\d+)?$')

    if not isinstance(infmt, dict):
        raise ParvecCheckError_YamlTopDict()

    for name, data in infmt.items():

        checkType(name, str)
        checkType(data, list)

        nSubs = name.count('$')
        nConstraints = len([x for x in data if not isinstance(x, dict)])

        if nConstraints != nSubs+1:
            raise ParvecCheckError_NumSubConstraints(data,
                                                     name,
                                                     nSubs,
                                                     nConstraints)

        for d in data:
            checkType(d, [list, str, dict])

            if isinstance(d, str):
                if not range_re.match(d):
                    eg = "<start> .. <stop> [.. <step>]"
                    raise ParvecCheckError_DataFormat(d, eg)
            elif isinstance(d, list):
                for c in d:
                    checkType(c, [str, int, long])
            elif isinstance(d, dict):
                for key in d:
                    checkType(key, str)
                    checkType(d[key], str)
                    checkValue(key, ["fmt",
                                     "pre-name",
                                     "post-name",
                                     "pre-value",
                                     "post-value"])
            else:
                raise ParvecCheckError_DataType(d, [str, list, dict])

    return
# }}} def checkYmlDsl

def processYmlDsl(infmt, args): # {{{
    '''Generate lines of parameter file to be output.
    '''

    def getSubstitutionList(x):
        if isinstance(x, str):
            x_ = re.sub(r"\s+", '', x) # rm whitespace
            try:
                start, stop, step = x_.split("..")
                return range(int(start), int(stop), int(step))
            except:
                start, stop = x_.split("..")
                return range(int(start), int(stop))
        else:
            assert isinstance(x, list)
            return sorted(x)

    paramParts = {
        "fmt":          args.fmt,
        "pre-name":     args.pre_name,
        "post-name":    args.post_name,
        "name":         None,
        "pre-value":    args.pre_value,
        "value":        None,
        "post-value":   args.post_value,
    }

    random.seed(args.seed)

    for paramName in sorted(list(infmt.keys())):
        paramData = infmt[paramName]

        nSubs = paramName.count('$')
        assert len(paramData) in [nSubs + 1, nSubs + 2]

        # Initialise fmt specifiers from args.
        # This may be overridden per parameter.
        thisParts_ = {}
        thisParts_.update(paramParts)

        # fmt dict specified for this parameter.
        if len(paramData) == nSubs + 2:
            # Extract the last dict to be used as fmt specifiers.
            lastDict = paramData.pop(max([i for (i,x) in enumerate(paramData)
                                          if isinstance(x, dict)]))

            thisParts_.update(lastDict)


        # init paramData (Haskell terminology)
        nameLists = [getSubstitutionList(x) for x in paramData[:-1]]

        # last paramData (Haskell terminology)
        valList = getSubstitutionList(paramData[-1])


        for nmPart in itertools.product(*nameLists):
            paramName_ = paramName
            for s in range(nSubs):
                paramName_ = paramName_.replace('$', str(nmPart[s]), 1)

            thisParts_["name"] = paramName_
            thisParts_["value"] = random.choice(valList)

            yield (thisParts_["fmt"] % thisParts_)
# }}} def processYmlDsl

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
    help="YAML file, or STDIN if None, describing parameters in vector.")

argparser.add_argument("-s", "--seed",
    type=int,
    default=random.randint(0, 2**32-1),
    help="Seed for random selection."
    " Defaults to randomly generated integer.")

argparser.add_argument("--seed-fmt",
    type=str,
    default="// seed: %d",
    help="Output format for seed (1st line output).")

argparser.add_argument("--fmt",
    type=str,
    default="%(pre-name)s%(name)s%(post-name)s"
    "%(pre-value)s%(value)s%(post-value)s",
    help="Output format for each line.")

argparser.add_argument("--pre-name",
    type=str,
    default="`define ",
    help="String before parameter name.")

argparser.add_argument("--post-name",
    type=str,
    default=" ",
    help="String after parameter name.")

argparser.add_argument("--pre-value",
    type=str,
    default="",
    help="String before chosen value.")

argparser.add_argument("--post-value",
    type=str,
    default="",
    help="String after chosen value.")

# }}} argparser

def main(args): # {{{

    # Read entire input stream into memory from STDIN or files.
    # fileinput.input() context manager handles open/closing.
    instr = ''.join(line for line in fileinput.input(args.input))

    # Load input stream into a YAML object with marked nodes.
    try:
        infmt = yamlMarkedLoad(instr)
    except yaml.YAMLError as e:
        raise ParvecCheckError_YamlLoad(e)

    # Load YAML object into DSL parser.
    # If no exception is raised then assume input file is correctly
    # formatted.
    checkYmlDsl(infmt)

    # Output param vector to stream from argparse.
    fd = open(args.output[0], 'w') if args.output else sys.stdout
    try:
        print(args.seed_fmt % args.seed, file=fd)
        for line in processYmlDsl(infmt, args):
            print(line, file=fd)
    finally:
        fd.close()

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
