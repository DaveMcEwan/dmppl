
from __future__ import absolute_import
from __future__ import division

import curses
import functools
import itertools
import locale


cursesColors = (
    curses.COLOR_BLACK,
    curses.COLOR_RED,
    curses.COLOR_GREEN,
    curses.COLOR_YELLOW,
    curses.COLOR_BLUE,
    curses.COLOR_MAGENTA,
    curses.COLOR_CYAN,
    curses.COLOR_WHITE,
)
nCursesColors = len(cursesColors)

cursesPairNums = \
    tuple(enumerate((cursesColors[f], cursesColors[b]) \
                    for f,b in itertools.product(range(nCursesColors),
                                                 range(nCursesColors))))

_,           blackRed,  blackGreen,  blackYellow,  blackBlue,  blackMagenta, blackCyan,  blackWhite,    \
redBlack,    _,         redGreen,    redYellow,    redBlue,    redMagenta,   redCyan,    redWhite,      \
greenBlack,  greenRed,  _,           greenYellow,  greenBlue,  greenMagenta, greenCyan,  greenWhite,    \
yellowBlack, yellowRed, yellowGreen, _,            yellowBlue, yellowMagenta,yellowCyan, yellowWhite,   \
blueBlack,   blueRed,   blueGreen,   blueYellow,   _,          blueMagenta,  blueCyan,   blueWhite,     \
magentaBlack,magentaRed,magentaGreen,magentaYellow,magentaBlue,_,            magentaCyan,magentaWhite,  \
cyanBlack,   cyanRed,   cyanGreen,   cyanYellow,   cyanBlue,   cyanMagenta,  _,          cyanWhite,     \
whiteBlack,  whiteRed,  whiteGreen,  whiteYellow,  whiteBlue,  whiteMagenta, whiteCyan,  _              = \
    tuple(n for n,(f,b) in cursesPairNums)

def cursesInitPairs(): # {{{
    '''Initialize curses foreground/background color pairs so that the
    foregroundBackground names below may be used.
    '''
    for n,(f,b) in cursesPairNums:
        if f != b:
            curses.init_pair(n, f, b)
# }}} def cursesInitPairs

class CursesWindow(object): # {{{
    '''Helper class to pre-calulate some constants and functions.
    The window is a rectangle in the middle of the screen.
    A box uses the first/last character position on each line/char, so
    topLeft is the position of the box corner.

    self.draw() is a wrapper for self.win.addstr() with encoding and color.

    +-----------...
    | Title...
    |
    ...
    |
    | Status...
    +-----------...
    '''
    def __init__(self, scr, nLines=40, nChars=80, colorPair=0,
                 beginY=None, beginX=None, center=True):

        scrNLines, scrNChars = scr.getmaxyx()

        assert isinstance(nLines, int), (type(nLines), nLines)
        assert isinstance(nChars, int), (type(nChars), nChars)
        self.nLines, self.nChars = nLines, nChars

        if beginY is None:
            if center:
                self.beginY = (scrNLines - nLines) // 2
            else:
                self.beginY = 0
        else:
            assert isinstance(beginY, int), (type(beginY), beginY)
            self.beginY = beginY

        if beginX is None:
            if center:
                self.beginX = (scrNChars - nChars) // 2
            else:
                self.beginX = 0
        else:
            assert isinstance(beginX, int), (type(beginX), beginX)
            self.beginX = beginX

        self.linesHeight, self.charsWidth = nLines - 2, nChars - 2
        self.lineTop, self.lineBottom = 1, nLines - 2
        self.charLeft, self.charRight = 1, nChars - 2

        self.win = scr.derwin(nLines, nChars, self.beginY, self.beginX)

        self.drawStr = functools.partial(self._drawStr,
                                         colorPair=colorPair)

    def _drawStr(self, s, x=1, y=1, colorPair=0, attr=curses.A_NORMAL,
                 encoding=locale.getpreferredencoding()): # {{{
        '''Intended to be used with functools.partial()

        NOTE: Unicode requires libncursesw-dev to be present at build, not just
        libncurses-dev ('w' indicates wide-character support).
        '''
        b = s.encode(encoding)
        return self.win.addstr(y, x, b, attr | curses.color_pair(colorPair))
    # }}} def _drawStr

# }}} class CursesWindow


if __name__ == "__main__":
    assert False, "Not a standalone script."
