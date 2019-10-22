
from __future__ import absolute_import
from __future__ import division

import functools
import gzip
import math
import numpy as np
import sys
from .base import stripSuffix

if sys.version_info[0] > 2:
    long = int

def isEven(x): # {{{
    '''Return True if x is an even integer, else False.
    '''
    assert isinstance(x, (int, long))

    return (x % 2 == 0)
# }}} def isEven

def isOdd(x): # {{{
    '''Return True if x is an odd integer, else False.
    '''
    assert isinstance(x, (int, long))

    return (x % 2 == 1)
# }}} def isOdd

def isPow2(x): # {{{
    '''Return True if x is an integer power of 2, else False.
    '''
    assert isinstance(x, (int, long))
    assert 0 <= x

    return (x != 0) and ((x & (x-1)) == 0)
# }}} def isPow2

def clog2(x): # {{{
    '''Return lowest number of bits required to represent x in base2.
    '''
    assert isinstance(x, (int, long, float))
    assert 0 <= x

    return int(math.ceil(math.log(x, 2)))
# }}} def clog2

def dotp(xs, ys): # {{{
    '''Dot product.

    NOTE: Allowing iterables as input means length can't be checked.
    '''
    assert all(isinstance(x, (int, long, float)) for x in xs), xs
    assert all(isinstance(y, (int, long, float)) for y in ys), ys

    return sum(x*y for x,y in zip(xs, ys))
# }}} def dotp

def clipNorm(x, lo=0.0, hi=1.0): # {{{
    '''Clip and normalize to range.
    '''
    assert isinstance(x, (int, long, float))
    _x = float(x)

    assert isinstance(lo, (int, long, float))
    assert isinstance(hi, (int, long, float))
    _lo = float(min(lo, hi)) # Allow lo > hi
    _hi = float(max(lo, hi)) # Allow hi < lo

    ret = (min(max(_x, _lo), _hi) - _lo) / (_hi - _lo)
    assert 0.0 <= ret <= 1.0

    return ret
# }}} def clipNorm

def int2base(x, base): # {{{
    '''Print a non-negative integer in a base from 2 to 36.

    Nothing to do with the base64 encoding scheme.
    '''
    assert isinstance(x, (int, long))
    assert 0 <= x

    numerals = '0123456789abcdefghijklmnopqrstuvwxyz'
    assert isinstance(base, (int, long))
    assert 1 < base < len(numerals)

    if x == 0:
        return numerals[0]
    r = []
    while x:
        x, a = divmod(x, base)
        r.append(numerals[a])
    r.reverse()
    return ''.join(r)
# }}} def int2base

def powsineCoeffs(n, alpha): # {{{
    '''Return a NumPy row with coefficient constants for window function.

    $w(x) = \\sin^\\alpha(\\frac{x\\pi}{n-1})$
    '''
    n = int(n)

    return np.power(np.sin(np.multiply(np.arange(n), np.pi/(n-1))), alpha)
# }}} def powsineCoeffs

def loadNpy(fname): # {{{
    '''Load a NumPy array, optionaly decompressing via GZip.

    Automatically append filename suffix if not provided.
    If file doesn't exist return None, leaving the caller to check.
    This makes it usable in filtered list comprehensions.
    '''
    assert isinstance(fname, str)
    assert 0 < len(fname)

    freal = stripSuffix(stripSuffix(fname, ".gz"), ".npy")
    assert 0 < len(freal)

    try:
        if fname.endswith(".npy"):
            fname_ = freal + ".npy"
            with open(fname_, 'rb') as fd:
                arr = np.load(fd)
        else:
            fname_ = freal + ".npy.gz"
            with gzip.GzipFile(fname_, 'rb') as fd:
                arr = np.load(fd)

        assert isinstance(arr, np.ndarray)
    except IOError:
        arr = None

    return arr
# }}} def loadNpy

def saveNpy(arr, fname): # {{{
    '''Save a NumPy array, optionally compressed with GZip.

    Append filename suffix if not provided.

    foo         -> foo.npy.gz
    foo.npy     -> foo.npy
    foo.npy.gz  -> foo.npy.gz
    '''
    assert isinstance(arr, np.ndarray)
    assert isinstance(fname, str)
    assert 0 < len(fname)

    freal = stripSuffix(stripSuffix(fname, ".gz"), ".npy")
    assert 0 < len(freal)

    if fname.endswith(".npy"):
        fname_ = freal + ".npy"
        with open(fname_, 'wb') as fd:
            np.save(fd, arr)
    else:
        fname_ = freal + ".npy.gz"
        with gzip.GzipFile(fname_, 'wb') as fd:
            np.save(fd, arr)

    return
