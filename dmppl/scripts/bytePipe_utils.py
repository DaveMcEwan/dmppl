#!/usr/bin/env python3

# BytePipe (USB Host Utility)
# Dave McEwan 2020-04-20
#
# Plug in the board then run like:
#    python bytePipe_utils.py
#
# A bitfile implementing the usbfsBpRegMem logic is required to be build from
# the SystemVerilog2005 implementation
# The bitfile to immediately program the board with is found using the first of
# these methods:
# 1. Argument `--bitfile`
# 2. Environment variable `$BYTEPIPE_BITFILE`
# 3. The last item of the list `./usbfsBpRegMem.*.bin`
# 4. './usbfsBpRegMem.bin`
# Depends on PyPI package "tinyprog", which also depends on "pyserial".
#
# After programming, the board presents itself as a USB serial device.
# The device to connect to is found using the first of these methods:
# 1. Argument `--device`
# 2. Environment variable `$BYTEPIPE_DEVICE`
# 3. The last item of the list `/dev/ttyACM*`

# mypy --ignore-missing-imports testBytePipe.py

# Standard library
import argparse
import functools
import glob
import locale
import os
import subprocess
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, \
    Tuple, Union, cast

# PyPI
import serial

# git clone https://github.com/DaveMcEwan/dmppl.git && pip install -e ./dmppl
from dmppl.base import run, verb, dbg
from dmppl.bytePipe import BpMem, \
    bpReadSequential, bpWriteSequential, bpReadAddr, bpWriteAddr, \
    bpReset, bpPrintMem, bpAddrValuesToMem

__version__ = "0.1.0"

def getBitfilePath(argBitfile) -> str: # {{{

    envBitfile = os.environ.get("BYTEPIPE_BITFILE")
    orderedBitfiles = sorted(glob.glob("usbfsBpRegMem.*.bin"))

    if argBitfile is not None:
        ret = argBitfile
    elif envBitfile is not None:
        ret = envBitfile
    elif len(orderedBitfiles) > 0:
        ret = orderedBitfiles[-1]
    else:
        ret = os.sep.join((os.path.dirname(os.path.abspath(__file__)),
                           "usbfsBpRegMem.bin"))

    return ret
# }}} def getBitfilePath

def getDevicePath(argDevice) -> str: # {{{

    envDevice = os.environ.get("BYTEPIPE_DEVICE")
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

def actionBits(device, _args): # {{{
    rd:Callable = functools.partial(bpReadSequential, device)
    wr:Callable = functools.partial(bpWriteSequential, device)
    mem:Callable = bpAddrValuesToMem

    verb("Writing ones to all register locations...", end='')
    _ = mem( wr(list((addr, 0xff) for addr in range(1, 128))) )
    verb("Done")

    verb("Writing zeros to all register locations...", end='')
    ones:BpMem = mem( wr(list((addr, 0x00) for addr in range(1, 128))) )
    verb("Done")

    verb("Reading all register locations...", end='')
    zeros:BpMem = mem( rd(list(range(1, 128))) )
    verb("Checking writable bits...", end='')
    symdiff:BpMem = cast(BpMem, tuple(o ^ z for o,z in zip(ones, zeros)))
    verb("Done")

    bpPrintMem("Writable bits", symdiff)

    return # No return value
# }}} def actionBits

def actionDump(device, _args): # {{{
    rd:Callable = functools.partial(bpReadSequential, device)
    wr:Callable = functools.partial(bpWriteSequential, device)
    mem:Callable = bpAddrValuesToMem

    verb("Reading all register locations...", end='')
    init0:BpMem = mem( rd(list(range(128))) )
    verb("Done")

    bpPrintMem("Dump", init0)

    return # No return value
# }}} def actionDump

def actionGet(device, args): # {{{


    addr = abs(int(args.addr)) % 128
    nBytes = abs(int(args.nBytes))
    fname = args.file

    verb("Reading %dB @%d to %s..." % (nBytes, addr, fname), end='')
    with open(fname, 'wb') as fd:
        fd.write(bytes(bpReadAddr(device, addr, nBytes, args.record_time)))
    verb("Done")

    return # No return value
# }}} def actionGet

def actionPeek(device, args): # {{{
    rd:Callable = functools.partial(bpReadSequential, device)

    addr = abs(int(args.addr)) % 128

    verb("Peeking @%d..." % addr, end='')
    addrValue:BpAddrValue = rd([addr])[0]
    rdAddr, value = addrValue
    assert addr == rdAddr, (addr, rdAddr)
    verb("Done")

    print("%02x" % value)

    return # No return value
# }}} def actionPeek

def actionPoke(device, args): # {{{
    wr:Callable = functools.partial(bpWriteSequential, device)

    addr = abs(int(args.addr)) % 128
    value = abs(int(args.data)) % 256

    assert 0 != addr, "Writing @0 reserved for burst."

    verb("Poking %d@%d..." % (value, addr), end='')
    addrValue:BpAddrValue = wr([(addr, value)])[0]
    rdAddr, value = addrValue
    assert addr == rdAddr, (addr, rdAddr)
    verb("Done")

    return # No return value
# }}} def actionPoke

def actionPut(device, args): # {{{

    addr = abs(int(args.addr)) % 128
    nBytes = abs(int(args.nBytes))
    fname = args.file

    verb("Writing %dB @%d from %s..." % (nBytes, addr, fname), end='')
    with open(fname, 'rb') as fd:
        bpWriteAddr(device, addr, nBytes, fd.read(nBytes), args.record_time)
    verb("Done")

    return # No return value
# }}} def actionPut

def actionReset(device, _args): # {{{

    verb("Reseting BytePipe FSM...", end='')
    bpReset(device)
    verb("Done")

    return # No return value
# }}} def actionReset

