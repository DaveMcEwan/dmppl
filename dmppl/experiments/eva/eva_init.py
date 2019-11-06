
# -*- coding: utf8 -*-

# Standard library imports
from itertools import groupby, product
import os
import re
import struct
import sys

# PyPI library imports
import toml

# Local library imports
from dmppl.base import dbg, info, verb, appendNonDuplicate, Bunch, \
    indexDefault, mkDirP, joinP
from dmppl.math import dotp, clipNorm, saveNpy
from dmppl.toml import loadToml, saveToml
from dmppl.vcd import VcdReader, VcdWriter, oneBitTypes, detypeVarName
from dmppl.scripts.vcd_utils import vcdClean
from dmppl.color import identiconSpriteSvg

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
from dmppl.experiments.eva.eva_common import appPaths, paths, \
    isUnitIntervalMeasure, measureNameParts, meaDbFromVcd

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

def loadEvc(infoFlag): # {{{
    '''Read EVC file with only basic checking.
    '''

    def infoEvc(evc): # {{{
        '''Print information about EVC.
        '''
        if not infoFlag:
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
        assert paths._INITIALIZED
        evc = toml.load(paths.fname_evc)
    except toml.decoder.TomlDecodeError as e:
        raise EVCError_TomlLoad(e)

    verb("Done")

    infoEvc(evc)

    return evc
# }}} def loadEvc

def initCfg(evcConfig, infoFlag): # {{{
    '''Fill in and save CFG.
    '''

    def infoCfg(cfg): # {{{
        '''Print information about CFG.
        '''
        if not infoFlag:
            return

        for k,v in cfg.__dict__.items():
            msg = "%s = %s" % (k, v)
            info(msg, prefix="INFO:CFG: ")

    # }}} def infoCfg

    verb("Initializing CFG... ", end='')

    cfg = Bunch()
    cfg.__dict__.update(loadToml(appPaths.configDefault))
    cfg.__dict__.update(evcConfig)

    verb("Saving... ", end='')
    saveToml(cfg.__dict__, paths.fname_cfg)
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
    defaultConfig = loadToml(appPaths.configDefault)
    defaultConfigKeys = list(defaultConfig.keys())
    for k,v in evc.get("config", {}).items():
        evcCheckValue(k, defaultConfigKeys)
        evcCheckType(v, type(defaultConfig[k]))

    # TODO: Check config values in allowed ranges.

    measureKeys = (
        "hook", # String: VCD path of measurement data. Required.
        "type", # String: in {event, bstate, threshold, normal}.
        "name", # String: Measurement name.
        "subs", # [String]: Substitution values for name/hook.
        "geq",  # Real/Int: Threshold limit.
        "leq",  # Real/Int: Threshold limit.
    )

    measureTypes = (
        # Binary expected to be sparse.
        "event",

        # Binary may be dense.
        "bstate",

        # True when `GEQ <= x AND x <= LEQ` -> bstate.
        # Or when `LEQ <= x OR x <= GEQ` -> bstate.
        # The logic only makes sense these two ways.
        # Can be used to define true when either above or below a value.
        # Can be used to define true when either inside or outside an interval.
        "threshold", # Require at least one of {geq, leq}.

        # Clip and normalise within interval `GEQ <= x <= LEQ` -> normal.
        # Real in [0, 1].
        "normal", # Optional {geq, leq}, defaulting to {0, 1}.
    )

    measures = evc.get("measure", [])
    for measure in measures:
        assert "hook" in measure.keys()
        assert "name" in measure.keys()
        assert "type" in measure.keys()
        for k,v in measure.items():
            evcCheckValue(k, measureKeys)

            if "type" == k:
                evcCheckValue(v, measureTypes)

                if "threshold" == v:
                    leqExists = ("leq" in measure.keys())
                    geqExists = ("geq" in measure.keys())
                    assert leqExists or geqExists

            # TODO: Check subs

    # TODO: More checking?
    return
# }}} def checkEvc

