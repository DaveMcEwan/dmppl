#!/usr/bin/env python3

# Correlator (USB Host Utility)
# Dave McEwan 2020-07-05
#
# Usage:
#   1. Plug in the board.
#   2. Program with `make prog` or with the `--prog` option of correlator-tui.
#   3. (optional) Experiment with correlator-tui to setup desired configuration.
#   4. Record correlation data for a number of windows:
#          `python3 correlator_record.py -o myData.out -n 123`
#      This gives a human-readable file with each window represented by a
#      fixed-size packet (5B).
#
# After programming, the board presents itself as a USB serial device.
# The device to connect to is found using the first of these methods:
# 1. Argument `-d,--device`
# 2. Environment variable `$CORRELATOR_DEVICE`
# 3. The last item of the list `/dev/ttyACM*`

# Standard library
import argparse
import enum
import functools
import locale
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from dmppl.base import run, verb, dbg, wrLines, grouper, \
    argparse_positiveInteger, argparse_nonNegativeInteger, \
    argparse_nonNegativeReal
from dmppl.bytePipe import bpReadSequential, bpWriteSequential, \
    bpReadAddr, bpWriteAddr

from dmppl.experiments.correlator.correlator_common import __version__, \
    SerialDevice, \
    maxSampleRate_kHz, \
    WindowShape, \
    getDevicePath, \
    HwReg, hwReadRegs, hwWriteRegs, detectNEngine, \
    calc_bitsPerWindow, \
    argparse_WindowLengthExp, argparse_WindowShape, \
    argparse_SamplePeriodExp, argparse_SampleJitterExp, \
    argparse_PwmSelect


