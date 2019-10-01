
# Standard library imports
from itertools import product
import os
import re
import sys

# PyPI library imports
import toml
import numpy as np

# Local library imports
from dmppl.base import dbg, Bunch, info, mkDirP, verb
from dmppl.math import saveNpy
from dmppl.toml import loadToml, saveToml
from dmppl.vcd import VcdReader, oneBitTypes

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
import dmppl.experiments.eva.eva_common as eva

if sys.version_info[0] == 3:
    unicode = str # Compatability with Python2

class EVCError(Exception): # {{{
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

class EVCError_TomlLoad(EVCError):
    '''TOML syntax error in EVC.
    '''
    def __init__(self, e):
        # TODO: Nicer message using e.lineno, e.colno, e.pos, e.doc?
        self.msg = e.__str__

class EVCError_DataType(EVCError):
    '''Data is wrong type.
    '''
    def __init__(self, data, expected):
        found = str(type(data).__name__)

        assert type(expected) in [type, list, type(None)]
        if expected is None:
            expect_str = '"None"'
        elif isinstance(expected, list):
            expect_str = 'one of "%s"' % \
                '", "'.join([x.__name__ if x is not None else 'None' \
                             for x in expected])
        else:
            expect_str = '"%s"' % expected.__name__

        data_str = str(data)

        self.msg = '''
The data "%s" is type "%s" but is expected to be %s.
''' % (data_str, found, expect_str)

class EVCError_DataValue(EVCError):
    '''Data is unexpected value.
    '''
    def __init__(self, data, expected):
        expect_str = 'one of "%s"' % '", "'.join(expected)

        self.msg = '''
The data value "%s" should be one of %s.
''' % (data, expect_str)

class EVCError_DataFormat(EVCError):
    '''Data is in wrong format.
    '''
    def __init__(self, data, example=''):
        if len(example):
            example = 'E.g.\n%s' % example
        self.msg = '''
The data "%s" does not match the specified format.
%s
''' % (data, example)

class EVCError_SignalName(EVCError):
    '''Mismatch between EVC and VCD.
    '''
    def __init__(self, name, signal):
        self.msg = '''
The event specifier "%s" uses signal "%s" \
which cannot be found in the VCD.
''' % (name, signal)

# }}} EVCError

def loadEvc(): # {{{
    '''Read EVC file with only basic checking.
    '''

    def infoEvc(evc): # {{{
        '''Print information about EVC.
        '''
        if not eva.infoFlag:
            return

        for k,v in evc.get("config", {}).items():
            msg = "%s = %s" % (k, v)
            info(msg, prefix="INFO:EVC:CONFIG: ")

        for m in evc.get("measure", []):
            msg = "%s <-- %s" % (m["name"], m["hook"])
            info(msg, prefix="INFO:EVC:MEASURE: ")

    # }}} def infoEvc

    verb("Loading EVC... ", end='')

    try:
        # NOTE: loadToml() appends ".toml" to fname.
        evc = toml.load(eva.paths.fname_evc)
    except toml.decoder.TomlDecodeError as e:
        raise EVCError_TomlLoad(e)

    verb("Done")

    infoEvc(evc)

    return evc
# }}} def loadEvc

def initCfg(evcConfig): # {{{
    '''Fill in and save CFG.
    '''

    def infoCfg(cfg): # {{{
        '''Print information about CFG.
        '''
        if not eva.infoFlag:
            return

        for k,v in cfg.__dict__.items():
            msg = "%s = %s" % (k, v)
            info(msg, prefix="INFO:CFG: ")

    # }}} def infoCfg

    verb("Initializing CFG... ", end='')

    cfg = Bunch()
    cfg.__dict__.update(loadToml(eva.appPaths.configDefault))
    cfg.__dict__.update(evcConfig)

    verb("Saving... ", end='')
    saveToml(cfg.__dict__, eva.paths.fname_cfg)
    verb("Done")

    infoCfg(cfg)

    return cfg
# }}} def initCfg

