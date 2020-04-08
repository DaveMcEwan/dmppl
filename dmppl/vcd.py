
from __future__ import print_function

import re
import sys

# NOTE: No dependencies from outside the standard library.

# NOTE: For compatibility with Python2.7 type annotations are currently
# commented out.
#from typing import BinaryIO, Optional, List, Tuple, Union, Type # 3.6+
# NOTE: To run static type checking install and run mypy:
#   pip3 install --user mypy
#   mypy vcd.py
# VarId = str
# VarName = str
# VarSize = str
# VarType = str
#Header = Tuple[List[VarName], List[VarSize], List[VarType]]
#Varlist = List[Tuple[VarName, VarSize, VarType]]

# Timescale has only a few allowed values.
allowedtimeUnits = ["s", "ms", "us", "ns", "ps", "fs"]
allowedtimeNumbers = ["1", "10", "100"]
allowedScopeTypes = ["begin", "fork", "function", "module", "task"]

# NOTE: Extended VCD (port) is not supported.
v2001Types = ["event", "integer", "parameter", "real", "reg", "supply0",
    "supply1", "time", "tri", "triand", "trior", "trireg", "tri0", "tri1",
    "wand", "wire", "wor"]

# System Verilog (IEEE1800-2012) variable types supported despite not being in
# standard VCD since they're so similar to wire/reg.
# NOTE: string only supported by GtkWave
svTypes = ["bit", "logic"]
gtkwaveTypes = ["string"]

supportedTypes = v2001Types + svTypes + gtkwaveTypes

twoStateTypes = ["bit"]

fourStateTypes = ["reg", "supply0", "supply1", "tri", "triand", "trior",
    "trireg", "tri0", "tri1", "wand", "wire", "wor", "logic"]

fourStates = ['0', '1', 'x', 'z']

oneBitTypes = twoStateTypes + fourStateTypes

def intToVarId(x): # {{{
    assert type(x) is int
    assert x >= 0

    # Each variable is assigned an arbitrary, compact ASCII identifier for
    # use in the value change section. The identifier is composed of
    # printable ASCII characters from ! to ~ (decimal 33 to 126).
    numerals = ''.join(chr(i) for i in range(33, 127))
    base = len(numerals)

    if x == 0:
        return numerals[0]

    r = []
    while x:
        x, a = divmod(x, base)
        r.append(numerals[a])
    r.reverse()

    return ''.join(r)
# }}} def intToVarId