def pktLines(device, nWindows:int, engineNum:int, hwRegs:Dict[HwReg, Any]) -> None: # {{{
    '''Generator yielding lines to be written to output.
    - Display progress/status line.
    - Read up to 50 packets in each burst.
      - pktPerBurst = maxRdBurst // nBytesPerWindow
      - 50 = 255B // 5B
    - Update progress/status line after each burst.
    - Append to output after each burst.
    '''
    rpt_ = ' '.join((
        '#',
        "device=%s" % device.name,
    ))
    yield rpt_
    rpt_ = ' '.join((
        '#',
        "HwRegRO",
        "PktfifoDepth=%d"       % hwRegs[HwReg.PktfifoDepth],
        "MaxWindowLengthExp=%d" % hwRegs[HwReg.MaxWindowLengthExp],
        "WindowPrecision=%d"    % hwRegs[HwReg.WindowPrecision],
        "MaxSamplePeriodExp=%d" % hwRegs[HwReg.MaxSamplePeriodExp],
        "MaxSampleJitterExp=%d" % hwRegs[HwReg.MaxSampleJitterExp],
    ))
    yield rpt_
    rpt_ = ' '.join((
        '#',
        "HwRegRW",
        "WindowLengthExp=%d" % hwRegs[HwReg.WindowLengthExp],
        "SamplePeriodExp=%d" % hwRegs[HwReg.SamplePeriodExp],
        "SampleJitterExp=%d" % hwRegs[HwReg.SampleJitterExp],
        "PwmSelect=%s"       % hwRegs[HwReg.PwmSelect].name,
        "XSelect=%d"         % hwRegs[HwReg.XSelect],
        "YSelect=%d"         % hwRegs[HwReg.YSelect],
    ))
    yield rpt_

    #rdBytePipe:Callable = functools.partial(bpReadSequential, device)
    wrBytePipe:Callable = functools.partial(bpWriteSequential, device)
    #rd:Callable = functools.partial(hwReadRegs, rdBytePipe)
    wr:Callable = functools.partial(hwWriteRegs, wrBytePipe)

    nBytesPerWindow:int = 5
    maxRdBurst:int = 255

    # NOTE: The term "rate" is used instead of "frequency" to reinforce that the
    # duty cycle is unbalanced so Fourier analysis will have high power in the
    # upper frequencies.
    samplePeriod_cycles:int = 2**hwRegs[HwReg.SamplePeriodExp]
    samplePeriod_ms:float = samplePeriod_cycles / float(maxSampleRate_kHz)
    sampleRate_kHz:float = 1.0 / samplePeriod_ms
    rpt_ = ' '.join((
        '#',
        "sampleStrobe",
        "averageRegularity=%d_cycles"    % samplePeriod_cycles,
        "averagePeriod=%0.06f_ms"        % samplePeriod_ms,
        "approximateRate=%0.06f_kHz"     % sampleRate_kHz,
    ))
    yield rpt_

    windowLength_samples:int = 2**hwRegs[HwReg.WindowLengthExp]
    windowPeriod_ms:float = windowLength_samples * samplePeriod_ms
    windowRate_kHz:float = 1.0 / windowPeriod_ms
    rpt_ = ' '.join((
        '#',
        'window',
        "length=%d_samples"     % windowLength_samples,
        "period_ms=%0.06f_ms"   % windowPeriod_ms,
        "rate=%0.06f_kHz"       % windowRate_kHz,
    ))
    yield rpt_

    totalNSamples:int = nWindows * windowLength_samples
    totalNBytes:int = nWindows * nBytesPerWindow
    totalTime_ms:float = nWindows * windowPeriod_ms
    totalBitrate_kbps:float = (8 * totalNBytes) / (1000 * totalTime_ms)
    rpt_ = ' '.join((
        '#',
        'dataset',
        "nWindows=%d" % nWindows,
        "time=%0.06f_ms" % totalTime_ms,
        "nSamples=%d" % totalNSamples,
        "pktfifoNBytes=%d" % totalNBytes,
        "pktfifoBitrate=%0.06f_kbps" % totalBitrate_kbps,
    ))
    yield rpt_

    nWindowPerBurst:int = maxRdBurst // nBytesPerWindow
    burstTime_ms:float = nWindowPerBurst * windowPeriod_ms
    nBytesPerBurst:int = nWindowPerBurst * nBytesPerWindow

    yield "winNum,countX,countY,countIsect,countSymdiff"
    lineFmt:str = ','.join(["%03d"]*5)

    # Flush the packet fifo.
    # The cycle this arrives at bpReg is the beginning of time for this dataset.
    verb("Flushing to begin dataset...", end='')
    wr(engineNum, {HwReg.PktfifoFlush: 1})
    verb("Done")

    nWindowsRemaining_ = nWindows
    burstNum_ = 0
    while (0 < nWindowsRemaining_):
        nBytesRemaining:int = nWindowsRemaining_ * nBytesPerWindow
        nBytesThisBurst:int = min(nBytesRemaining, nBytesPerBurst)

        assert ((nBytesThisBurst // nBytesPerWindow) == \
                int(nBytesThisBurst / nBytesPerWindow)), \
               (nBytesThisBurst, nBytesPerWindow)

        # Read burst from packet fifo.
        verb("Reading burst %d..." % burstNum_, end='')
        bs = bpReadAddr(device, HwReg.PktfifoRd.value, nBytesThisBurst)
        verb("Done")
        assert len(bs) == nBytesThisBurst, (len(bs), nBytesThisBurst)
        assert all(isinstance(b, int) for b in bs), bs
        assert all((0 <= b <= 255) for b in bs), bs

        # Translate bs to output line.
        for pkt in grouper(bs, nBytesPerWindow):
            assert len(pkt) == nBytesPerWindow, (len(pkt), nBytesPerWindow)
            assert all(isinstance(b, int) for b in pkt), pkt
            line = lineFmt % tuple(pkt)
            yield line

        nWindowsRemaining_ -= nWindowPerBurst
        burstNum_ += 1

# }}} def pktLines

# {{{ argparser

argparser = argparse.ArgumentParser(
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("-d", "--device",
    type=str,
    default=None,
    help="Serial device to connect to (immediately after programming)."
         " If None then try using environment variable `$CORRELATOR_DEVICE`;"
         " Then try using the last item of `/dev/ttyACM*`.")

argparser.add_argument("--timeout",
    type=functools.partial(argparse_nonNegativeReal, "timeout"),
    default=1.0,
    help="Maximum expected time (seconds) required to read a burst of 256B."
         " Passed directly to pySerial.")

argparser.add_argument("--init-windowLengthExp",
    type=argparse_WindowLengthExp,
    default=None,
    help="windowLength = 2**windowLengthExp  (samples)")

argparser.add_argument("--init-windowShape",
    type=argparse_WindowShape,
    default=None,
    help="Shape of sampling window function.")

argparser.add_argument("--init-samplePeriodExp",
    type=argparse_SamplePeriodExp,
    default=None,
    help="sampleRate = maxSampleRate * 2**-samplePeriodExp  (Hz)")

argparser.add_argument("--init-sampleJitterExp",
    type=argparse_SampleJitterExp,
    default=None,
    help="sampleJitter < 2**sampleJitterExp  (samples)")

argparser.add_argument("--init-pwmSelect",
    type=argparse_PwmSelect,
    default=None,
    help="Data source for LED brightness, either string like 'Cov' or integer.")

argparser.add_argument("--init-xSelect",
    type=functools.partial(argparse_nonNegativeInteger, "init-xSelect"),
    default=None,
    help="Probe number for X input.")

argparser.add_argument("--init-ySelect",
    type=functools.partial(argparse_nonNegativeInteger, "init-ySelect"),
    default=None,
    help="Probe number for Y input.")

argparser.add_argument("--prng-seed",
    type=int,
    default=None,
    help="Seed for xoshiro128+ PRNG used for sampling jitter.")

argparser.add_argument("--engine",
    type=functools.partial(argparse_nonNegativeInteger, "engine"),
    default=0,
    help="Engine number.")

argparser.add_argument("-o", "--output",
    type=str,
    default=None,
    help="File to record data, or STDOUT if not given.")

argparser.add_argument("-n", "--nWindows",
    type=functools.partial(argparse_positiveInteger, "nWindows"),
    default=10,
    help="Number of windows to record.")

# }}} argparser

def main(args) -> int: # {{{
    '''
    1. Open connection to device.
    2. Read config RO registers.
    3. Write config RW registers if --init-* is used.
    4. Read/check config RW registers.
    5. Record data with burst reads from pktfifo.
    '''

    locale.setlocale(locale.LC_ALL, '')

    devicePath = getDevicePath(args.device)

    # Keep lock on device to prevent other processes from accidentally messing
    # with the state machine.
    with SerialDevice(devicePath, exclusive=True,
                       rdTimeout=args.timeout, wrTimeout=args.timeout,
                       connectNAttempt=50, connectTimeout=0.2) as device:
        rdBytePipe:Callable = functools.partial(bpReadSequential, device)
        wrBytePipe:Callable = functools.partial(bpWriteSequential, device)
        rd:Callable = functools.partial(hwReadRegs, rdBytePipe)
        wr:Callable = functools.partial(hwWriteRegs, wrBytePipe)

        verb("Detecting number of engines...", end='')
        nEngine:int = detectNEngine(rd)
        assert args.engine < nEngine, "--engine must be less than %d" % nEngine
        engineNum:int = args.engine
        verb("Done")

        verb("Reading RO registers...", end='')
        hwRegsRO:Dict[HwReg, Any] = rd(engineNum, (
            HwReg.PktfifoDepth,
            HwReg.MaxWindowLengthExp,
            HwReg.WindowPrecision,
            HwReg.MaxSamplePeriodExp,
            HwReg.MaxSampleJitterExp,
        ))
        verb("Done")

        # Gather registers required for initialization.
        initRegsRW:Dict[HwReg, Any] = {}
        if args.init_windowLengthExp is not None:
            initRegsRW[HwReg.WindowLengthExp] = args.init_windowLengthExp
        if args.init_windowShape is not None:
            initRegsRW[HwReg.WindowShape] = args.init_windowShape
        if args.init_samplePeriodExp is not None:
            initRegsRW[HwReg.SamplePeriodExp] = args.init_samplePeriodExp
        if args.init_sampleJitterExp is not None:
            initRegsRW[HwReg.SampleJitterExp] = args.init_sampleJitterExp
        if args.init_pwmSelect is not None:
            initRegsRW[HwReg.PwmSelect] = args.init_pwmSelect
        if args.init_xSelect is not None:
            initRegsRW[HwReg.XSelect] = args.init_xSelect
        if args.init_ySelect is not None:
            initRegsRW[HwReg.YSelect] = args.init_ySelect


        if 0 < len(initRegsRW):
            verb("Initializing RW registers...", end='')
            wr(engineNum, initRegsRW)
            verb("Checking...", end='')
            hwRegsRW:Dict[HwReg, Any] = rd(engineNum, initRegsRW.keys())
            assert all(initRegsRW[k] == v for k,v in hwRegsRW.items()), hwRegsRW
            verb("Done")


        if args.prng_seed is not None:
            seed:int = abs(args.prng_seed)
            verb("Initializing PRNG (xoshiro128+ %s)..." % hex(seed), end='')
            bpWriteAddr(device, HwReg.PrngSeed.value, 16, [0]*16)
            bpWriteAddr(device, HwReg.PrngSeed.value, 4, [
                (seed >> 3*8) & 0xff,
                (seed >> 2*8) & 0xff,
                (seed >> 1*8) & 0xff,
                (seed >> 0*8) & 0xff,
            ])
            verb("Done")


        verb("Reading RW registers...", end='')
        hwRegsRW:Dict[HwReg, Any] = rd(engineNum, [
            HwReg.WindowLengthExp,
            HwReg.WindowShape,
            HwReg.SamplePeriodExp,
            HwReg.SampleJitterExp,
            HwReg.PwmSelect,
            HwReg.XSelect,
            HwReg.YSelect,
        ])
        verb("Done")

        try:
            verb("Recording...")
            nLinesWritten, wrSuccess = \
                wrLines(args.output, pktLines(device,
                                              args.nWindows, engineNum,
                                              {**hwRegsRO, **hwRegsRW}))
            verb("Recording %s" % ("complete" if wrSuccess else
                                   "FAILURE nLinesWritten=%d" % nLinesWritten))
        except KeyboardInterrupt:
            verb("KeyboardInterrupt. Exiting.")

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