def evcCheckType(data, expected): # {{{
    '''Check data node is expected type.
A list of multiple expected types may be given, or just one type.
    '''
    assert type(expected) in [type, list, type(None)]

    if expected is None:
        ok = isinstance(data, None)
    elif isinstance(expected, list):
        ok = True in [isinstance(data, e) if e is not None else \
                         isinstance(data, None) \
                         for e in expected]
    else:
        ok = isinstance(data, expected)

    if not ok:
        raise EVCError_DataType(data, expected)
# }}}

def evcCheckValue(data, expected): # {{{
    '''Check data node is expected one of a list of expected values.
    '''
    assert isinstance(expected, (tuple, list))

    if data not in expected:
        raise EVCError_DataValue(data, expected)
# }}} def evcCheckValue

def checkEvc(evc): # {{{
    '''Check EVC for sanity.
    '''

    # All supported config keys have a default entry of the correct type.
    defaultConfig = loadToml(eva.appPaths.configDefault)
    defaultConfigKeys = list(defaultConfig.keys())
    for k,v in evc.get("config", {}).items():
        evcCheckValue(k, defaultConfigKeys)
        evcCheckType(v, type(defaultConfig[k]))

    # TODO: Check config values in allowed ranges.

    measureKeys = (
        "hook", # String: VCD path of measurement data. Required.
        "type", # String: in {event, binary, normal}.
        "name", # String: Measurement name.
        "subs", # [String]: Substitution values for name/hook.
        #"geq",  # Real: Threshold/interval limit.
        #"leq",  # Real: Threshold/interval limit.
    )

    measureTypes = (
        # Binary expected to be sparse.
        "event",

        # Binary may be dense.
        "binary",

        # Real in [0, 1].
        "normal",

        # Clip and normalise within interval `GEQ <= x <= LEQ` -> normal.
        #"interval", # Require both {geq, leq}.

        # True when `GEQ <= x AND x <= LEQ` -> binary.
        # Can be used to define true when either above or below a value.
        # Can be used to define true when either inside or outside an interval.
        #"threshold", # Require at least one of {geq, leq}.
    )

    measures = evc.get("measure", [])
    # TODO: Check required hook, name, type.
    for measure in measures:
        for k,v in measure.items():
            evcCheckValue(k, measureKeys)

            if "type" == k:
                evcCheckValue(v, measureTypes)

            # TODO: Check subs

    # TODO: More checking?
    return
# }}} def checkEvc