class VcdReader(object): # {{{
    def __init__(self, filename=None):
        self.filename = filename

    @staticmethod
    def vcdHeader(lines): # {{{
        '''Read VCD Header.
        '''

        # Take all lines up to $enddefinitions.
        # Treat header as a single string of tokens separated by whitespace.
        # NOTE: The same generator (lines) is used by vcdTimechunks.
        def getHeaderTokens(lines):
            line = ""
            while "$enddefinitions" not in line:
                try:
                  lineNum, line = next(lines)
                except StopIteration:
                    return

                for token in line.split():
                    yield token

        headerTokens = getHeaderTokens(lines)

        # Parse tokens with FSM to fill in header as IEEE1364-2001.
        header = {
            "comment"        : [],
            "date"           : [],
            "version"        : [],
            "timescales"     : [],
            "vars"           : [],
        }
        curCmd = None # Main FSM state keeper.
        curScope = [] # Secondary FSM state keeper.
        for token in headerTokens: # {{{ VCD header parsing FSM
            tokenLower = token.lower()

            if "$end" == tokenLower:
                curCmd = None
            elif curCmd is None:
                if   "$comment"        == tokenLower: curCmd = "comment"
                elif "$date"           == tokenLower: curCmd = "date"
                elif "$version"        == tokenLower: curCmd = "version"
                elif "$enddefinitions" == tokenLower: curCmd = "enddefinitions"
                elif "$scope"          == tokenLower:
                    curCmd = "scope"
                    # Take next 2 tokens as scopeType and scopeId.
                    # Ignore any further tokens for this command.

                    scopeType = next(headerTokens)
                    assert scopeType in allowedScopeTypes, \
                        "Unknown scope type <<<%s>>>" % scopeType

                    scopeId = next(headerTokens)

                    curScope.append((scopeType, scopeId))
                elif "$timescale" == tokenLower:
                    curCmd = "timescale"
                    # Take next 2 tokens as timeNumber and timeUnit.
                    # Ignore any further tokens for this command.

                    timeNumber_ = next(headerTokens)
                    if timeNumber_.endswith('s'): # Number/unit are joined.
                        timeNumber = timeNumber_.rstrip("smunpf")
                        timeUnit = timeNumber_.lstrip("01")
                    else: # Number/unit are separate.
                        timeNumber = timeNumber_
                        timeUnit = next(headerTokens)

                    assert timeNumber in allowedtimeNumbers, \
                        "Unknown time number <<<%s>>>" % timeNumber

                    assert timeUnit in allowedtimeUnits, \
                        "Unknown time unit <<<%s>>>" % timeUnit

                    header["timescales"].append((timeNumber, timeUnit))
                elif "$upscope" == tokenLower:
                    curCmd = "upscope"
                    # Immediately pop scope stack and ignore any further tokens.

                    curScope.pop()
                elif "$var" == tokenLower:
                    curCmd = "var"
                    # Take next 2 tokens as timeNumber and timeUnit.
                    # Ignore any further tokens for this command.
                    varType = next(headerTokens)
                    assert varType in supportedTypes, \
                        "Unknown var type <<<%s>>>" % varType

                    varSize_ = next(headerTokens)
                    varSize = int(varSize_, 10)

                    varId = next(headerTokens)

                    varName = next(headerTokens) # reference

                    # Bit select is optional next token so modify FSM.
                    # NOTE: No whitespace allowed in [msb:lsb] format.
                    x = next(headerTokens)
                    if "$end" == x:
                        varBitSel = None
                        curCmd = None
                    else:
                        varBitSel = x

                    # Order of this tuple is important for sorting later.
                    v = (varId, list(curScope), varName, varType, varSize, varBitSel)
                    header["vars"].append(v)
                else:
                    assert False, "Unknown keyword <<<%s>>>" % token
            elif curCmd in ["enddefinitions",
                            "scope",
                            "timescale",
                            "upscope",
                            "var"]:
                # Ignore further tokens as all the standard ones have been
                # taken and consumed already.
                pass
            elif curCmd in ["comment",
                            "date",
                            "version"]:
                # Keep appending tokens for these commands.
                header[curCmd].append(token)
            else:
                # Programming error only.
                assert False, "Unknown curCmd <<<%s>>>" % curCmd

        # }}} VCD header parsing FSM

        # Process abstract data from parsing into concrete values.
        vcdComment = ' '.join(header["comment"]) # Cat everything.
        vcdDate = ' '.join(header["date"])       # Cat everything.
        vcdVersion = ' '.join(header["version"]) # Cat everything.
        vcdTimescale = header["timescales"][-1]  # Ignore all but last.

        vcdVars = sorted(header["vars"])

        def vcdVarPath(varScope,
                       varName,
                       varType,
                       varBitSel):
        #def vcdVarPath(varScope: List[Tuple[str, str]],
        #               varName: str,
        #               varType: str,
        #               varBitSel: str) -> str:
            '''Get full dot-separated VCD var path.
            Scope types only stated where they change.
            '''
            prev_t = None
            s = []
            for t,n in varScope:
                if t != prev_t:
                    prev_t = t
                    s.append(t + ':' + n)
                else:
                    s.append(n)

            sizeSuffix = '' if varBitSel is None else varBitSel
            s.append(varName + sizeSuffix)

            return '.'.join(s)

        varIds, varTypes, varSizes, varNames = zip(*(
            (varId, varType, varSize, vcdVarPath(varScope,
                                                 varName,
                                                 varType,
                                                 varBitSel)) \
            for varId,varScope,varName,varType,varSize,varBitSel in vcdVars))

        #assert len(varIds) == len(varTypes) == len(varSizes) == len(varNames)
        h = (
            list(varIds),   # Non-unique short strings.
            list(varNames), # Full path strings. Should be unique.
            list(varSizes), # Integers.
            list(varTypes), # VCD types as strings.
            vcdComment,
            vcdDate,
            vcdVersion,
            vcdTimescale,
        )
        return h
    # }}} def vcdHeader

    @staticmethod
    def vcdTimechunks(self, lines): # {{{

        def procChangeLine(line): # {{{
            c0 = line[0].lower() if 0 < len(line) else ''

            if '#' == c0:
                timeNotData = True
                value = int(line[1:])
                varId = None
            elif 'b' == c0:
                # Multi-character (vector) value change.
                # Could be vector of wire, reg, etc, OR integer.
                timeNotData = False
                value, varId = line[1:].split()
            elif c0 in ['0', '1', 'x', 'z']:
                # Single-character (scalar) value change.
                # Only event, wire, reg, etc. Not integer or real.
                timeNotData = False
                value, varId = line[0], line[1:]
            elif 'r' == c0:
                timeNotData = False
                value, varId = line[1:].split()
            else:
                # Unknown type of change line.
                # Perhaps  a $comment, or the $end from $enddefinitions.
                timeNotData = None
                value = None
                varId = None

            return timeNotData, value, varId # }}} procChangeLine

        newTime = None # Initial value to read first timechunk.
        changedVarIds = []
        valueStrings = []
        prevTcLineNum_, prevTcTell_ = None, None
        for lineNum, line in lines:
            timeNotData, value, varId = \
                procChangeLine(line)

            if timeNotData:
                self.tcLineNum_, self.tcTell_ = prevTcLineNum_, prevTcTell_
                prevTcLineNum_ = lineNum
                try:
                    prevTcTell_ = self.fd.tell()
                except:
                    pass # Ignore lack of tell() on STDIN

            if (timeNotData, value, varId) == (None, None, None):
                # Unknown type of change line, ignore.
                continue
            elif timeNotData and newTime is not None:
                # Reached beginning of a new timechunk, after the first one.
                tc = (
                    newTime,
                    changedVarIds,
                    valueStrings,
                )
                yield tc

                changedVarIds = []
                valueStrings = []
            elif varId is not None:
                changedVarIds.append(varId)
                valueStrings.append(value)

            newTime = value if timeNotData else newTime

        # Last timechunk.
        if newTime is not None:
            self.tcLineNum_, self.tcTell_ = prevTcLineNum_, prevTcTell_
            tc = (
                newTime,
                changedVarIds,
                valueStrings,
            )
            yield tc
    # }}} def vcdTimechunks

    def __enter__(self): # {{{
        self.fd = open(self.filename, 'r') \
                  if self.filename is not None else \
                  sys.stdin

        def getLines(fd): # {{{
            '''Generator producing stripped lines with numbers.

            NOTE: The usual for/__next__() method disables tell().
            '''
            line = fd.readline()
            lineNum = 1
            while line:
                yield lineNum, line.strip()
                line = fd.readline()
                lineNum += 1
        # }}} def getLines
        lines = getLines(self.fd)

        try:
            self.varIds, \
            self.varNames, \
            self.varSizes, \
            self.varTypes, \
            self.vcdComment, \
            self.vcdDate, \
            self.vcdVersion, \
            self.vcdTimescale = self.vcdHeader(lines)
        except StopIteration as e: # Missing $enddefinitions
            self.fd.close()
            raise e

        # Find first instance of each varId, and map to corresponding varType,
        # varSize, and list of varNames.
        # Could also be implemented with reduce()'s.
        self.varIdsUnique = []
        self.mapVarIdToType = {}
        self.mapVarIdToSize = {}
        self.mapVarIdToNames = {}
        _prev_ = None
        _iVars = zip(self.varIds, self.varTypes, self.varSizes, self.varNames)
        for v,t,s,nm in _iVars:

            # NOTE: Using _prev_ instead of not-in relies on vcdVars being
            # sorted previously in vcdHeader().
            # Using not-in is very expensive when there are many vars.
            #if v not in self.varIdsUnique:
            if v != _prev_:
                self.varIdsUnique.append(v)
                self.mapVarIdToType[v] = t
                self.mapVarIdToSize[v] = s
                self.mapVarIdToNames[v] = [nm]
            else:
                self.mapVarIdToNames[v] += [nm]

            _prev_ = v

        self.mapVarNameToVarId = \
            {nm: v for v,nms in self.mapVarIdToNames.items() for nm in nms}
        self.mapVarNameNovectorToVarId = \
            {re.sub(r'\[.*$', '', nm): v for nm,v in self.mapVarNameToVarId.items()}

        self.timechunks = self.vcdTimechunks(self, lines)

        return self
    # }}} def __enter__

    def __exit__(self, type, value, traceback):
        if self.fd != sys.stdin:
            self.fd.close()