def actionTest(device, _args): # {{{
    rd:Callable = functools.partial(bpReadSequential, device)
    wr:Callable = functools.partial(bpWriteSequential, device)
    mem:Callable = bpAddrValuesToMem

    verb("Reading all register locations...", end='')
    init0:BpMem = mem( rd(list(range(128))) )
    verb("Done")
    bpPrintMem("Initial values", init0)

    verb("Writing ones to all register locations...", end='')
    init1:BpMem = mem( wr(list((addr, 0xff) for addr in range(1, 128))) )
    verb("Done")
    bpPrintMem("Initial values (again)", init1)
    verb("Checking previous unchanged...", end='')
    allUnchanged:bool = all((i0 == i1) for i0,i1 in zip(init0[1:], init1[1:]))
    verb("Done")
    if not allUnchanged:
        verb("Warning: Some values changed!")

    verb("Writing zeros to all register locations...", end='')
    ones:BpMem = mem( wr(list((addr, 0x00) for addr in range(1, 128))) )
    verb("Done")
    bpPrintMem("Ones", ones)

    verb("Reading all register locations...", end='')
    zeros:BpMem = mem( rd(list(range(1, 128))) )
    verb("Checking writable bits...", end='')
    symdiff:BpMem = cast(BpMem, tuple(o ^ z for o,z in zip(ones, zeros)))
    verb("Done")
    bpPrintMem("Zeros", zeros)
    bpPrintMem("Writable bits", symdiff)

    verb("Writing unique values to all register locations...", end='')
    _ = mem( wr(list((addr, addr+10) for addr in range(1, 128))) )
    verb("Reading back...", end='')
    addrPlus10:BpMem = mem( rd(list(range(1, 128))) )
    verb("Done")
    bpPrintMem("mem[addr] <-- (addr+10)", addrPlus10)

    return # No return value
# }}} def actionTest

# {{{ argparser

argparser = argparse.ArgumentParser(
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("--bitfile",
    type=str,
    default=None,
    help="Bitfile for FPGA implementing hardware."
         " If None then try using environment variable `$BYTEPIPE_BITFILE`;"
         " Then try using the last item of `./usbfsBpRegMem.*.bin`;"
         " Then try using the bundled bitfile.")

argparser.add_argument("--no-prog",
    action="store_true",
    help="Don't attempt to program a bitfile."
         " Assume there's already a programmed device available.")

argparser.add_argument("--device",
    type=str,
    default=None,
    help="Serial device to connect to (immediately after progrmming)."
         " If None then try using environment variable `$BYTEPIPE_DEVICE`;"
         " Then try using the last item of `/dev/ttyACM*`.")

def argparseInt(s, width=None): # {{{
    assert isinstance(s, str), (type(s), s)
    assert width is None or isinstance(width, int), (type(width), width)

    hiOpen = None if width is None else 2**width

    i = int(s, 16) if s.startswith("0x") else int(s, 10)

    if width is None:
        pass
    elif not (0 <= i < hiOpen):
        msg = "Integer must be in [0, %d)" % hiOpen
        raise argparse.ArgumentTypeError(msg)
    return i
# }}} def argparseInt
argparser.add_argument("-a", "--addr",
    type=functools.partial(argparseInt, width=7),
    default=0,
    help="Address for peek,poke actions. (7b)")

argparser.add_argument("-d", "--data",
    type=functools.partial(argparseInt, width=8),
    default=0,
    help="Data for poke action. (8b)")

argparser.add_argument("-n", "--nBytes",
    type=argparseInt,
    default=0,
    help="Number of bytes to send/receive using put/get.")

argparser.add_argument("-f", "--file",
    type=str,
    default="bp.bin",
    help="Filepath of source/sink using put/get.")

argparser.add_argument("--record-time",
    action="store_true",
    help="Record progress for put/get to `bpRecordTime.csv`.")

actions = {
    "bits": actionBits,
    "dump": actionDump,
    "get": actionGet,
    "peek": actionPeek,
    "poke": actionPoke,
    "put": actionPut,
    "reset": actionReset,
    "test": actionTest,
}
argparser.add_argument("action",
    nargs='?',
    choices=actions.keys(),
    default="bits",
    help="Perform an action:"
         " Attempt to identify writable bits;"
         " Dump the contents of each location;"
         " Run a test;"
         " Reset the BytePipe FSM;"
         " Peek the value at --addr;"
         " Poke the value from --data to --addr;")

# }}} argparser

def main(args) -> int: # {{{
    '''
    1. Upload bitfile to TinyFPGA-BX (optional).
    2. Open connection to device.
    3. Discover writable bits.
    '''

    locale.setlocale(locale.LC_ALL, '')

    if args.no_prog:
        devicePath = getDevicePath(args.device)
    else:
        bitfile = getBitfilePath(args.bitfile)
        verb("Uploading bitfile %s ..." % bitfile, end='')
        assert 0 == uploadBitfile(bitfile)
        verb("Done")

        # Allow OS time to enumerate USB before looking for device.
        nAttempts = 10
        waitTime = 1 # seconds
        verb("Waiting up to %0.01fs..." % (nAttempts * waitTime), end='')

        maybeDevicePath_:Optional[str] = None
        for _ in range(nAttempts):
            time.sleep(waitTime)
            try:
                maybeDevicePath_ = getDevicePath(args.device)
                break
            except OSError:
                pass

        if maybeDevicePath_ is None:
            return 1
        else:
            devicePath = maybeDevicePath_

        verb("Done")


    # Keep lock on device to prevent other processes from accidentally messing
    # with the state machine.
    verb("Connecting to device %s" % devicePath)
    with serial.Serial(devicePath, timeout=1.0, write_timeout=1.0) as device:
        actions[args.action](device, args)

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