def expandEvc(evc, cfg): # {{{
    '''Perform substitutions in EVC to create and save EVCX.

    Does not include config since that goes into a separate file.
    '''

    def infoEvcx(evcx): # {{{
        '''Print information about EVCX.
        '''
        if not eva.infoFlag:
            return

        for nm,v in evcx.items():
            msg = "%s %d %s <-- %s" % (v["type"], v["idx"], nm, v["hook"])
            info(msg, prefix="INFO:EVCX: ")

    # }}} def infoEvcx

    reInt = r"[+-]?\d+"
    reEvcRange = re.compile(r"^" +
                            reInt +
                            r"\s*\.\.\s*" +
                            reInt +
                            r"(\s*\.\.\s*" +
                            reInt +
                            r")?$")

    def evcSubstitute(instr, choices): # {{{
        reEvcSubstitution = re.compile(r'({\d*})')

        ret_ = instr

        found = reEvcSubstitution.search(ret_)
        i = -1
        while found is not None:
            found_str = ret_[found.start():found.end()].strip("{}")
            if len(found_str) > 0:
                i = int(found_str)
            else:
                i += 1

            ret_ = reEvcSubstitution.sub(choices[i], ret_, count=1)

            found = reEvcSubstitution.search(ret_)

        return ret_
    # }}} def evcSubstitute

    verb("Expanding EVC to EVCX... ", end='')

    evsIdxEvent_, evsIdxBinary_, evsIdxNormal_ = 0, 0, 0
    evcx = {}
    for measure in evc.get("measure", []):
        subs = measure["subs"] if "subs" in measure else []
        tp = measure["type"]

        # `subs` guaranteed to be list of lists
        # Each `sub` guaranteed to be homogenous list.
        # Each `s` guaranteed to be string or int, but string may be a range.
        assert isinstance(subs, list)
        for sub in subs:
            assert isinstance(sub, list)
            for s in sub:
                # Unsure how practical other types are.
                assert isinstance(s, (int, str, unicode))

        # Build up new list of lists of usable strings.
        subs_ = []
        for sub in subs:
            sub_ = []
            for s in sub:
                # Range <start>..<stop>..<step>
                if isinstance(s, (str, unicode)) and reEvcRange.match(s):
                    sub_ += [str(i) for i in range(*[int(x) \
                                                     for x in s.split("..")])]
                else:
                    s_ = str(s)
                    sub_.append(s_)
            subs_.append(sub_)

        # `subs_` guaranteed to be list of lists
        # Each `sub_` guaranteed to be homogenous list.
        # Each `s_` guaranteed to be usable string.
        assert isinstance(subs_, list)
        for sub_ in subs_:
            assert isinstance(sub_, list)
            for s_ in sub_:
                assert isinstance(s_, str)

        subsProd = product(*subs_)
        for subsList in subsProd:
            fullName = evcSubstitute(measure["name"], subsList)

            fullHook = cfg.vcdhierprefix + \
                evcSubstitute(measure["hook"], subsList)

            if "event" == tp:
                evsIdx = evsIdxEvent_
                evsIdxEvent_ += 1
            elif "binary" == tp:
                evsIdx = evsIdxBinary_
                evsIdxBinary_ += 1
            elif "normal" == tp:
                evsIdx = evsIdxNormal_
                evsIdxNormal_ += 1
            else:
                evsIdx = evsIdxEvent_
                assert False, tp

            evcx[fullName] = {
                "hook": fullHook,
                "type": tp,
                "idx": evsIdx,
                #"geq": geq,
                #"leq": leq,
            }

    verb("Saving... ", end='')
    if eva.initDone: # Unittests don't setup everything.
        saveToml(evcx, eva.paths.fname_evcx)
    verb("Done")

    infoEvcx(evcx)

    return evcx
# }}} def expandEvc

def checkEvcxWithVcd(evcx, vcd): # {{{
    '''Check hooks exist in VCD.
    '''

    def infoEvcxWithVcd(evcx): # {{{
        '''Print information about EVCX.
        '''
        if not eva.infoFlag:
            return

        for nm,v in evcx.items():
            msg = "%s %d %s <-- %s %s %s" % \
                (v["type"], v["idx"], nm,
                 v["hookVarId"], v["hookType"], v["hookBit"])
            info(msg, prefix="INFO:EVCX/VCD: ")

    # }}} def infoEvcxWithVcd

    verb("Checking EVCX with VCD... ", end='')

    plainVarNames = [re.sub(r'\[.*$', '', x) for x in vcd.varNames]

    newEvcx_ = {}
    for nm,v in evcx.items():
        hk = v["hook"]

        # Plain hook in VCD, which doesn't have vector select.
        # NOTE: Only limited support. No vectored modules, no multidim.
        # hk -> hkPlain
        # module:TOP.foo.bar[3] -> module:TOP.foo.bar
        hkPlain = re.sub(r'\[.*$', '', hk)

        if hkPlain not in plainVarNames:
            raise EVCError_SignalName(hk, hkPlain)

        hkVarId = vcd.mapVarNameNovectorToVarId[hkPlain]
        hkType = vcd.mapVarIdToType[hkVarId]
        hkSize = vcd.mapVarIdToSize[hkVarId]

        # Check width of VCD signal contains numbered bit.
        if hkType in oneBitTypes and hk.endswith(']'):
            hkBit = int(hk[hk.rfind('['):].strip('[]'), 10)
            if hkBit >= hkSize:
                raise EVCError_SignalName(hk, hkBit)
        else:
            hkBit = None

        newEvcx_[nm] = v
        newEvcx_[nm].update({
            "hookVarId": hkVarId,
            "hookType": hkType,
            "hookBit": hkBit,
        })
    verb("Done")

    infoEvcxWithVcd(newEvcx_)

    return newEvcx_