# }}} def saveNpy

def _assertPt(pt): # {{{
    '''Common assertions for points.
    '''
    if __debug__:
        pt = tuple(pt)

        assert hasattr(pt, "__iter__"), \
            "pt=%s Point must be iterable. list, tuple, or generator." % \
            (pt,)

        assert 0 < len(pt), \
            "pt=%s, Point must have at least one dimension." % \
            (pt,)

        for p in pt:
            assert isinstance(p, (float, int, long)), (type(p), pt)

    return
# }}} def _assertPt

def _assertPts(pts): # {{{
    '''Common assertions for sequences of points.
    '''
    if __debug__:
        pts = list(pts)

        assert hasattr(pts, "__iter__"), \
            "pts=%s Points must be iterable. list, tuple, or generator." % \
            (pts,)

        for i in range(len(pts)):
            _assertPt(pts[i])

            assert len(pts[i]) == len(pts[i-1]), \
                "pts=%s All points must be of equal dimensionallity." % \
                (pts,)

    return
# }}} def _assertPts

def _assertPtPair(ptA, ptB): # {{{
    '''Common assertions for pair of points.
    '''
    if __debug__:
        ptA = tuple(ptA)
        ptB = tuple(ptB)

        _assertPt(ptA)
        _assertPt(ptB)

        assert len(ptA) == len(ptB), \
            "ptA=%s ptB=%s Both points must be of equal dimensionallity." % \
            (ptA, ptB)

    return
# }}} def _assertPtPair

def _assertPtPairs(ptPairs): # {{{
    '''Common assertions for sequences of point pairs.
    '''
    if __debug__:
        ptPairs = list(ptPairs)

        assert hasattr(ptPairs, "__iter__"), \
            "ptPairs=%s Point pairs must be iterable." % \
            (ptPairs,)

        for i in range(len(ptPairs)):
            assert 2 == len(ptPairs[i]), \
                "ptPairs[%d]=%s Point pairs must be in pairs." % \
                (i, ptPairs[i])

            ptA, ptB = ptPairs[i]
            _assertPtPair(ptA, ptB)

    return
# }}} def _assertPtPairs

def _ptsOp(op, pts, *args, **kwargs): # {{{
    '''Apply a point operation to a sequence of points as a generator.
    '''
    _assertPts(pts)
    return (op(pt, *args, **kwargs) for pt in pts)
# }}} def _ptsOp

def _ptPairsOp(op, ptPairs, *args, **kwargs): # {{{
    '''Apply a point operation to a sequence of points as a generator.
    '''
    _assertPtPairs(ptPairs)
    return (op(ptA, ptB, *args, **kwargs) for ptA,ptB in ptPairs)
# }}} def _ptPairsOp

def ptScale(pt=(0, 0), scale=1): # {{{
    '''Scale a point/vector.
    '''
    _assertPt(pt)
    assert isinstance(scale, (float, int, long)), (type(scale), scale)

    return tuple(p * scale for p in pt)
# }}} def ptScale

def ptShift(pt=(0, 0), shift=(0, 0)): # {{{
    '''Shift a point.
    '''
    _assertPt(pt)

    assert len(shift) == len(pt), \
        "pt=%s, shift=%s Shift must have same dimensionallity as point." % \
        (pt, shift)

    for s in shift:
        assert isinstance(s, (float, int, long)), (type(s), shift)

    return tuple(p + s for p,s in zip(pt, shift))
# }}} def ptShift

def ptMirror(pt=(0, 0), mirror=(None, None)): # {{{
    '''Mirror a point around hyperplanes.
    '''
    _assertPt(pt)

    assert len(mirror) == len(pt), \
        "pt=%s, mirror=%s Plane must have same dimensionallity as point." % \
        (pt, mirror)

    for m in mirror:
        assert m is None or isinstance(m, (float, int, long)), (type(m), mirror)

    return tuple(p if r is None else 2*r - p for p,r in zip(pt, mirror))
