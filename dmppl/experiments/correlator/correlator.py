#!/usr/bin/env python3

# Correlator (USB Host Utility)
# Dave McEwan 2020-04-12
#
# Plug in the board then run like:
#    correlator.py &
#
# A bitfile implementing the correlator logic is required to be build from
# the SystemVerilog2005 implementation
# The bitfile to immediately program the board with is found using the first of
# these methods:
# 1. Argument `-b,--bitfile`
# 2. Environment variable `$CORRELATOR_BITFILE`
# 3. The last item of the list `correlator.*.bin`
#
# After programming, the board presents itself as a USB serial device.
# The device to connect to is found using the first of these methods:
# 1. Argument `-d,--device`
# 2. Environment variable `$CORRELATOR_DEVICE`
# 3. The last item of the list `/dev/ttyUSB*`

import argparse
import curses
import enum
import functools
import locale
import sys
import time

from dmppl.base import run, verb, dbg
from dmppl.color import cursesInitPairs, whiteBlue, whiteRed, blackRed, greenBlack

__version__ = "0.1.0"

@enum.unique
class HwReg(enum.Enum): # {{{
    # Static, RO
    Precision               = enum.auto()
    MetricA                 = enum.auto()
    MetricB                 = enum.auto()
    MaxNInputs              = enum.auto()
    MaxWindowLengthExp      = enum.auto()
    MaxSampleRateNegExp     = enum.auto()
    MaxSampleJitterNegExp   = enum.auto()

    # Dynamic, RW
    NInputs                 = enum.auto()
    WindowLengthExp         = enum.auto()
    SampleRateNegExp        = enum.auto()
    SampleMode              = enum.auto()
    SampleJitterNegExp      = enum.auto()
# }}} class HwReg

@enum.unique
class SampleMode(enum.Enum): # {{{
    Periodic    = enum.auto()
    Nonperiodic = enum.auto()
# }}} class SampleMode

mapMetricIntToStr = {
    1: "Ċls",
    2: "Ċos",
    3: "Ċov",
    4: "Ḋep",
    5: "Ḣam",
    6: "Ṫmt",
}

def getBitfilePath(args): # {{{

    ret = "foo"
    return ret
# }}} def getBitfilePath

def getDevicePath(args): # {{{

    ret = "/dev/null"
    return ret
# }}} def getDevicePath

def uploadBitfile(args): # {{{

    bitfile = getBitfilePath(args)

    return 0
# }}} def uploadBitfile

def hwReadRegs(device, keys): # {{{
    dummyRegs = {
        HwReg.Precision                 : 8,
        HwReg.MetricA                   : 3,
        HwReg.MetricB                   : 4,
        HwReg.MaxNInputs                : 5,
        HwReg.MaxWindowLengthExp        : 32,
        HwReg.MaxSampleRateNegExp       : 32,
        HwReg.MaxSampleJitterNegExp     : 32,
        HwReg.NInputs                   : 5,
        HwReg.WindowLengthExp           : 6,
        HwReg.SampleRateNegExp          : 7,
        HwReg.SampleMode                : SampleMode.Periodic,
        HwReg.SampleJitterNegExp        : 8,
    }
    return {k: dummyRegs[k] for k in keys}
# }}} def hwReadRegs

def hwWriteRegs(device, keyValues): # {{{

    return 0
# }}} def hwWriteRegs

def drawStr(s, x=0, y=0, colorPair=0, win=None,
            encoding=locale.getpreferredencoding()): # {{{
    '''Intended to be used with functools.partial()
    '''
    # TODO: Check length
    b = s.encode(encoding)
    return win.addstr(y, x, b, curses.color_pair(colorPair))
# }}} def drawStr