# }}} def checkEvcxWithVcd

def blockConstants(evcx, cfg): # {{{
    '''Calculate constants from EVCX and CFG
    '''
    bc = Bunch()

    bc.eventNames  = [nm for nm,v in evcx.items() if v["type"] == "event"]
    bc.binaryNames = [nm for nm,v in evcx.items() if v["type"] == "binary"]
    bc.normalNames = [nm for nm,v in evcx.items() if v["type"] == "normal"]


    # TODO: How to specify simple functions like reflection, derivatives, FFT?
    # event: 1 <==> non-Zero, 0 otherwise
    # binary_rise: 1 <==> posedge, 0 otherwise
    # binary_fall: 1 <==> negedge, 0 otherwise
    # normal_pos0: (f_i)
    # normal_neg0: (1 - f_i)
    # normal_pos1: (f_i)'
    # normal_neg1: (1 - f_i)'
    # normal_pos2: (f_i)''
    # normal_neg2: (1 - f_i)''
    # ...
    bc.nEvent  = len(bc.eventNames)         # occur
    bc.nBinary = len(bc.binaryNames) * 2    # rise, fall
    bc.nNormal = len(bc.normalNames) * 4    # pos, neg, rise, fall

    bc.eventShape = (bc.nEvent, cfg.evsblocksize)
    bc.binaryShape = (bc.nBinary, cfg.evsblocksize)
    bc.normalShape = (bc.nNormal, cfg.evsblocksize)

    if eva.infoFlag:
        eventMsg = "evsBlockEventShape = %s ==> %dKiB" % \
            (str(bc.eventShape), bc.nEvent * cfg.evsblocksize / 1024.0)
        info(eventMsg, prefix="INFO:EVS: ")

        binaryMsg = "evsBlockBinaryShape = %s ==> %dKiB" % \
            (str(bc.binaryShape), bc.nBinary * cfg.evsblocksize / 1024.0)
        info(binaryMsg, prefix="INFO:EVS: ")

        normalMsg = "evsBlockNormalShape = %s ==> %dKiB" % \
            (str(bc.normalShape), bc.nNormal * cfg.evsblocksize / 128.0)
        info(normalMsg, prefix="INFO:EVS: ")

    return bc
# }}} def blockConstants

