
# Standard library imports
from itertools import product
import re

# PyPI library imports
import toml

# Local library imports
from dmppl.base import *
from dmppl.toml import loadToml, saveToml
from dmppl.vcd import VcdReader

# Project imports
import eva_common as eva

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

def expandEvc(evc): # {{{
    '''Perform substitutions in EVC to create and save EVCX.

    Does not include config since that goes into a separate file.
    '''

    def infoEvcx(evcx): # {{{
        '''Print information about EVCX.
        '''
        if not eva.infoFlag:
            return

        for k,v in evcx.items():
            msg = "%s %s <-- %s" % (v["type"], k, v["hook"])
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

    evcx = {}
    for measure in evc.get("measure", []):
        subs = measure["subs"] if "subs" in measure else []

        # `subs` guaranteed to be list of lists
        # Each `sub` guaranteed to be homogenous list.
        # Each `s` guaranteed to be string or int, but string may be a range.
        assert isinstance(subs, list)
        for sub in subs:
            assert isinstance(sub, list)
            for s in sub:
                # Unsure how practical other types are.
                assert isinstance(s, (int, str))

        # Build up new list of lists of usable strings.
        subs_ = []
        for sub in subs:
            sub_ = []
            for s in sub:
                # Range <start>..<stop>..<step>
                if isinstance(s, str) and reEvcRange.match(s):
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
            fullHook = evcSubstitute(measure["hook"], subsList)

            evcx[fullName] = {
                "hook": fullHook,
                "type": measure["type"],
                #"geq": geq,
                #"leq": leq,
            }

    verb("Saving... ", end='')
    saveToml(evcx, eva.paths.fname_evcx)
    verb("Done")

    infoEvcx(evcx)

    return evcx
# }}} def expandEvc

def evaInit(args): # {{{
    '''Read in EVC and VCD to create result directory like ./foo.eva/
    '''

    evc = loadEvc()
    checkEvc(evc)

    mkDirP(eva.paths.outdir)

    evcx = expandEvc(evc)

    eva.cfg = initCfg(evc["config"])

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

    # TODO: Gather common measurement types and initialize arrays.
    # TODO: How long should arrays be? Set a max in config?
    # evsEvent = np.zeros(shapeEvent, dtype=np.bool)
    # evsBinary = np.zeros(shapeBinary, dtype=np.bool)
    # evsNormal = np.ndarray(shapeNormal, dtype=np.float64)
    # TODO: Work through timechunks updating ndarrays.
    #with VcdReader(args.input) as vcd:
    #    checkEvcxWithVcd(evcx, vcd) # TODO: Some vcd paths must exist.


# }}} def evaInit

if __name__ == "__main__":
    assert False, "Not a standalone script."