# }}} class VcdReader

# TODO: Use this to support forgiving varNames?
def _varPathnamesToHiers(nms): # {{{
#def _varPathnamesToHiers(nms: List[str]) -> List:
        # Only allowed characters in varHier_ a-zA-Z0-9_:
        # 1. "hello", "world", etc - No hierarchy given. => Create TOP module.
        # 2. "module:foo.hello", "module:bar.world" - Hierarchy given but
        #     lacking top. => Create TOP module.
        # 3. "module:foo.hello", "module:foo.world" - Hierarchy given and
        #    top is the same for all vars. => No TOP required.
        hiers_ = [re.sub(r"[\W:]+", '', nm, re.ASCII).split('.') \
                     for nm in nms]
        topGiven = all(hiers_[i][0] == hiers_[i-1][0] \
                       for i in range(len(hiers_)))
        varHiers = hiers_ if topGiven else \
            [["module:TOP"] + h for h in hiers_]
        assert len(varHiers) == len(nms)

        return varHiers
# }}} def _varPathnamesToHiers

def detypeVarName(varName): # {{{
    if '[' in varName:
        withoutRange = varName[:varName.find('[')]
    else:
        withoutRange = varName
    nmParts = withoutRange.split('.')
    return '.'.join([p.split(':')[-1] for p in nmParts])
