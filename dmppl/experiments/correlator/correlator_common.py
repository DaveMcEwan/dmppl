
# Standard library
import argparse
import enum
import glob
import os
import subprocess
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

# PyPI
import serial

from dmppl.base import verb, asrtNumber
from dmppl.bytePipe import BpAddrs, BpAddrValues, BpMem, \
    bpReadSequential, bpWriteSequential, bpPrintMem, bpAddrValuesToMem, \
    bpWriteAddr

__version__ = "0.1.0"

maxSampleRate_kHz:int = 48000

# NOTE: Must match addresses in bpReg.v
@enum.unique
class HwReg(enum.Enum): # {{{
    # Rfifo
    PktfifoRd               = 1

    # WO
    PktfifoFlush            = 2
    PrngSeed                = 3

    # Static, RO
    PktfifoDepth            = 4
    MaxWindowLengthExp      = 5
    WindowPrecision         = 6
    MaxSamplePeriodExp      = 7
    MaxSampleJitterExp      = 8

    # Dynamic, RW
    WindowLengthExp         = 9
    WindowShape             = 10
    SamplePeriodExp         = 11
    SampleJitterExp         = 12
    PwmSelect               = 13
    XSelect                 = 14
    YSelect                 = 15

# }}} Enum HwReg
mapHwAddrToHwReg:Dict[int, HwReg] = {e.value: e for e in HwReg}

@enum.unique
class WindowShape(enum.Enum): # {{{
    Rectangular = 0
    Logdrop     = 1
# }}} class WindowShape

@enum.unique
class PwmSelect(enum.Enum): # {{{
    WinNum          = 0
    X               = 1
    Y               = 2
    Isect           = 3
    Symdiff         = 4
    # NOTE: No unicode in enum names.
    # That allows argparse_PwmSelect to take a string.
    Cov             = 5
    Dep             = 6
    Ham             = 7
# }}} class PwmSelect

mapHwRegToEnum = {
    HwReg.WindowShape:  WindowShape,
    HwReg.PwmSelect:    PwmSelect,
}

engineAddrStride:int = 16

def getBitfilePath(argBitfile) -> str: # {{{

    envBitfile = os.environ.get("CORRELATOR_BITFILE")
    orderedBitfiles = sorted(glob.glob("correlator.*.bin"))

    if argBitfile is not None:
        ret = argBitfile
    elif envBitfile is not None:
        ret = envBitfile
    elif len(orderedBitfiles) > 0:
        ret = orderedBitfiles[-1]
    else:
        ret = os.sep.join((os.path.dirname(os.path.abspath(__file__)),
                           "correlator.bin"))

    return ret
# }}} def getBitfilePath

def getDevicePath(argDevice) -> str: # {{{

    envDevice = os.environ.get("CORRELATOR_DEVICE")
    orderedDevices = sorted(glob.glob("/dev/ttyACM*"))

    if argDevice is not None:
        ret = argDevice
    elif envDevice is not None:
        ret = envDevice
    elif len(orderedDevices) > 0:
        ret = orderedDevices[-1]
    else:
        raise OSError("Device not found. Use --help for details.")

    return ret
# }}} def getDevicePath

def uploadBitfile(bitfile): # {{{

    p = subprocess.run(("tinyprog", "-p", bitfile))

    return p.returncode
# }}} def uploadBitfile

def hwReadRegs(rd, engineNum:int, keys:Iterable[HwReg]) -> Dict[HwReg, Any]: # {{{
    '''Wrapper for reader function including checks and type conversion.

    Reader function must take an iterable of integers representing address,
    and return an iterable of (addr, value) pairs.
    rd :: [int] -> [(int, int)]
    '''
    addrBase:int = engineNum * engineAddrStride
    addrs:List[int] = [addrBase + k.value for k in keys]
    values:Iterable[Tuple[int, int]] = rd(addrs)
    assert len(keys) == len(values)

    ret_ = {}
    for k,(a,v) in zip(keys, values):
        assert isinstance(k, HwReg), k
        assert isinstance(a, int), a
        assert isinstance(v, int), v
        assert a == (addrBase + k.value), (a, k.value, engineNum)

        if k in mapHwRegToEnum.keys():
            ret_[k] = mapHwRegToEnum[k](v)
        else:
            ret_[k] = v

    return ret_
# }}} def hwReadRegs

def hwWriteRegs(wr, engineNum:int, keyValues:Dict[HwReg, Any]) -> Dict[HwReg, Any]: # {{{
    '''Wrapper for writer function including checks and type conversion.

    Writer function must take an iterable of (addr, value) pairs,
    and return an iterable of (addr, value) pairs.
    wr :: [(int, int)] -> [(int, int)]
    '''
    addrBase:int = engineNum * engineAddrStride

    addrValues:List[Tuple[int, int]] = \
        [(addrBase + k.value, (v.value if isinstance(v, enum.Enum) else v)) \
         for k,v in keyValues.items()]

    ret = wr(addrValues)

    return ret