# }}} def ptMirror

def ptRotate(pt=(0, 0), rotation=((0, 0), (0, 0)), center=(0, 0)): # {{{
    '''Rotate a point around a center point with a rotation matrix.
    '''
    _assertPt(pt)

    assert len(center) == len(pt), \
        "pt=%s, center=%s Center must have same dimensionallity as point." % \
        (pt, mirror)

    for c in center:
        assert isinstance(c, (float, int, long)), (type(c), center)

    center = tuple(center)
    negCenter = ptMirror(center, tuple(0.0 for _ in center))
    ptOriginVec = ptShift(pt, negCenter)

    rotated = tuple(sum(elR * p for elR,p in zip(rowR, ptOriginVec)) \
                    for rowR in rotation)

    ret = ptShift(rotated, center)
    return ret
# }}} def ptRotate

def rotMat2D(theta=0, clockwise=False): # {{{
    '''Return the 2D rotation matrix for angle theta.
    '''
    assert isinstance(theta, (float, int, long)), (type(theta), theta)
    if clockwise:
        ret = ((np.cos(theta), np.sin(theta)), (-np.sin(theta), np.cos(theta)))
    else:
        ret = ((np.cos(theta), -np.sin(theta)), (np.sin(theta), np.cos(theta)))
    return ret
# }}} def rotMat2D

def ptRotate2D(pt=(0, 0), theta=0, center=(0, 0)): # {{{
    '''Rotate a 2D point around a center point by theta radians.
    '''
    return ptRotate(pt, rotMat2D(theta), center)
# }}} def ptRotate2D

def ptPairDifference(ptA=(0, 0), ptB=(0, 0)): # {{{
    '''Return the vector difference between a pair of points.
    '''
    _assertPtPair(ptA, ptB)

    return tuple(b-a for a,b in zip(ptA, ptB))
# }}} def ptPairDifference

def ptPairPtBetween(ptA=(0, 0), ptB=(0, 0), fraction=0.5): # {{{
    '''Return the point between a pair of points.
    '''
    _assertPtPair(ptA, ptB)
    assert isinstance(fraction, float), (type(fraction), fraction)
    assert 0 <= fraction <= 1.0, fraction

    return tuple((b-a)*fraction + a for a,b in zip(ptA, ptB))
# }}} def ptPairPtBetween

def ptPairDistance(ptA=(0, 0), ptB=(0, 0)): # {{{
    '''Return the Euclidean distance between a pair of points.

    https://en.wikipedia.org/wiki/Euclidean_distance
    '''
    _assertPtPair(ptA, ptB)

    return math.sqrt(sum((b-a)**2 for a,b in zip(ptA, ptB)))
# }}} def ptPairDistance

def ptsMkPolygon(nPts=3, radius=[1.0]): # {{{
    '''Generate points for a 2D polygon with a number of radiuses.

    Joining the points forms a shade with regularly angled sides around the
    origin.
    A single radius gives a convex shape like a square, hexagon. etc.
    Multiple radiuses gives a concave shape like a star, gear wheel, etc.
    '''
    assert isinstance(nPts, (float, int, long)), (type(nPts), nPts)
    lRadius = len(radius)
    return (ptRotate2D((radius[i % lRadius], 0.0), i*2*math.pi/nPts) \
            for i in range(nPts))
# }}} def ptsMkPolygon

ptsScale = functools.partial(_ptsOp, ptScale)
ptsShift = functools.partial(_ptsOp, ptShift)
ptsMirror = functools.partial(_ptsOp, ptMirror)
ptsRotate = functools.partial(_ptsOp, ptRotate)
ptsRotate2D = functools.partial(_ptsOp, ptRotate2D)
ptPairsDifference = functools.partial(_ptPairsOp, ptPairDifference)
ptPairsPtBetween = functools.partial(_ptPairsOp, ptPairPtBetween)
ptPairsDistance = functools.partial(_ptPairsOp, ptPairDistance)

# TODO: ptPairAngle? ptPolar?
# TODO: arcLength, arcIsBig, arcEndpoint
# TODO: bezPt, bezPts, bezAngle, bezLength
# TODO: Support NumPy arrays as points.

if __name__ == "__main__":
    assert False, "Not a standalone script."