def guiTitle(win, device, regs): # {{{
    '''Draw the static title section.
    Intended to be called only once.

    <appName> ... <precision> <metricA> <metricB> ... <devicePath>
    '''

    draw = functools.partial(drawStr, y=0, colorPair=whiteBlue, win=win)

    height, width = win.getmaxyx()
    maxX = width - 1 # Can't write rightmost character.

    appName = "Correlator"
    devicePath = device.name
    precision = "%db" % regs[HwReg.Precision]
    metricA = mapMetricIntToStr[regs[HwReg.MetricA]]
    metricB = mapMetricIntToStr[regs[HwReg.MetricB]]

    left = appName
    mid = ' '.join((precision, metricA, metricB))
    right = devicePath

    midBegin = (width // 2) - (len(mid) // 2)
    rightBegin = maxX - len(right)

    draw(" "*maxX, 0)
    draw(left, 0)
    draw(mid, midBegin)
    draw(right, rightBegin)
    win.refresh()

    return # No return value
# }}} def guiTitle

def guiStatus(win, hwUpdated): # {{{
    '''Draw/redraw the status section.

    Up/Down: Move ... Left/Right: Change ... Enter: Send
    '''

    draw = functools.partial(drawStr, y=0, colorPair=whiteBlue, win=win)
    drawHC = functools.partial(drawStr, y=0, colorPair=whiteRed, win=win)

    height, width = win.getmaxyx()
    maxX = width - 1 # Can't write rightmost character.

    left = "Up/Down: Move"
    mid = "Left/Right: Change"
    right = "Enter: Send"

    midBegin = (width // 2) - (len(mid) // 2)
    rightBegin = maxX - len(right)

    draw(" "*maxX, 0)
    draw(left, 0)
    draw(mid, midBegin)
    if hwUpdated:
        draw(right, rightBegin)
    else:
        drawHC(right, rightBegin)

    win.refresh()

    return # No return value
# }}} def guiStatus

def gui(scr, device, regs): # {{{
    '''
    Window objects:
    - scr: All available screen space.
    - full: Rectangle in the centre of scr.
    - titl: Single line at top of full for title and static info.
    - inpt: Rectangle below titl for dynamic inputs.
    - otpt: Rectangle below inpt for dynamic outputs.
    - stus: Single line at bottom of full for instructions and dynamic status.

    Each of the window objects is refreshed individually.
    '''

    # {{{ Define layout
    # Top, Bottom, Left, and Right positions are relative to scr.

    # Screen is passed as first arg from curses.wrapper().
    scrLines, scrChars = scr.getmaxyx()
    scrTop, scrLeft = 0, 0
    scrBottom, scrRight = scrLines - 1, scrChars - 1

    # The "full" window is a rectangle in the middle of the screen.
    # A box is drawn around full using an extra character on each side.
    fullLines, fullChars = 30, 80
    fullTop, fullLeft = \
        (scrLines - fullLines) // 2, \
        (scrChars - fullChars) // 2
    fullBottom, fullRight = fullTop + fullLines - 1, fullLeft + fullChars - 1
    full = curses.newwin(fullLines+1, fullChars+2, fullTop, fullLeft-1)

    # The "titl" window is a single line at the top of full.
    titlLines, titlChars = 1, fullChars
    titlTop, titlLeft = fullTop + 1, fullLeft
    titlBottom, titlRight = titlTop + titlLines - 1, titlLeft + titlChars - 1
    titl = curses.newwin(titlLines, titlChars+1, titlTop, titlLeft)
    titl.clear()

    # The "inpt" window is a fixed height rectangle below titl.
    inptLines, inptChars = 5, fullChars
    inptTop, inptLeft = titlTop + 1, fullLeft
    inptBottom, inptRight = inptTop + inptLines - 1, inptLeft + inptChars - 1
    inpt = curses.newwin(inptLines, inptChars+1, inptTop, inptLeft)

    # The "stus" window is a single line at the bottom of full.
    # NOTE: Defined bottom-up rather than top-down.
    stusLines, stusChars = 1, fullChars
    stusBottom, stusLeft = fullBottom, fullLeft
    stusTop, stusRight = stusBottom - stusLines + 1, stusLeft + stusChars - 1
    stus = curses.newwin(stusLines, stusChars+1, stusTop, stusLeft)

    # The "otpt" window is a rectangle below inpt which occupies all remaining
    # lines between inpt and stus.
    otptLines, otptChars = \
        fullLines - titlLines - inptLines - stusLines, \
        fullChars
    otptTop, otptLeft = inptBottom + 1, fullLeft
    otptBottom, otptRight = otptTop + otptLines - 1, otptLeft + otptChars - 1
    otpt = curses.newwin(otptLines, otptChars+1, otptTop, otptLeft)

    # }}} Define layout

    curses.curs_set(0) # Hide the cursor.
    cursesInitPairs() # Initialize colors
    scr.clear()
    #full.box()

    guiTitle(titl, device, regs)

    drawInpt = functools.partial(drawStr, colorPair=greenBlack, win=inpt)
    drawOtpt = functools.partial(drawStr, colorPair=blackRed, win=otpt)
    for i in range(inptLines):
        drawInpt(str(i)[-1]*fullChars, 0, i)
    for i in range(otptLines):
        drawOtpt(str(i)[-1]*fullChars, 0, i)
    inpt.refresh()
    otpt.refresh()

    guiStatus(stus, False)
    stus.refresh()

    stus.getch()

    return # No return value
# }}} def gui

# {{{ argparser

argparser = argparse.ArgumentParser(
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

argparser.add_argument("-b", "--bitfile",
    type=str,
    default=None,
    help="Bitfile for FPGA implementing correlator hardware.")

argparser.add_argument("-d", "--device",
    type=str,
    default=None,
    help="Serial device to connect to (immediately after progrmming).")

def argparseNInputs(s): # {{{
    i = int(s)
    if not (2 <= i <= 99):
        msg = "Number of active inputs must be in [2, maxNInputs]"
        raise argparse.ArgumentTypeError(msg)
    return i
# }}} def argparseNInputs
argparser.add_argument("--init-nInputs",
    type=argparseNInputs,
    default=2,
    help="Number of inputs to calculate correlation between.")

def argparseWindowLengthExp(s): # {{{
    i = int(s)
    if not (0 <= i <= 99):
        msg = "Window length exponent must be in [2, maxWindowLengthExp]"
        raise argparse.ArgumentTypeError(msg)
    return i
# }}} def argparseWindowLengthExp
argparser.add_argument("--init-windowLengthExp",
    type=argparseWindowLengthExp,
    default=10,
    help="windowLength = 2**windowLengthExp  (samples)")

def argparseSampleRateNegExp(s): # {{{
    i = int(s)
    if not (0 <= i <= 99):
        msg = "Sample rate divisor exponent must be in [0, maxSampleRateNegExp]"
        raise argparse.ArgumentTypeError(msg)
    return i
# }}} def argparseSampleRateNegExp
argparser.add_argument("--init-sampleRateNegExp",
    type=argparseSampleRateNegExp,
    default=0,
    help="sampleRate = maxSampleRate * 2**-sampleRateNegExp  (Hz)")

def argparseSampleMode(s): # {{{
    i = s.lower()
    if "periodic" == i:
        ret = SampleMode.Periodic
    elif "nonperiodic" == i:
        ret = SampleMode.Nonperiodic
    else:
        msg = "Sample mode must be in {PERIODIC, NONPERIODIC}"
        raise argparse.ArgumentTypeError(msg)
    return ret
# }}} def argparseSampleMode
argparser.add_argument("--init-sampleMode",
    type=argparseSampleMode,
    default=SampleMode.Periodic,
    help="Sample periodically or non-periodically (using pseudo-random jitter)")

def argparseSampleJitterNegExp(s): # {{{
    i = int(s)
    if not (1 <= i <= 99):
        msg = "Sample rate divisor exponent must be in [1, maxSampleJitterNegExp]"
        raise argparse.ArgumentTypeError(msg)
    return i
# }}} def argparseSampleJitterNegExp
argparser.add_argument("--init-sampleJitterNegExp",
    type=argparseSampleJitterNegExp,
    default=1,
    help="sampleJitter = windowLength * 2**-sampleJitterNegExp  (samples)")

# }}} argparser

def main(args): # {{{
    '''
    1. Upload bitfile to FPGA.
    2. Open connection to device.
    3. Read config RO registers.
    4. Write config RW registers.
    5. Read/check config RW registers.
    6. Initialize GUI
    7. GUI output loop:
        1. Sleep for refresh period.
        2. Read results RO registers.
        2. Update results section.
    8. GUI config loop:
        1. Wait for <Enter>
        2. Write config RW registers.
        3. Read config RW registers, check they're what was written.
    9. GUI input loop:
        1. Wait for keypress.
        2. Handle keypress by moving highlighted line or changing value.
    '''

    locale.setlocale(locale.LC_ALL, '')

    verb("Uploading bitfile...", end='')
    uploadBitfile(args)
    verb("Done")

    # TODO: Search for device every 100ms instead of just sleeping, with 1s
    # timeout to give useful error message.
    #time.sleep(1) # Allow OS to enumerate USB.

    # Keep lock on device to prevent other processes from accidentally messing
    # with the state machine.
    verb("Connecting to device")
    with open(getDevicePath(args), "w+b") as device:
        rd = functools.partial(hwReadRegs, device)
        wr = functools.partial(hwWriteRegs, device)

        verb("Reading RO registers...", end='')
        regsRO = rd((HwReg.Precision,
                     HwReg.MetricA,
                     HwReg.MetricB,
                     HwReg.MaxNInputs,
                     HwReg.MaxWindowLengthExp,
                     HwReg.MaxSampleRateNegExp,
                     HwReg.MaxSampleJitterNegExp))
        verb("Done")

        verb("Initializing RW registers...", end='')
        initRegsRW = {
            HwReg.NInputs:              args.init_nInputs,
            HwReg.WindowLengthExp:      args.init_windowLengthExp,
            HwReg.SampleRateNegExp:     args.init_sampleRateNegExp,
            HwReg.SampleMode:           args.init_sampleMode,
            HwReg.SampleJitterNegExp:   args.init_sampleJitterNegExp,
        }
        wr(initRegsRW)
        verb("Checking...", end='')
        regsRW = rd(initRegsRW.keys())
        # TODO: uncomment
        #assert all(initRegsRW[k] == v for k,v in regsRW.items()), regsRW
        verb("Done")

        try:
            verb("Starting GUI (curses)...")
            curses.wrapper(gui, device, {**regsRO, **regsRW})
            verb("GUI Done")
        except KeyboardInterrupt:
            verb("KeyboardInterrupt. Exiting.")

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