# }}} def detypeVarName

def _vcdVarDefs(self): # {{{
    varIds = self.varIds
    varTypes = self.varTypes
    varSizes = self.varSizes
    varNames = self.varNames

    # Calculate varScope which should look like:
    # [(scopeType, scopeName)]
    # [("module", "TOP"), (None, "foo"), ("wire", "mysignal")]
    # NOTE: scopeType is ignored for last element since that is already
    # given as varType.
    varScopes = [[s.split(':') if ':' in s else (None, s) \
                  for s in varName.split('.')] for varName in varNames]
    # Allow missing "module:" prefix on top level scope.
    varScopes = [[("module",sName) if 0 == i and sType is None \
                                   else (sType,sName) \
                  for i,(sType,sName) in enumerate(varScope)] \
                 for varScope in varScopes]
    for varScope in varScopes:
        assert all((sType in allowedScopeTypes) or (sType is None) \
                   for sType,sName in varScope)

    varDtNames = [detypeVarName(varName) for varName in varNames]

    assert len(varIds) == \
           len(varTypes) == \
           len(varSizes) == \
           len(varNames) == \
           len(varScopes) == \
           len(varDtNames), (len(varIds),
                           len(varTypes),
                           len(varSizes),
                           len(varNames),
                           len(varScopes),
                           len(varDtNames))

    # Sort (varDtName, varScopes, varType, varSize, varId)s alphabetically by
    # varDtName, which puts all common scopes together.
    vs = sorted(list(zip(varDtNames, varScopes, varTypes, varSizes, varIds)))

    # Detect scope changes and print scope/var/upscope tree.
    # {{{ ascent/descent
    # 1. No change. {foo.x, foo.y}
    #   #ascent = 0
    #   #descent = 0
    #   {foo.x, foo.y}
    #       cPL = 1
    #       pL = 1
    #       vL = 1
    #       #ascent = 0
    #       #descent = 0
    #   {foo.bar.baz.x, foo.bar.baz.y}
    #       cPL = 3
    #       pL = 3
    #       vL = 3
    #       #ascent = 0
    #       #descent = 0
    # 2. Down one or more. {foo.x, foo.bar.baz.y}
    #   #ascent = 0
    #   #descent >= 1
    #   {foo.x, foo.bar.y}
    #       cPL = 1
    #       pL = 1
    #       vL = 2
    #       #ascent = 0
    #       #descent = 1
    #   {foo.x, foo.bar.baz.y}
    #       cPL = 1
    #       pL = 1
    #       vL = 3
    #       #ascent = 0
    #       #descent = 2
    # 3. Up one or more. {foo.bar.baz.x, foo.y}
    #   #ascent >= 1
    #   #descent = 0
    #   {foo.bar.x, foo.y}
    #       cPL = 1
    #       pL = 2
    #       vL = 1
    #       #ascent = 1
    #       #descent = 0
    #   {foo.bar.baz.x, foo.y}
    #       cPL = 1
    #       pL = 3
    #       vL = 1
    #       #ascent = 2
    #       #descent = 0
    # 4. Up and down one or more. {foo.bar.baz.x, foo.hello.world.y}
    #   #ascent >= 1
    #   #descent >= 1
    #   {foo.bar.x, foo.baz.y}
    #       cPL = 1
    #       pL = 2
    #       vL = 2
    #       #ascent = 1
    #       #descent = 1
    #   {foo.bar.baz.x, foo.hello.world.y}
    #       cPL = 1
    #       pL = 3
    #       vL = 3
    #       #ascent = 2
    #       #descent = 2
    # }}} ascent/descent
    prevScope = [] #[(None, None)]
    for varDtName,varScope,varType,varSize,varId in vs:
        vL = len(varScope) - 1
        pL = len(prevScope)
        cPL = 0
        for (pType,pName),(vType,vName) in zip(prevScope, varScope[:-1]):
            if pType != vType or pName != vName:
                break
            else:
                cPL += 1
        assert cPL <= pL
        assert cPL <= vL
        nAscent = pL - cPL
        nDescent = vL - cPL

        #print()
        #print(varDtName,varScope,varType,varSize,varId)
        #print("  vL=%d, pL=%d, cPL=%d" % (vL, pL, cPL))
        #print("  nAscent=%d, nDescent=%d" % (nAscent, nDescent))

        # Calculate number of ascents ($upscope $end)
        for _ in range(nAscent):
            print(u"$upscope $end", file=self.fd)

        # Descend into module, from correct position in varScope
        # $scope <type> <name> $end
        relevantScope = varScope[cPL:cPL+nDescent]
        for sType,sName in relevantScope:
            thisScopeType = sType if sType is not None else prevScopeType
            print(u"$scope %s %s $end" % (thisScopeType, sName), file=self.fd)
            prevScopeType = thisScopeType

        prevScope = varScope[:-1]

        varRange = "" if 2 > varSize else \
                   "[%d:0]" % (varSize-1)
        _, varLocalName = varScope[-1]
        print(u"$var %s %d %s %s %s $end" % \
              (varType, varSize, varId, varLocalName, varRange), file=self.fd)

    # Calculate number of ascents ($upscope $end) after final var.
    for _ in range(vL):
        print(u"$upscope $end", file=self.fd)

    return