def evaInit(args): # {{{
    '''Read in EVC and VCD to create result directory like ./foo.eva/
    '''
    assert eva.initDone

    def twoStateBool(v, hookbit): # {{{
        if isinstance(v, int):
            return (0 != v)
        else:
          assert isinstance(v, str), (type(v), v)
          intValue = int(v, 2)
          if hookBit is None:
              return (intValue != 0)
          else:
              return ((intValue & 1<<hookBit) != 0)
    # }}} def twoStateBool

    evc = loadEvc()
    checkEvc(evc)

    mkDirP(eva.paths.outdir)

    eva.cfg = initCfg(evc["config"])

    evcx_ = expandEvc(evc, eva.cfg)

    # Gather common measurement types.
    bc = blockConstants(evcx_, eva.cfg)

    # NOTE: VCD input may come from STDIN ==> only read once.
    with VcdReader(args.input) as vcd:
        evcx = checkEvcxWithVcd(evcx_, vcd)

        evcxVarIds = set(v["hookVarId"] for nm,v in evcx.items())
        mapVarIdToEvsIndices = \
            {varid: [(v["type"], v["idx"], v["hookType"], v["hookBit"]) \
                     for nm,v in evcx.items() \
                     if varid == v["hookVarId"]] for varid in evcxVarIds}


        # Initialize arrays which will comprise a block of the EVS dataset.
        blkEvent = np.zeros(bc.eventShape, dtype=np.bool)
        blkBinary = np.zeros(bc.binaryShape, dtype=np.bool)
        blkNormal = np.zeros(bc.normalShape, dtype=np.float64)
        evsFnameFmt = os.path.join(eva.paths.fname_evs, "evs.%s.%d")
        mkDirP(os.path.dirname(evsFnameFmt))

        # Work through timechunks updating ndarrays.
        mapVarIdToPrev_ = {varid: (0,0) for varid in evcxVarIds}

        blkNumPrev_ = 0
        for tc in vcd.timechunks:
            newTime, changedVarIds, newValues = tc

            if newTime < eva.cfg.timestart:
                continue

            if eva.cfg.timestop != 0 and newTime > eva.cfg.timestop:
                break

            tQuotient, tRemainder = divmod(newTime, eva.cfg.timestep)
            if 0 != tRemainder:
                continue

            # Index in EVent Sample (EVS) array of this time.
            timeIdx = (newTime - eva.cfg.timestart) // eva.cfg.timestep
            assert isinstance(timeIdx, int), type(timeIdx)
            assert 0 <= timeIdx, (timeIdx, newTime, eva.cfg.timestart, eva.cfg.timestep)

            # EVS time is split into blocks.
            blkNum, blkIdx = divmod(timeIdx, eva.cfg.evsblocksize)

            # Write current blocks to disk, reinitialize.
            if blkNum != blkNumPrev_:
                saveNpy(blkEvent,  evsFnameFmt % ("event", blkNum))
                saveNpy(blkBinary, evsFnameFmt % ("binary", blkNum))
                saveNpy(blkNormal, evsFnameFmt % ("normal", blkNum))

                blkEvent = np.zeros(bc.eventShape, dtype=np.bool)
                blkBinary = np.zeros(bc.binaryShape, dtype=np.bool)
                blkNormal = np.zeros(bc.normalShape, dtype=np.float64)

                # Reset previous block indices to 0.
                mapVarIdToPrev_ = \
                    {varid: (v,0) for varid,(v,i) in mapVarIdToPrev_.items()}

            for varId,newValue in zip(changedVarIds, newValues):
                if not varId in evcxVarIds:
                    continue

                assert isinstance(newValue, str)
                newValueClean = newValue.replace('x', '0').replace('z', '1')

                prevValue, prevBlkIdx = mapVarIdToPrev_[varId] # Always clean.

                # Fill arrays
                # TODO: Needs more testing.
                # TODO: rise/fall etc?
                for tp,evsIdx,hookType,hookBit in mapVarIdToEvsIndices[varId]:

                    if "event" == tp:
                        if "event" == hookType:
                            blkEvent[evsIdx][blkIdx] = True
                        elif hookType in oneBitTypes:
                            blkEvent[evsIdx][blkIdx] = \
                                twoStateBool(newValueClean, hookBit)
                        else:
                            assert False, hookType

                    elif "binary" == tp:
                        if hookType in oneBitTypes:
                            blkBinary[evsIdx][prevBlkIdx+1:blkIdx] = \
                                twoStateBool(prevValue, hookBit)
                            blkBinary[evsIdx][blkIdx] = \
                                twoStateBool(newValueClean, hookBit)
                        else:
                            assert False, hookType

                    elif "normal" == tp:
                        if "real" == hookType:
                            blkNormal[evsIdx][blkIdx] = float(newValueClean)
                        else:
                            assert False, hookType
                    else:
                        assert False, tp

                mapVarIdToPrev_[varId] = newValueClean, blkIdx

        # End of file, save last block.
        saveNpy(blkEvent,  evsFnameFmt % ("event", blkNum))
        saveNpy(blkBinary, evsFnameFmt % ("binary", blkNum))
        saveNpy(blkNormal, evsFnameFmt % ("normal", blkNum))

# }}} def evaInit

if __name__ == "__main__":
    assert False, "Not a standalone script."