def expandEvc(evc, cfg, infoFlag): # {{{
    '''Perform substitutions in EVC to create and save EVCX.

    Does not include config since that goes into a separate file.
    '''

    def infoEvcx(evcx): # {{{
        '''Print information about EVCX.
        '''
        if not infoFlag:
            return

        for nm,v in evcx.items():
            hk = v["hook"]
            geq = v.get("geq")
            leq = v.get("leq")
            if v["type"] in ["threshold", "normal"]:
                hk = hk if geq is None else ("%s <= " % geq + hk)
                hk = hk if leq is None else (hk + " <= %s" % leq)

            msg = "%s %d %s <-- %s" % (v["type"], v["idx"], nm, hk)
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

    evsIdxEvent_, evsIdxBstate_, evsIdxNormal_, evsIdxThreshold_ = 0, 0, 0, 0
    evcx = {}
    for measure in evc.get("measure", []):
        subs = measure["subs"] if "subs" in measure else []
        tp = measure["type"]

        if "normal" == tp:
            # Values of geq,leq define clipNorm interval.
            geq = measure.get("geq", 0)
            leq = measure.get("leq", 1)
            assert isinstance(geq, (int, float)), (type(geq), geq)
            assert isinstance(leq, (int, float)), (type(leq), leq)
            assert geq < leq, (geq, leq)
        elif "threshold" == tp:
            # At least one of geq, leq must be a number.
            # Values of geq,leq used for boundary checks.
            geq = measure.get("geq", None)
            leq = measure.get("leq", None)
            assert (geq is not None) or (leq is not None), (geq, leq)
            assert isinstance(geq, (int, float)) or geq is None, (type(geq), geq)
            assert isinstance(leq, (int, float)) or leq is None, (type(leq), leq)
        else:
            # Event and bstate don't use geq or leq.
            pass

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
            elif "bstate" == tp:
                evsIdx = evsIdxBstate_
                evsIdxBstate_ += 1
            elif "threshold" == tp:
                evsIdx = evsIdxThreshold_
                evsIdxThreshold_ += 1
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
            }
            if tp in ["threshold", "normal"]:
                evcx[fullName]["geq"] = geq
                evcx[fullName]["leq"] = leq

    verb("Saving... ", end='')
    # Unittests don't setup everything.
    try:
        saveToml(evcx, paths.fname_evcx)
    except AttributeError:
        pass
    verb("Done")

    infoEvcx(evcx)

    return evcx
# }}} def expandEvc

def checkEvcxWithVcd(evcx, vcd, infoFlag): # {{{
    '''Check hooks exist in VCD.
    '''

    def infoEvcxWithVcd(evcx): # {{{
        '''Print information about EVCX.
        '''
        if not infoFlag:
            return

        for nm,v in evcx.items():
            msg = "%s %d %s <-- %s %s %s" % \
                (v["type"], v["idx"], nm,
                 v["hookVarId"], v["hookType"], v["hookBit"])
            info(msg, prefix="INFO:EVCX/VCD: ")

    # }}} def infoEvcxWithVcd

    verb("Checking EVCX with VCD... ", end='')

    plainVarNames = [re.sub(r'\[.*$', '', x) for x in vcd.varNames]

    evcxx_ = {}
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

        evcxx_[nm] = v
        evcxx_[nm].update({
            "hookVarId": hkVarId,
            "hookType": hkType,
            "hookBit": hkBit,
        })
    verb("Done")

    infoEvcxWithVcd(evcxx_)

    return evcxx_

# }}} def checkEvcxWithVcd