# }}} def _vcdVarDefs

class VcdWriter(object): # {{{
    def __init__(self, filename=None):
        self.filename = filename

        # Boolean to control if a blank line is inserted above each timechunk.
        self.separateTimechunks = True

    def wrHeader(self, varlist,
                 comment="", date="", version="",
                 timescale="1 ns", varaliases=[]): # {{{

        assert isinstance(comment, str), (type(comment), comment)
        assert isinstance(date, str), (type(date), date)
        assert isinstance(version, str), (type(version), version)
        assert isinstance(timescale, str), (type(timescale), timescale)

        # Comment, date, and version are just freeform strings.
        self.vcdComment = comment.strip()
        self.vcdDate = date.strip()
        self.vcdVersion = version.strip()

        if 0 < len(self.vcdComment):
            print(u"$comment %s $end" % self.vcdComment, file=self.fd)
            #self.fd.write(u"$comment %s $end\n" % self.vcdComment)

        if 0 < len(self.vcdDate):
            print(u"$date %s $end" % self.vcdDate, file=self.fd)

        if 0 < len(self.vcdVersion):
            print(u"$version %s $end" % self.vcdVersion, file=self.fd)

        def _verifyTimescale(ts): # {{{
        #def _verifyTimescale(ts: str) -> Tuple[str, str]:
                tsParts = ts.split()
                if 2 == len(tsParts):
                    timeNumber, timeUnit = tsParts
                elif 1 == len(tsParts):
                    # No separating space.
                    timeNumber = ts.rstrip("smunpf")
                    timeUnit = ts.lstrip("01")
                else:
                    assert False, ts

                assert timeNumber in allowedtimeNumbers, \
                    "Unknown time number <<<%s>>>" % timeNumber

                assert timeUnit in allowedtimeUnits, \
                    "Unknown time unit <<<%s>>>" % timeUnit

                return (timeNumber, timeUnit)
        # }}} def _verifyTimescale

        self.vcdTimescale = _verifyTimescale(timescale)
        print(u"$timescale %s %s $end" % self.vcdTimescale, file=self.fd)

        def _verifyVars(varlist, varaliases): # {{{
        #def _verifyVars(varlist: Varlist, varaliases):
            # Example inputs:
            #   varlist = [
            #       ("TOP.clk",                 1,  "wire"),
            #       ("module:TOP.badtype:rst",  1,  "wire"),
            #       ("TOP.myblock.counter",     8,  "reg"),
            #   ]
            #
            #   varaliases = [
            #       ("TOP.clk", "TOP.myblock.i_clk", "logic"),
            #       ("TOP.rst", "TOP.myblock.i_rst", "bit"),
            #   ]

            varIdsUnique = []
            varIds = []
            varNames = []
            varSizes = []
            varTypes = []

            for i, (varName, varSize, varType) in enumerate(varlist):
                varId = intToVarId(i)
                varIdsUnique.append(varId)
                varIds.append(varId)

                assert isinstance(varName, str), (type(varName), varName)
                assert varName not in varNames, "Replica varName=%s" % varName
                varNames.append(detypeVarName(varName))

                assert isinstance(varSize, int), (type(varSize), varSize)
                assert isinstance(varType, str), (type(varType), varType)
                assert varType in supportedTypes, \
                    "Unknown varType=%s" % varType
                assert isinstance(varSize, int)
                if "event" == varType:
                    varSize = 1 # assert varSize in [0, 1], varSize
                elif "real" == varType:
                    assert varSize in [8, 16, 32, 64], varSize
                elif "integer" == varType:
                    assert varSize in [8, 16, 32, 64], varSize
                else:
                    assert 0 < varSize, "varSize=%d" % varSize
                varTypes.append(varType)
                varSizes.append(varSize)

            for rootVarName, aliasName, aliasType in varaliases:
                rootVarNameDt = detypeVarName(rootVarName)
                aliasNameDt = detypeVarName(aliasName)

                assert rootVarNameDt in varNames, \
                    "Alias with unknown rootVarName=%s" % rootVarName

                idx = varNames.index(rootVarNameDt)
                assert 0 <= idx, idx

                varIds.append(varIds[idx])
                varNames.append(aliasNameDt)
                varTypes.append(varTypes[idx])
                varSizes.append(varSizes[idx])

            return varIdsUnique, varIds, varNames, varSizes, varTypes
        # }}} def _verifyVars

        self.varIdsUnique, \
        self.varIds, \
        self.varNames, \
        self.varSizes, \
        self.varTypes = _verifyVars(varlist, varaliases)
        _vcdVarDefs(self)

        self.mapVarNameToVarId = {self.varNames[i]: v for i,v in enumerate(self.varIdsUnique)}
        self.mapVarIdToVarSize = {v: self.varSizes[i] for i,v in enumerate(self.varIdsUnique)}
        self.mapVarIdToVarType = {v: self.varTypes[i] for i,v in enumerate(self.varIdsUnique)}

        print(u"$enddefinitions $end", file=self.fd)

        return
    # }}} def wrHeader

    def wrTimechunk(self, timechunk): # {{{

        newTime, changedVars, newValues = timechunk

        # Use each element in changedVars first as a varId, then a varName.
        changedVarIds = [v if v in self.varIdsUnique \
                           else (self.mapVarNameToVarId[v] if v in self.varNames \
                                                        else None) \
                         for v in changedVars]
        assert len(changedVarIds) == len(changedVars)

        # Don't write anything for empty timechunk.
        if 0 == len(changedVars):
            return

        # Start each timechunk with a blank line for readability.
        assert isinstance(self.separateTimechunks, bool), \
            (type(self.separateTimechunks), self.separateTimechunks)
        if self.separateTimechunks:
            print(u"", file=self.fd)

        assert isinstance(newTime, int), (type(newTime), newTime)
        print(u"#%d" % newTime, file=self.fd)

        for varId,newValue in sorted(list(zip(changedVarIds, newValues))):
            assert varId is not None # TODO: More helpful assertion message.

            varType = self.mapVarIdToVarType[varId]
            varSize = self.mapVarIdToVarSize[varId]

            if "event" == varType:
                # Events are always value=0 since they have no value.
                print(u"0%s" % varId, file=self.fd)
            elif varType in oneBitTypes and 1 == varSize:
                # 1b format
                assert str(newValue) in fourStates, newValue
                print(u"%s%s" % (str(newValue), varId), file=self.fd)
            elif "real" == varType:
                # real format
                # Always printed with 6 decimal places.
                if isinstance(newValue, float):
                    newValue_ = "%0.06f" % newValue
                else:
                    newValue_ = str(newValue)
                print(u"r%s %s" % (newValue_, varId), file=self.fd)
            else:
                # bit vector format
                if isinstance(newValue, int):
                    newValue_ = bin(newValue)[2:]
                else:
                    newValue_ = str(newValue)

                if len(newValue_) < varSize:
                    newValue_ = '0'*(varSize-len(newValue_)) + newValue_

                print(u"b%s %s" % (newValue_, varId), file=self.fd)

        return
    # }}} def wrTimechunk

    def __enter__(self):
        self.fd = open(self.filename, 'w') \
                  if self.filename is not None else \
                  sys.stdout
        return self

    def __exit__(self, type, value, traceback):
        if self.fd != sys.stdout:
            self.fd.close()