# }}} def hwWriteRegs

def detectNEngine(rd) -> int: # {{{
    '''Detect number of engines available.

    Read the same RO register for all engines and report back the index of the
    highest non-zero result.

    Reader function must take an iterable of HwReg representing address,
    and return an dict of values keyed by address.
    rd :: [HwReg] -> {HwReg: int}
    '''
    engineDetectAddr = HwReg.PktfifoDepth
    nEngineMax:int = 8

    ret:int = max([i+1 for i in range(nEngineMax) \
                     if 0 != rd(i, (engineDetectAddr,))[engineDetectAddr]])

    return ret
# }}} def detectNEngine

def calc_bitsPerWindow(hwRegs:Dict[HwReg, Any]) -> int: # {{{

    precision:int = hwRegs[HwReg.WindowPrecision] # bits
    nInputs:int = 2 # unitless

    ret:int = precision * (nInputs**2 - nInputs)

    return ret
# }}} def calc_bitsPerWindow

def argparse_WindowLengthExp(s): # {{{
    i = int(s)
    if not (0 <= i <= 99):
        msg = "Window length exponent must be in [2, maxWindowLengthExp]"
        raise argparse.ArgumentTypeError(msg)
    return i
# }}} def argparse_WindowLengthExp

def argparse_WindowShape(s): # {{{
    i = s.lower()
    if "rectangular" == i:
        ret = WindowShape.Rectangular
    elif "logdrop" == i:
        ret = WindowShape.Logdrop
    else:
        msg = "Window shape must be in {RECTANGULAR, LOGDROP}"
        raise argparse.ArgumentTypeError(msg)
    return ret
# }}} def argparse_WindowShape

def argparse_SamplePeriodExp(s): # {{{
    i = int(s)
    if not (0 <= i <= 99):
        msg = "Sample rate divisor exponent must be in [0, maxSamplePeriodExp]"
        raise argparse.ArgumentTypeError(msg)
    return i
# }}} def argparse_SamplePeriodExp

def argparse_SampleJitterExp(s): # {{{
    i = int(s)
    if not (0 <= i <= 99):
        msg = "Sample jitter exponent must be in [0, maxSampleJitterExp)"
        raise argparse.ArgumentTypeError(msg)
    return i
# }}} def argparse_SampleJitterExp

def argparse_PwmSelect(s): # {{{

    sClean = s.encode("ascii", "ignore").decode("ascii").casefold()

    try:
        i = int(sClean)
        if not (0 <= i <= 7):
            msg = "LED source must be in [0, 7]"
            raise argparse.ArgumentTypeError(msg)

    except ValueError:
        mapNameToInt = {e.name.casefold(): e.value for e in PwmSelect}

        if sClean not in mapNameToInt.keys():
            allowedNames = ','.join(e.name for e in PwmSelect)
            msg = "LED source must be in {%s}" % allowedNames
            raise argparse.ArgumentTypeError(msg)

        i = mapNameToInt[sClean]

    return PwmSelect(i)
# }}} def argparse_PwmSelect

class SerialDevice(object): # {{{
    '''Context manager around PySerial to attempt connection until resource is
       free.
    '''
    def __init__(self, path=None, exclusive=True,
                       rdTimeout=1.0, wrTimeout=1.0,
                       connectNAttempt=1, connectTimeout=1.0):

        assert isinstance(path, str), (type(path), path)
        self.path = str(path)
        self.exclusive = bool(exclusive)
        self.rdTimeout = float(rdTimeout)
        self.wrTimeout = float(wrTimeout)

        asrtNumber(connectNAttempt, geq=1)
        asrtNumber(connectTimeout, geq=0.01) # Minimum 10ms between attempts.
        self.connectNAttempt = int(connectNAttempt)
        self.connectTimeout = float(connectTimeout)

    def __enter__(self):

        exception_ = None

        for i in range(self.connectNAttempt):
            if 0 != i:
                time.sleep(self.connectTimeout)

            verb("Attempt %d/%d connecting SerialDevice %s ... " % \
                 (i+1, self.connectNAttempt, self.path), end='')
            try:

                self.port = serial.Serial(self.path,
                                          timeout=self.rdTimeout,
                                          write_timeout=self.wrTimeout,
                                          exclusive=self.exclusive)
                self.port.open()
            except Exception as e:
                exception_ = e

            if hasattr(self, "port") and self.port.is_open:
                verb("Success")
                break
            else:
                verb("Failure")


        if not (hasattr(self, "port") and self.port.is_open):
            raise exception_

        return self.port

    def __exit__(self, exceptionType, exceptionValue, exceptionTraceback):
        self.port.close()

# }}} class SerialDevice