def meaVcd(instream, evcx, cfg, infoFlag): # {{{
    '''Filter input data to sanitized VCD (measure.vcd).

    Extract measurements of interest, at times of interest.
    Perform interpolation for normal measurements.
    Time becomes a straightforward sample index.
    Hierarchy shows raw measures and reflection/rise/fall.

    NOTE: This initial extraction to filter/clean the dataset is probably the
    most complex part of eva!
    '''
    assert paths._INITIALIZED

    def twoStateBool(v, hookbit): # {{{
        if isinstance(v, int):
            ret = (0 != v)
        else:
          assert isinstance(v, str), (type(v), v)
          intValue = int(v, 2)
          if hookBit is None:
              ret = (intValue != 0)
          else:
              ret = ((intValue & 1<<hookBit) != 0)

        assert isinstance(ret, bool), type(ret)

        return ret
    # }}} def twoStateBool

    def vcdoVarlist(evcx): # {{{
        '''Create varlist for vcdo.wrHeader from EVCX.

        structure:  [ (<name:str>, <width:int>,  <type:str>), ... ]
        example:    [ ("aName", 1,  "bit"), ... ]

        All signals are of either "bit" or "real" VCD type.
        '''
        measuresEvent = (nm for nm,v in evcx.items() if "event"  == v["type"])
        measuresBstate = (nm for nm,v in evcx.items() if "bstate" == v["type"])
        measuresThreshold = (nm for nm,v in evcx.items() if "threshold" == v["type"])
        measuresNormal = (nm for nm,v in evcx.items() if "normal" == v["type"])

        # Sibling measurements denoted by prefix.
        prefixesEvent =  ("measure",)
        prefixesBstate = ("measure", "reflection", "rise", "fall",)
        prefixesNormal = ("raw", "smooth", "measure",)
        prefixesThreshold = ("measure", "reflection", "rise", "fall",)

        namesEvent = \
            ('.'.join(("event", pfx, nm)) \
             for nm in sorted(measuresEvent) for pfx in prefixesEvent)
        namesBstate = \
            ('.'.join(("bstate", pfx, nm)) \
             for nm in sorted(measuresBstate) for pfx in prefixesBstate)
        namesThreshold = \
            ('.'.join(("threshold", pfx, nm)) \
             for nm in sorted(measuresThreshold) for pfx in prefixesThreshold)
        namesNormal = \
            ('.'.join(("normal", pfx, nm)) \
             for nm in sorted(measuresNormal) for pfx in prefixesNormal)

        varlist = [(nm, 1, "bit") \
                   for nms in (namesEvent, namesBstate, namesThreshold,) \
                   for nm in nms] + \
                  [(nm, 64, "real") \
                   for nms in (namesNormal,) \
                   for nm in nms]

        return varlist
    # }}} def vcdoVarlist

    def interpolateNormal(iVarId, oTime, mea, mapVarIdToHistory_, nq_, bq_, newValue=None): # {{{
        nm = mea["name"]
        geq = mea["geq"]
        leq = mea["leq"]

        prevIpolTime, prevIpolValues_ = mapVarIdToHistory_[iVarId]

        for t in range(prevIpolTime+1, oTime):
            assert t < oTime, (t, oTime)

            zs = [prevIpolValues_[0]] + prevIpolValues_
            prevIpolValues_ = zs[:-1]

            assert len(zs) == len(cfg.fir), zs
            smoothValue = dotp(zs, cfg.fir)
            clipnormValue = clipNorm(smoothValue, geq, leq)

            bq_.append((t, "normal.smooth." + nm, smoothValue))
            bq_.append((t, "normal.measure." + nm, clipnormValue))

        zs = [prevIpolValues_[0] if newValue is None else newValue] + prevIpolValues_
        mapVarIdToHistory_[iVarId] = (oTime, zs[:-1])

        assert len(zs) == len(cfg.fir), zs
        smoothValue = dotp(zs, cfg.fir)
        clipnormValue = clipNorm(smoothValue, geq, leq)

        nq_.append(("normal.smooth." + nm, smoothValue))
        nq_.append(("normal.measure." + nm, clipnormValue))

    # }}} def interpolateNormal

    # NOTE: VCD input may come from STDIN ==> only read once.
    with VcdReader(instream) as vcdi, VcdWriter(paths.fname_mea) as vcdo:
        evcxx = checkEvcxWithVcd(evcx, vcdi, infoFlag)

        verb("Extracting measurements to VCD ... ", end='')

        evcxVarIds = tuple(sorted(list(set(v["hookVarId"] \
                                           for nm,v in evcxx.items()))))

        meaSortKey = (lambda mea: mea["name"])
        mapVarIdToMeasures = \
            {varId: sorted([{"name": nm,
                             "type": v["type"],
                             "hookType": v["hookType"],
                             "hookBit": v["hookBit"],
                             "geq": v.get("geq"),
                             "leq": v.get("leq")} \
                            for nm,v in evcxx.items() \
                            if varId == v["hookVarId"]], key=meaSortKey) \
             for varId in evcxVarIds}

        # Initialize previous values to 0.
        # {varId: (time, value), ...}
        mapVarIdToPrev_ = {varId: (0,0) for varId in evcxVarIds}

        # Initialise previous values for normals to 0 for filter history.
        # {varId: (time, values), ...}
        mapVarIdToHistory_ = \
            {varId: (0, [0.0 for _ in cfg.fir[1:]]) \
             for varId in evcxVarIds \
             if "normal" in [mea["type"] for mea in mapVarIdToMeasures[varId]]}

        vcdo.wrHeader(vcdoVarlist(evcx),
                      comment=' '.join((vcdi.vcdComment,
                                        "<<< Extracted by evaInit >>>")),
                      date=vcdi.vcdDate,
                      version=vcdi.vcdVersion,
                      timescale=' '.join(vcdi.vcdTimescale))

        # Forward (future) queue of speculative changes which may need to be
        # interleaved with timechunks from vcdi.
        # E.g. event->bit conversion inferring 1 then 0 in consecutive times.
        # Or rise/fall on bstate.
        # [ (time, name, value) ... ]
        # Initialise all measurements to 0, except reflections to 1.
        fq_ = [(0, nm, int(re.match(r"^[^\.]*\.reflection\.", nm) is not None)) \
               for nm in vcdo.varNames]

        # Work through vcdi timechunks putting values into vcdo.
        for iTc in vcdi.timechunks:
            iTime, iChangedVarIds, iNewValues = iTc

            if iTime < cfg.timestart:
                continue

            if cfg.timestop != 0 and iTime > cfg.timestop:
                break

            tQuotient, tRemainder = divmod(iTime, cfg.timestep)
            if 0 != tRemainder:
                continue

            # Index in EVent Sample (EVS) array of this time.
            oTime = (iTime - cfg.timestart) // cfg.timestep
            assert isinstance(oTime, int), type(oTime)
            assert 0 <= oTime, (oTime, iTime, cfg.timestart, cfg.timestep)

            # Current (now) queue of changes which may contain duplicate
            # varnames with different values.
            # Only the last appended will be used.
            # No time field is necessary, all use current timechunk (oTime).
            # [ (name, value) ... ]
            nq_ = [(nm, v) for t,nm,v in fq_ if t == oTime]

            # Extract proper changes from fq_ and put into current queue.
            # Changes are proper if they are for time before this timechunk.
            # fq_ may still contain future speculative changes.
            bq_ = [(t,nm,v) for t,nm,v in fq_ if t < oTime]
            fq_ = [(t,nm,v) for t,nm,v in fq_ if t > oTime]


            for iVarId,iNewValue in zip(iChangedVarIds, iNewValues): # {{{
                if not iVarId in evcxVarIds:
                    continue

                assert isinstance(iNewValue, str) # VcdReader only gives str.
                newValueClean = iNewValue.replace('x', '0').replace('z', '1')

                prevTime, prevValue = mapVarIdToPrev_[iVarId] # Always clean.
                assert prevTime <= oTime, (prevTime, oTime)

                # Each iVarId may refer to multiple measurements, such as
                # vectored wires or wires used in multiple ways.
                for mea in mapVarIdToMeasures[iVarId]:
                    nm = mea["name"]
                    tp = mea["type"]
                    hookType = mea["hookType"]
                    hookBit = mea["hookBit"]

                    if "event" == tp: # {{{
                        if "event" == hookType:
                            # vcdi implies event only occurring at this time.
                            nq_.append(("event.measure." + nm, 1))

                            # Speculatively reset to 0 in next time.
                            fq_.append((oTime+1, "event.measure." + nm, 0))
                        elif hookType in oneBitTypes:
                            newValue = int(twoStateBool(newValueClean, hookBit))
                            nq_.append(("event.measure." + nm, newValue))
                        else:
                            # Event measure only made from VCD event, or
                            # 2-state (bit), 4-state types (wire, reg, logic)
                            assert False, hookType
                    # }}} event

                    elif "bstate" == tp: # {{{
                        if hookType in oneBitTypes:
                            newValue = twoStateBool(newValueClean, hookBit)

                            if prevValue != newValue:
                                nq_.append(("bstate.measure." + nm, int(newValue)))
                                nq_.append(("bstate.reflection." + nm, int(not newValue)))

                                if newValue:
                                    nq_.append(("bstate.rise." + nm, 1))
                                    fq_.append((oTime+1, "bstate.rise." + nm, 0))
                                else:
                                    nq_.append(("bstate.fall." + nm, 1))
                                    fq_.append((oTime+1, "bstate.fall." + nm, 0))
                            else:
                                pass # No change
                        else:
                            # Bstate measure only made from VCD 2-state (bit) or
                            # 4-state types (wire, reg, logic, etc)
                            assert False, hookType
                    # }}} bstate

                    elif "threshold" == tp: # {{{
                        if (hookType in oneBitTypes and hookBit is None) or \
                           (hookType in ["real", "integer"]):

                            geq = mea["geq"]
                            leq = mea["leq"]

                            newValueFloat = float(newValueClean) \
                                if "real" == hookType else \
                                float(int(newValueClean, 2))

                            if geq is None:
                                # Is measurement under threshold?
                                newValue = (newValueFloat <= leq)
                            elif leq is None:
                                # Is measurement over threshold?
                                newValue = (geq <= newValueFloat)
                            elif geq < leq:
                                # Is measurement inside interval?
                                newValue = \
                                    (newValueFloat <= leq and \
                                     geq <= newValueFloat)
                            else:
                                # Is measurement outside interval?
                                newValue = \
                                    (newValueFloat <= leq or \
                                     geq <= newValueFloat)

                            if prevValue != newValue:
                                nq_.append(("threshold.measure." + nm, int(newValue)))
                                nq_.append(("threshold.reflection." + nm, int(not newValue)))

                                if newValue:
                                    nq_.append(("threshold.rise." + nm, 1))
                                    fq_.append((oTime+1, "threshold.rise." + nm, 0))
                                else:
                                    nq_.append(("threshold.fall." + nm, 1))
                                    fq_.append((oTime+1, "threshold.fall." + nm, 0))
                            else:
                                pass # No change

                        else:
                            # Threshold (number to bstate) measure only made
                            # from VCD 2-state (bit) vector, 4-state (wire, reg,
                            # logic) vector, integer, or real.
                            assert False, (hookType, hookBit)
                    # }}} threshold

                    elif "normal" == tp: # {{{
                        if (hookType in oneBitTypes and hookBit is None) or \
                           (hookType in ["real", "integer"]):

                            newValue = float(newValueClean) \
                                if "real" == hookType else \
                                float(int(newValueClean, 2))

                            # NOTE: normal.raw values are not necessarily
                            # in [0, 1]; rather than (-inf, +inf).
                            nq_.append(("normal.raw." + nm, newValue))

                            interpolateNormal(iVarId, oTime, mea,
                                              mapVarIdToHistory_, nq_, bq_,
                                              newValue=newValue)

                        else:
                            # Normal (real number) measure only made
                            # from VCD 2-state (bit) vector, 4-state (wire, reg,
                            # logic) vector, integer, or real.
                            assert False, (hookType, hookBit)
                    # }}} normal

                    else:
                        assert False, tp

                # Track previous value in vcdi
                try:
                    mapVarIdToPrev_[iVarId] = oTime, newValue
                except UnboundLocalError:
                    pass

            # }}} for iVarId,iNewValue in zip(iChangedVarIds, iNewValues)

            # Interpolate normal/smooth values up to, current timechunk for
            # measures which aren't sampled in this timechunk.
            for iVarId,(prevIpolTime, prevIpolValues_) in mapVarIdToHistory_.items():
                if prevIpolTime == oTime:
                    continue

                for mea in mapVarIdToMeasures[iVarId]:
                    if "normal" != mea["type"] or 0 >= oTime:
                        continue

                    interpolateNormal(iVarId, oTime, mea,
                                      mapVarIdToHistory_, nq_, bq_,
                                      newValue=None)



            bq_.sort()
            for fqTime, fqGroup in groupby(bq_, key=(lambda x: x[0])):
                fqChangedVars, fqNewValues = \
                    list(zip(*[(nm,v) for _,nm,v in fqGroup]))
                assert fqTime < oTime, (fqTime, oTime)
                vcdo.wrTimechunk((fqTime, fqChangedVars, fqNewValues))

            # Resolve conflicts from fq_/bq_.
            # Forward queue is speculative so a proper value from the current
            # timechunk will take precedence.
            # I.e. Always use the last appended change.
            if 0 < len(nq_):
                dedupVars = []
                for nm,v in nq_:
                    dedupVars = appendNonDuplicate(dedupVars, (nm,v), replace=True)
                nqChangedVars, nqNewValues = zip(*dedupVars)
                vcdo.wrTimechunk((oTime, nqChangedVars, nqNewValues))

        verb("Done") # with

    return