# }}} class VcdWriter

def rdMetadata(fname): # {{{
    '''Read through file counting actual value changes and finding
       location of timechunks.

    tcTell_ is 'an opaque number' (fileOffset) which can be with fd.seek()
        It points to the start of the line *after* the time specifier.
        Calling seek then next(timechunks) will give a wrong newTime.
        So you must save a list of (time, fileOffset) and use the saved time.

    Use mapVarIdToNumChanges to assign shorter varIds to signals which change
    more frequently.
    '''
    with VcdReader(fname) as vdi:
        timejumps_ = [] # [(time, position), ...]
        mapVarIdToTimejumps_ = {i: [] for i in vdi.varIdsUnique}
        mapVarIdToNumChanges_ = {i: 0 for i in vdi.varIdsUnique}

        prevValues_ = {i: None for i in vdi.varIdsUnique}
        for newTime,changedVarIds,newValues in vdi.timechunks:
            timejumps_.append((newTime, vdi.tcTell_))

            tcPrevValues = [prevValues_[i] for i in changedVarIds]
            for i,n,p in zip(changedVarIds, newValues, tcPrevValues):
                mapVarIdToTimejumps_[i].append((newTime, vdi.tcTell_))

                if n != p:
                    mapVarIdToNumChanges_[i] += 1
                prevValues_[i] = n

    timejumps_.sort()

    return timejumps_, mapVarIdToTimejumps_, mapVarIdToNumChanges_
