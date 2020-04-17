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
from typing import Any, Callable, Dict, List, Optional, Union

from dmppl.base import run, verb, dbg
from dmppl.color import CursesWindow, cursesInitPairs, \
    whiteBlue, whiteRed, blackRed, greenBlack

__version__ = "0.1.0"

maxSampleRateMHz:int = 48

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
# }}} Enum HwReg

@enum.unique
class SampleMode(enum.Enum): # {{{
    Nonjitter   = enum.auto()
    Nonperiodic = enum.auto()
# }}} class SampleMode

@enum.unique
class UpdateMode(enum.Enum): # {{{
    Batch       = enum.auto()
    Interactive = enum.auto()
# }}} class UpdateMode

@enum.unique
class GuiReg(enum.Enum): # {{{
    # Software-only
    UpdateMode      = enum.auto()

    # Derived from hardware
    Enable          = enum.auto()
    NInputs         = enum.auto()
    WindowLength    = enum.auto()
    SampleMode      = enum.auto()
    SampleRate      = enum.auto()
    SampleJitter    = enum.auto()
# }}} Enum GuiReg

# NOTE: Some values are carefully updated with string substitution on the
# initial read of the RO registers.
# TODO: Should be enum called GuiReg
mapGuiRegToDomain_:Dict[GuiReg, str] = { # {{{
    # Controls no hardware register (GUI state only).
    GuiReg.UpdateMode: "∊ {%s}" % ", ".join(m.name for m in UpdateMode),

    # Controls register "NInputs" (toggle between 0 and previous NInputs).
    GuiReg.Enable: "∊ {True, False}",

    # Controls register "NInputs".
    # Domain defined by HwReg.MaxNInputs
    GuiReg.NInputs: "∊ ℤ ∩ [2, %d]",

    # Controls register "WindowLengthExp".
    # Domain defined by HwReg.MaxWindowLengthExp
    GuiReg.WindowLength: "(samples) = 2**w; w ∊ ℤ ∩ [1, %d]",

    # Controls register "SampleMode".
    GuiReg.SampleMode: "∊ {%s}" % ", ".join(m.name for m in SampleMode),

    # Controls register "SampleRateNegExp".
    # Domain defined by HwReg.MaxSampleRateNegExp
    GuiReg.SampleRate: "(MHz) = %d/2**r; r ∊ ℤ ∩ [0, %%d]" % maxSampleRateMHz,

    # Controls register "SampleJitterNegExp".
    # Domain defined by HwReg.MaxSampleJitterNegExp
    GuiReg.SampleJitter: "(samples) = WindowLength/2**j; j ∊ ℤ ∩ [1, %d]",
} # }}}

mapMetricIntToStr:Dict[int, str] = { # {{{
    1: "Ċls",
    2: "Ċos",
    3: "Ċov",
    4: "Ḋep",
    5: "Ḣam",
    6: "Ṫmt",
} # }}}

def getBitfilePath(args) -> str: # {{{

    ret = "foo"
    return ret
# }}} def getBitfilePath

def getDevicePath(args) -> str: # {{{

    ret = "/dev/null"
    return ret
# }}} def getDevicePath

def uploadBitfile(args): # {{{

    bitfile = getBitfilePath(args)

    return 0
# }}} def uploadBitfile

def hwReadRegs(device, keys) -> Dict[HwReg, Any]: # {{{
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
        HwReg.SampleMode                : SampleMode.Nonjitter,
        HwReg.SampleJitterNegExp        : 8,
    }
    return {k: dummyRegs[k] for k in keys}
# }}} def hwReadRegs

def hwWriteRegs(device, keyValues): # {{{

    return 0
# }}} def hwWriteRegs