# }}} def meaVcd

def evaVcdInfo(fname): # {{{
    '''Read in a VCD and return a dict of metadata.
    '''
    ret = {}
    with VcdReader(fname) as vcdi:
        #ret["varIds"]   = vcdi.varIds
        #ret["varNames"] = vcdi.varNames
        #ret["varSizes"] = vcdi.varSizes
        #ret["varTypes"] = vcdi.varTypes
        #ret["comment"] = vcdi.vcdComment
        #ret["date"]    = vcdi.vcdDate
        #ret["version"] = vcdi.vcdVersion
        #ret["timescale"] = ' '.join(vcdi.vcdTimescale)

        varNames = [detypeVarName(nm) for nm in vcdi.varNames]
        ret["unitIntervalVarNames"] = \
            [nm for nm in varNames if isUnitIntervalMeasure(nm)]

        ret["timechunkTimes"] = []
        for tc in vcdi.timechunks:
            newTime, changedVarIds, newValues = tc
            ret["timechunkTimes"].append(newTime)

    return ret
# }}} def evaVcdInfo

def createIdenticons(vcdInfo): # {{{
    '''Produce an identicon for each signal in VCD.
    '''
    verb("Creating identicons... ", end='')

    mkDirP(paths.dname_identicon)

    measureNames = vcdInfo["unitIntervalVarNames"]

    for nm in measureNames:
        measureType, siblingType, baseName = measureNameParts(nm)

        svgStr = identiconSpriteSvg(baseName)

        fname = joinP(paths.dname_identicon, baseName + ".svg")
        with open(fname, 'w') as fd:
            fd.write(svgStr)

    verb("Done")

    return
# }}} def createIdenticons

def evaInit(args): # {{{
    '''Read in EVC and VCD to create result directory like ./foo.eva/
    '''
    assert paths._INITIALIZED

    evc = loadEvc(args.info)
    checkEvc(evc)

    mkDirP(paths.outdir)

    cfg = initCfg(evc["config"], args.info)

    evcx = expandEvc(evc, cfg, args.info)

    # Fully read in and copy then clean input data.
    verb("Cleaning input VCD... ", end='')
    vcdClean(args.input, paths.fname_cln)
    verb("Done")

    # VCD-to-VCD: extract, interpolate, clean
    meaVcd(paths.fname_cln, evcx, cfg, args.info)
    #vcdClean(paths.fname_mea) # Reduce size of varIds
    vcdInfo = evaVcdInfo(paths.fname_mea)
    saveToml(vcdInfo, paths.fname_meainfo)

    # VCD-to-binaries
    meaDbFromVcd()

    # Identicons
    createIdenticons(vcdInfo)

    return 0
# }}} def evaInit

if __name__ == "__main__":
    assert False, "Not a standalone script."
