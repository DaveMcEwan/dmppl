
import toml

from dmppl.base import *

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

def loadEvc(args): # {{{
    '''Read EVC file with only basic checking.
    '''

    def infoEvc(evc): # {{{
        '''Print information about EVC.
        '''

        for k,v in evc.get("config", {}).items():
            msg = "%s = %s" % (k, v)
            info(msg, prefix="INFO:EVC:CONFIG: ")

        for m in evc.get("measure", []):
            msg = "%s <-- %s" % (m["name"], m["hook"])
            info(msg, prefix="INFO:EVC:MEASURE: ")

    # }}} def infoEvc

    eva.verb("Loading EVC... ", end='')

    try:
        evc = toml.load(eva.paths.fname_evc)
    except toml.decoder.TomlDecodeError as e:
        raise EVCError_TomlLoad(e)

    eva.verb("Done")

    if args.info:
        infoEvc(evc)

    return evc
# }}} def loadEvc

def initCfg(args, evcCfg): # {{{
    '''Fill in and save CFG.
    '''

    def infoCfg(cfg): # {{{
        '''Print information about CFG.
        '''

        for k,v in cfg.__dict__.items():
            msg = "%s = %s" % (k, v)
            info(msg, prefix="INFO:CFG: ")

    # }}} def infoCfg

    verb("Initializing CFG... ", end='')

    cfg = Bunch()
    cfg.__dict__.update(toml.load(eva.paths.share + "configDefault.toml"))
    cfg.__dict__.update(evcCfg)

    verb("Saving... ", end='')
    with open(eva.paths.fname_cfg, 'w') as fd:
        toml.dump(cfg.__dict__, fd)

    verb("Done")

    print(args.info)
    if args.info:
        infoCfg(cfg)

    return cfg
# }}} def initCfg

def processEvc(evc): # {{{
    '''Check EVC for sanity and expand into EVCX.
    '''


    return evcx
# }}} def processEvc

def evaInit(args): # {{{
    '''Read in EVC and VCD to create result directory like ./foo.eva/
    '''

    evc = loadEvc(args)

    mkDirP(eva.paths.outdir)

    eva.cfg = initCfg(args, evc["config"]) # TODO

    #evcx = processEvc(evc) # TODO: Some keys must exist and have choice values.
    # TODO: evcx must be saved in there too.

    #with VcdReader(fname_vcd) as vcd:
    #    checkEvcxWithVcd(evcx, vcd) # TODO: Some vcd paths must exist.
    #
    #
    #    if args.info:
    #        infoEvc(evc)
    #
    #    # NOTE: EVC and VCD have now been sanity checked so
    #    mkDirP(eva.paths.outdir)

    print(eva.paths.share)

# }}} def evaInit

if __name__ == "__main__":
    assert False, "Not a standalone script."
