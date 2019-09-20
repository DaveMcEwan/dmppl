
import numpy as np
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

if __name__ == "__main__":
    assert False, "Not a standalone script."