# }}} def rdMetadata

def vcdClean(fnamei, fnameo, comment=None): # {{{
    '''Read in VCD with forgiving reader and write out cleaned version with
       strict writer.

    1. Most frequently changing signals are assigned shorter varIds.
    2. Redundant value changes are eliminated.
    3. Empty timechunks are eliminated.
    4. Timechunks are ordered.
    '''
    # Imports just for vcdClean kept separately since this isn't strictly
    # required for just reading and writing VCD.
    from dmppl.base import joinP, rdLines
    from tempfile import mkdtemp
    from shutil import rmtree

    # Read/copy input to temporary file.
    # Required when input is STDIN because it's read multiple times.
    tmpd = mkdtemp()
    tmpf = joinP(tmpd, "tmpf.vcd")
    with open(tmpf, 'w') as fd:
        fd.write('\n'.join(rdLines(fnamei, commentLines=False)))

    timejumps, mapVarIdToTimejumps, mapVarIdToNumChanges = rdMetadata(tmpf)

    cleanComment = "<<< dmppl.vcd.vcdClean >>>" if comment is None else comment

    with VcdReader(tmpf) as vdi, \
         VcdWriter(fnameo) as vdo:

        usedVarIds = []
        vlistUnsorted = []
        varaliases = []
        for i,n,s,t in zip(vdi.varIds, vdi.varNames, vdi.varSizes, vdi.varTypes):

            if i not in usedVarIds:
                usedVarIds.append(i)
                var = (i, n, s, t)
                vlistUnsorted.append(var)
            else:
                alias = (vdi.mapVarIdToNames[i][0], n, t)
                varaliases.append(alias)

        # Sort varlist by number of changes.
        vlistSorted = sorted([(mapVarIdToNumChanges[i], i, n, s, t) \
                              for i,n,s,t in vlistUnsorted], reverse=True)
        varlist = [(n, s, t) for c,i,n,s,t in vlistSorted]

        vdo.wrHeader(varlist,
                     comment=' '.join((vdi.vcdComment, cleanComment)),
                     date=vdi.vcdDate,
                     version=vdi.vcdVersion,
                     timescale=' '.join(vdi.vcdTimescale),
                     varaliases=varaliases)


        vdo.separateTimechunks = False # Omit blank lines between timechunks.

        # All timechunks are read in monotonic increasing time order, thanks to
        # the sort() in rdMetadata().
        # Multiple (consecutive) timechunks referring to the same time will be
        # read in the same order as the input file, so last one wins.
        # Timechunks to write are put into a queue, then only written out when
        # a timechunk for a greater time is processed.
        wrqTime_, wrqChangedVars_, wrqNewValues_ = 0, [], []

        _ = next(vdi.timechunks) # Initialize timechunks generator FSM.
        for newTime,fileOffset in timejumps:
            try:
                vdi.fd.seek(fileOffset)
                tci = next(vdi.timechunks)
            except StopIteration:
                # Last timechunk exhausts the rdLines generator underlying the
                # vdi.timechunks generator, so this restarts everything.
                vdi.fd.close()
                vdi.__enter__()
                _ = next(vdi.timechunks) # Initialize timechunks generator FSM.
                vdi.fd.seek(fileOffset)
                tci = next(vdi.timechunks)

            _, changedVarIds, newValues = tci

            changedVars = \
                [detypeVarName(vdi.mapVarIdToNames[v][0]) \
                 for v in changedVarIds]

            if newTime == wrqTime_:
                # Append this timechunk to queue.
                wrqChangedVars_ += changedVars
                wrqNewValues_ += newValues
            else:
                # Merge all timechunks in the queue.
                _merge = dict(zip(wrqChangedVars_, wrqNewValues_))
                mrgdChangedVars, mrgdNewValues = \
                    zip(*[(k,v) for k,v in _merge.items()])
                vdo.wrTimechunk((wrqTime_, mrgdChangedVars, mrgdNewValues))
                wrqChangedVars_, wrqNewValues_ = changedVars, newValues

            wrqTime_ = newTime

        # Merge last lot of timechunks in the queue.
        _merge = dict(zip(wrqChangedVars_, wrqNewValues_))
        mrgdChangedVars, mrgdNewValues = \
            zip(*[(k,v) for k,v in _merge.items()])
        tco = (wrqTime_, mrgdChangedVars, mrgdNewValues)
        vdo.wrTimechunk((wrqTime_, mrgdChangedVars, mrgdNewValues))

    rmtree(tmpd)

    return 0
# }}} def vcdClean

if __name__ == "__main__":
    assert False, "Not a standalone script."