def hwRegsToGuiRegs(hwRegs:Dict[HwReg, Any]) -> Dict[GuiReg, Any]: # {{{
    enable:bool = (0 == hwRegs[HwReg.NInputs])

    windowLength:int = 2**hwRegs[HwReg.WindowLengthExp]

    sampleJitter:Optional[int] = None \
        if hwRegs[HwReg.SampleMode] == SampleMode.Nonjitter else \
        (windowLength // 2**hwRegs[HwReg.SampleJitterNegExp])

    sampleRate = float(maxSampleRateMHz) / 2**hwRegs[HwReg.SampleRateNegExp]
    ret = {
        GuiReg.Enable:       enable,
        GuiReg.NInputs:      hwRegs[HwReg.NInputs],
        GuiReg.WindowLength: windowLength,
        GuiReg.SampleMode:   hwRegs[HwReg.SampleMode],
        GuiReg.SampleRate:   sampleRate,
        GuiReg.SampleJitter: '-' if sampleJitter is None else sampleJitter,
    }
    return ret
# }}} def hwRegsToGuiRegs

class FullWindow(CursesWindow): # {{{
    '''The "full" window is a rectangle in the middle of the screen.

    +----------- ... -------------+
    |Title...                     |
    |                             |
    | inputs/parameters           |
    |                             |
    ...                         ...
    |                             |
    | outputs/results             |
    |                             |
    |Status...                    |
    +----------- ... -------------+
    '''
    def drawTitle(self, device, hwRegs) -> None: # {{{
        '''Draw the static title section.
        Intended to be called only once.

        <appName> ... <precision> <metricA> <metricB> ... <devicePath>
        '''

        appName:str = "Correlator"
        devicePath:str = device.name
        precision:str = "%db" % hwRegs[HwReg.Precision]
        metricA:str = mapMetricIntToStr[hwRegs[HwReg.MetricA]]
        metricB:str = mapMetricIntToStr[hwRegs[HwReg.MetricB]]

        left:str = appName
        mid:str = ' '.join((precision, metricA, metricB))
        right:str = devicePath

        midBegin:int = (self.nChars // 2) - (len(mid) // 2)
        rightBegin:int = self.charRight - len(right) + 1

        # Fill whole line with background.
        self.drawStr(" "*self.charsWidth)

        self.drawStr(left)
        self.drawStr(mid, midBegin)
        self.drawStr(right, rightBegin)

        return # No return value
    # }}} def drawTitle

    def drawStatus(self) -> None: # {{{
        '''Draw/redraw the status section.

        Up/Down: Move ... Left/Right: Change ... Enter: Send
        '''

        left:str = "Up/Down: Navigate"
        mid:str = "Left/Right: Modify"
        right:str = "Enter: Send Update"

        midBegin:int = (self.nChars // 2) - (len(mid) // 2)
        rightBegin:int = self.charRight - len(right) + 1

        # Fill whole line with background.
        self.drawStr(" "*self.charsWidth, y=self.lineBottom)

        self.drawStr(left, y=self.lineBottom)
        self.drawStr(mid, midBegin, y=self.lineBottom)
        self.drawStr(right, rightBegin, y=self.lineBottom)

        return # No return value
    # }}} def drawStatus
# }}} class FullWindow

class InputWindow(CursesWindow): # {{{
    '''The "inpt" window contains a list of parameters with their values.

    The user can modify values using the left/right arrow keys.
    No box.
    Asterisk at topLeft indicates if display is up to date with hardware.

    +----------- ... -------------+
    |label0     value0     domain0|
    |label1     value1     domain1|
    ...                         ...
    |labelN     valueN     domainN|
    +----------- ... -------------+
    '''
    def drawParams(self, guiRegs, selectIdx:int) -> None: # {{{
        '''Draw all the parameter lines.

        <label> ... <value> ... <domain>
        '''
        maxLenName:int = max(len(r.name) for r in GuiReg)

        self.win.clear()
        for i,(r,d) in enumerate(mapGuiRegToDomain_.items()):
            nm:str = r.name

            left:str = ' '*(maxLenName - len(nm)) + nm + " = "
            right:str = d

            v = guiRegs[r]
            if isinstance(v, str):
              mid = v
            elif isinstance(v, bool):
              mid = "True" if v else "False"
            elif isinstance(v, int):
              mid = "%d" % v
            elif isinstance(v, float):
              mid = "%0.03f" % v
            elif isinstance(v, enum.Enum):
              mid = v.name
            else:
              mid = str(v)

            #midBegin:int = (self.nChars // 2) - (len(mid) // 2)
            midBegin:int = len(left) + 2
            #rightBegin:int = self.charRight - len(right) + 1
            rightBegin:int = 30

            # Fill whole line with background.
            self.drawStr(" "*self.charsWidth, y=i+1)

            self.drawStr(left, y=i+1)
            self.drawStr(mid, midBegin, y=i+1)
            self.drawStr(right, rightBegin, y=i+1)

        return # No return value
    # }}} def drawParams
# }}} class InputWindow

def gui(scr, device, hwRegs): # {{{
    '''
    Window objects:
    - scr: All available screen space.
    - full: Rectangle in the centre of scr.
    - inpt: Rectangle below title for dynamic inputs.
    - otpt: Rectangle above status for dynamic outputs.

    Each of the window objects is refreshed individually.
    '''
    curses.curs_set(0) # Hide the cursor.
    cursesInitPairs() # Initialize colors

    full:CursesWindow = FullWindow(scr,
        nLines=30, nChars=80,
        colorPair=whiteBlue)
    full.win.box()
    full.drawTitle(device, hwRegs)
    full.drawStatus()
    full.win.refresh()

    guiRegs_:Dict[GuiReg, Any] = hwRegsToGuiRegs(hwRegs)
    guiRegs_.update({GuiReg.UpdateMode: UpdateMode.Batch})
    assert all(k in guiRegs_.keys() for k in GuiReg)

    inpt:CursesWindow = InputWindow(full.win,
        nLines=len(GuiReg)+2, nChars=full.nChars-2,
        colorPair=greenBlack,
        beginY=full.lineTop+1, beginX=1)
    inpt.drawParams(guiRegs_, 0)
    inpt.win.refresh()

    # Fill remaining lines
    otpt:CursesWindow = CursesWindow(full.win,
        nLines=full.nLines-4-len(GuiReg)-1, nChars=full.nChars-2,
        colorPair=whiteRed,
        beginY=inpt.nLines+1, beginX=1)
    for i in range(otpt.linesHeight):
        otpt.drawStr(str(i)[-1]*otpt.charsWidth, x=1, y=otpt.lineTop+i)
    #otpt.win.box()
    otpt.win.refresh()

    # {{{ Layout test/example

    # 0000-+
    # |1111|
    # |+--+|
    # ||22||
    # |+--+|
    # |    5
    # |    |
    # +7777+

    tst1 = curses.newwin(8, 6, 0, 1)
    tst1.box()
    tst1.addstr(0, 0, "0000") # Overwrites topLeft box
    tst1.addstr(1, 1, "1111") # Nicely contained
    tst1.addstr(7, 1, "7777") # Overwrites bottom box
    tst1.addstr(5, 5, "5")    # Overwrites right box
    tst1.refresh()

    tst2 = curses.newwin(3, 4, 2, 2)
    tst2.box()
    tst2.addstr(1, 1, "22")
    tst2.refresh()

    tst3 = curses.newwin(1, 4, 1, 10)
    tst3.box()
    tst3.refresh()

    tst4 = curses.newwin(1, 10, 3, 10)
    tst4.addstr(0, 0, full.win.encoding)
    tst4.refresh()

    # }}} Layout test/example

    #time.sleep(2)
    full.win.getch() # Calls refresh for this and derived windows.

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
        ret = SampleMode.Nonjitter
    elif "nonperiodic" == i:
        ret = SampleMode.Nonperiodic
    else:
        msg = "Sample mode must be in {PERIODIC, NONPERIODIC}"
        raise argparse.ArgumentTypeError(msg)
    return ret
# }}} def argparseSampleMode
argparser.add_argument("--init-sampleMode",
    type=argparseSampleMode,
    default=SampleMode.Nonjitter,
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

def main(args) -> int: # {{{
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
        rd:Callable = functools.partial(hwReadRegs, device)
        wr:Callable = functools.partial(hwWriteRegs, device)

        verb("Reading RO registers...", end='')
        hwRegsRO:Dict[HwReg, Any] = rd((HwReg.Precision,
                     HwReg.MetricA,
                     HwReg.MetricB,
                     HwReg.MaxNInputs,
                     HwReg.MaxWindowLengthExp,
                     HwReg.MaxSampleRateNegExp,
                     HwReg.MaxSampleJitterNegExp))
        verb("Done")

        # Fill in missing values of parameter domains.
        mapGuiRegToDomain_.update({
            GuiReg.NInputs: mapGuiRegToDomain_[GuiReg.NInputs] %
                hwRegsRO[HwReg.MaxNInputs],
            GuiReg.WindowLength: mapGuiRegToDomain_[GuiReg.WindowLength] %
                hwRegsRO[HwReg.MaxWindowLengthExp],
            GuiReg.SampleRate: mapGuiRegToDomain_[GuiReg.SampleRate] %
                hwRegsRO[HwReg.MaxSampleRateNegExp],
            GuiReg.SampleJitter: mapGuiRegToDomain_[GuiReg.SampleJitter] %
                hwRegsRO[HwReg.MaxSampleJitterNegExp],
        })

        verb("Initializing RW registers...", end='')
        initRegsRW:Dict[HwReg, Any] = {
            HwReg.NInputs:              args.init_nInputs,
            HwReg.WindowLengthExp:      args.init_windowLengthExp,
            HwReg.SampleRateNegExp:     args.init_sampleRateNegExp,
            HwReg.SampleMode:           args.init_sampleMode,
            HwReg.SampleJitterNegExp:   args.init_sampleJitterNegExp,
        }
        wr(initRegsRW)
        verb("Checking...", end='')
        hwRegsRW:Dict[HwReg, Any] = rd(initRegsRW.keys())
        # TODO: uncomment
        #assert all(initRegsRW[k] == v for k,v in hwRegsRW.items()), hwRegsRW
        verb("Done")

        try:
            verb("Starting GUI (curses)...")
            curses.wrapper(gui, device, {**hwRegsRO, **hwRegsRW})
            verb("GUI Done")
        except KeyboardInterrupt:
            verb("KeyboardInterrupt. Exiting.")

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())

