
from __future__ import absolute_import
from __future__ import division

import hashlib
import math
import numpy as np
import sys
from .base import compose

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

def identiconSquareBool(x, s=5): # {{{
    '''Generate a square s-by-s boolean identicon using a hash of x.

    NOTE: x does not need to be hashable as x.__str__() is applied before
    passing to MD5.
    Returns list of list of bools.
    '''
    assert isinstance(s, int) and 3 < s < 13, (type(s), s)
    nBits = s**2

    # Only use some bits to keep result looking clean.
    nDiscardRows = int(math.ceil(s / 2)) - 1
    nUsedBits = nBits - s*nDiscardRows

    # MD5 gives 16 bytes (128 bits), limiting max value of s.
    h = hashlib.md5(bytes(str(x).encode())).digest()
    assert isinstance(h, bytes), type(h)
    assert 16 == len(h), str(h)

    # Create a string of bools at least nUsedBits long from the first bits in
    # the hash digest.
    if 2 == sys.version_info[0]: # Python2 str/bytes weirdness
        u = [(0 != ord(h[i // 8]) & (1 << (i % 8))) for i in range(nUsedBits)]
    else:
        u = [(0 != h[i // 8] & (1 << (i % 8))) for i in range(nUsedBits)]
    assert nUsedBits <= len(u), (s, len(u))

    # Replicate rows to make full length (nBits).
    b = (u + u[s:s*nDiscardRows] + u[0:s])[-nBits:]
    assert len(b) == nBits, (len(b), nBits)

    # Partition into columns.
    columns = [b[i:i+s] for i in range(0, nBits, s)]

    # Transpose columnns to make rows to make it look "the right way up".
    rows = [[col[i] for col in columns] for i in range(s)]

    return rows
# }}} def identiconSquareBool

def asciiart2dBool(x, t='#', f=' '): # {{{
    '''Return an ASCII-art string to be printed representing a bool 2D array.
    '''
    return '\n'.join((''.join([(t if r else f) for r in row])) for row in x)
# }}} def asciiart2dBool


if __name__ == "__main__":
    assert False, "Not a standalone script."
