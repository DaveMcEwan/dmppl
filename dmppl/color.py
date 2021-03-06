
from __future__ import absolute_import
from __future__ import division

import curses
import functools
import hashlib
import itertools
import locale
import math
import numpy as np
import sys
from .base import compose, dbg

def colorspace1D(a, gamma=1.0, nBits=8): # {{{
    '''Return RGB tuple to represent a bounded value as grayscale.

    Higher values of a are darker.
    '''
    assert isinstance(a, float), "type(a)=%s" % str(type(a))
    assert 0.0 <= a <= 1.0 or np.isnan(a), "a=%s" % a
    assert isinstance(gamma, float), "type(gamma)=%s" % str(type(gamma))
    assert isinstance(nBits, int), "type(nBits)=%s" % str(type(nBits))
    assert nBits > 1

    n_levels = 2**nBits - 1

    if np.isnan(a):
        gray = 0
    else:
        gray = int( n_levels * (1-a)**gamma )

    return gray, gray, gray
# }}} def colorspace1D

def colorspace2D(a, b, gamma=1.0, nBits=8): # {{{
    '''Return RGB tuple to represent bounded pair of values a,b as color.

    Higher values of a and b are darker.
    Implementation of colorspace in https://arxiv.org/abs/1905.06386
    '''
    assert isinstance(a, float), "type(a)=%s" % str(type(a))
    assert np.isnan(a) or 0.0 <= a <= 1.0, a
    assert isinstance(b, float), "type(b)=%s" % str(type(b))
    assert np.isnan(b) or 0.0 <= b <= 1.0, b
    assert isinstance(gamma, float), "type(gamma)=%s" % str(type(gamma))
    assert isinstance(nBits, int), "type(nBits)=%s" % str(type(nBits))
    assert nBits > 1

    if np.isnan(a):
        a = 0.0

    if np.isnan(b):
        b = 0.0

    theta = 1.0 - (np.sqrt(a**2 + b**2) / np.sqrt(2.0))**gamma
    phi = np.arctan2(b, a)

    pi4 = 0.25 * np.pi
    n_levels = 2**nBits - 1

    red = int( n_levels * theta )
    green = int( n_levels * theta**(max(0, pi4 - phi) + 1) )
    blue = int( n_levels * theta**(max(0, phi - pi4) + 1) )
    assert 0 <= red <= 255
    assert 0 <= green <= 255
    assert 0 <= blue <= 255

    return red, green, blue
# }}} def colorspace2D

def rgbStr(red, green, blue): # {{{
    '''Return string for RGB tuple as used in HTML, SVG, etc.
    '''
    assert isinstance(red, int)
    assert isinstance(green, int)
    assert isinstance(blue, int)
    assert 0 <= red <= 255
    assert 0 <= green <= 255
    assert 0 <= blue <= 255

    return "{:02x}{:02x}{:02x}".format(red, green, blue)
# }}} def rgbStr
rgb1D = compose(rgbStr, colorspace1D, unpack=True)
rgb2D = compose(rgbStr, colorspace2D, unpack=True)

def identiconSprite(x, nRows=5, nCols=5): # {{{
    '''Generate a vertically symmetrical square boolean identicon.

    `x` must be a stringable object.

    Returns list of list of bools.

    This is similar to the "sprites" generated by GitHub.
    https://en.wikipedia.org/wiki/Identicon
    https://barro.github.io/2018/02/avatars-identicons-and-hash-visualization/

    NOTE: x does not need to be hashable as x.__str__() is applied before
    passing to MD5.
    '''
    assert isinstance(nRows, int), (type(nRows), nRows)
    assert isinstance(nCols, int), (type(nCols), nCols)
    assert nRows * nCols <= 128, (nRows, nCols)

    # Mirror vertically.
    nColsHalf = int(math.ceil(nCols / 2))
    nBitsHalf = nRows * nColsHalf

    # MD5 gives 16 bytes (128 bits), limiting max dimensions.
    h = hashlib.md5(bytes(str(x).encode())).digest()
    assert isinstance(h, bytes), type(h)
    assert 16 == len(h), str(h)

    # Create a string of bools nBitsHalf long from the first bits in digest.
    if 2 == sys.version_info[0]: # Python2 str/bytes weirdness
        u = [(0 != ord(h[i // 8]) & (1 << (i % 8))) for i in range(nBitsHalf)]
    else:
        u = [(0 != h[i // 8] & (1 << (i % 8))) for i in range(nBitsHalf)]
    assert nBitsHalf == len(u), (nBitsHalf, len(u))

    # Partition into columns creating half the image.
    columnsHalf = [u[i:i + nRows] for i in range(0, nBitsHalf, nRows)]

    # Replicate columns to make full image.
    columns = columnsHalf + columnsHalf[::-1][nCols % 2:]

    # Transpose columnns to make rows to make it look "the right way up",
    # because horizontally symmetrical isn't as personable.
    rows = [[col[r] for col in columns] for r in range(nRows)]

    return rows
# }}} def identiconSprite

def asciiart2dBool(x, t='#', f=' '): # {{{
    '''Return an ASCII-art string to be printed representing a bool 2D array.
    '''
    return '\n'.join((''.join([(t if r else f) for r in row])) for row in x)
# }}} def asciiart2dBool

def identiconSpriteSvg(x, **kwargs): # {{{
    '''Take a stringable object x and produce an SVG of a sprite identicon.

    nRows, nCols set the arrangement of squares comprising the sprite.

    NOTE: CSS can be used to set colors.
    '''

    nRows = kwargs.get("nRows", 5)
    nCols = kwargs.get("nCols", 5)
    classList = kwargs.get("classList", ["identicon"])
    unitSize = kwargs.get("unitSize", 1)
    sizeUnit = kwargs.get("sizeUnit", "mm") # {"mm", "px", "%", '', ...}
    cssProps = kwargs.get("cssProps", False)

    bitFmtParts_ = [
        '<rect',
          'class="bit"',
          'x="%d"',
          'y="%d"',
    ]
    if not cssProps:
        bitFmtParts_ += [
            'width="%d"' % unitSize,
            'height="%d"' % unitSize,
        ]
    bitFmtParts_.append('/>')
    bitFmt = ' '.join(bitFmtParts_)

    bits = identiconSprite(x, nRows=nRows, nCols=nCols)
    bitPositions = [(c*unitSize, r*unitSize) \
                    for r,bitRow in enumerate(bits) \
                    for c,b in enumerate(bitRow) \
                    if b]

    # 0,0 is top-left
    viewBoxMinX, viewBoxMinY = 0, 0
    viewBoxWidth, viewBoxHeight = nRows*unitSize, nCols*unitSize

    ret_ = []
    ret_ += [
      '<svg',
        'xmlns="http://www.w3.org/2000/svg"',
        'xmlns:xlink="http://www.w3.org/1999/xlink"',
        'viewBox="%d %d %d %d"' % (viewBoxMinX, viewBoxMinY, viewBoxWidth, viewBoxHeight),
        'class="%s"' % ' '.join(classList),
        'width="%d%s"' % (nCols, sizeUnit),
        'height="%d%s"' % (nRows, sizeUnit),
        '>',
    ]
    if cssProps:
        ret_ += [
            '<style>',
            'rect.bit { width:%dpx; height:%dpx; }' % (unitSize, unitSize),
            '</style>',
        ]
    ret_ += [bitFmt % (x,y) for x,y in bitPositions]
    ret_.append('</svg>')

    return '\n'.join(ret_)
# }}} def identiconSpriteSvg

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
