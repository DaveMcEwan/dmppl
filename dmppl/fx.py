
from __future__ import division

import numpy as np
from .math import isPow2, clog2

'''
Fixed point format represents the semi-open interval (0, 1].

All values must be in range by construction.
Designed to avoid gradient vanishing, i.e. 1 times 1 should equal 1.
Designed to value memory bandwidth over hardware logic complexity, so
operations may require more gates than similar operations in Q format.
The difference in the cost ratio of memory bandwidth to logic complexity is
more significant when nBits is small.

NOTE: This has nothing to do with the package on PyPI for Haskell-like
operators which is also called "fx".

NOTE: This is *not* Q format!
In Qn.n (n bits, all are fraction bits) there is no value to represent 1 so you
end up doing something like 0.9 times 0.9 giving 0.81 where fewer bits of
precision increases the error.
In other words Qn.n format is for the semi-open interval [0, 1) which works
perfectly with conventional integer arithmetic.
This format requires slightly different arithmetic.

Convert from true value x to representation s.
    E.g. let x = 0.5, nBits = 8
  Multiply by 2**nBits and round down to nearest integer.
    p = x * 2**nBits = 128 = 0x80
  Subtract 1 to give representation s.
    s = p - 1 = 127 = 0x7f

Convert to true value x from representation s.
    E.g. let s = 0x3f, nBits = 8
  Add 1 to get numerator of fraction.
    s + 1 = 0x3f + 1 = 63 + 1 = 64 = 0x40
  Denominator is 2**nBits
    (s+1) / 2**nbits = 64/256 = 1/4

There isn't a representation for 0, but that's okay.
Multiplying nearly zero with nearly zero gets you even closer to zero, so
fxHadp(0x0, 0x0) returns 0x0.
Adding nearly zero to nearly zero does get you further from zero, so
fxAdd(0x0, 0x0) returns 0x1.


E.g. addition:
Let nBits equal 8, so 0xff represents the value 1.
0 + 0 = 0           -->     0x00 + 0x00 = 0x00
1/4 + 1/4 = 1/2     -->     0x3f + 0x3f = 0x7f
1 + 1 = 1           -->     0xff + 0xff = 0x1ff, ignore overflows --> 0xff

This is the operation desired to add two numbers in fx bit format and put the
result also in fx format, masking out overflows:
  ((x + 1) + (y + 1) - 1) & (2**nBits-1)
Rearrange:
  (x + 1) + (y + 1) - 1
  = x + y + 2 - 1
  = x + y + 1
Giving:
  (x + y + 1) & (2**nBits-1)


E.g. multiplication:
Let nBits equal 8, so 0xff represents the value 1.
There isn't a representation for 0, but that doesn't matter.
0 * 0 = 0           -->     0x00 * 0x00 = 0x00
1/2 * 1/2 = 1/4     -->     0x7f * 0x7f = 0x3f
1 * 1 = 1           -->     0xff * 0xff = 0xff

This is the operation desired to multiply two numbers in fx bit format and put
the result also in fx format:
This is the operation desired:
  ((x + 1) * (y + 1) - 1) >> nBits
Rearrange:
  (x + 1)(y + 1) - 1
  = xy + x + y + 1 - 1
  = xy + x + y
Giving:
  (x * y + x + y) >> nBits

NumPy/Python doesn't work consistently with nBits larger than 31.
>>> x8 = np.asarray([0, 1, 0xff], dtype=np.uint8)
>>> x16 = np.asarray([0, 1, 0xff, 0xffff], dtype=np.uint16)
>>> x32 = np.asarray([0, 1, 0xff, 0xffff, 0x7fffffff, 0xffffffff], dtype=np.uint32)
>>> x64 = np.asarray([0, 1, 0xff, 0xffff], dtype=np.uint64)
>>> [[((x_ + 1)*(x_ + 1) - 1) for x_ in s] for s in (x8, x16, x32, x64)]
[[0, 3, 65535],
 [0, 3, 65535, 4294967295],
 [0, 3, 65535, 4294967295, 4611686018427387903, -1],    # 32b goes to -1.
 [0.0, 3.0, 65535.0, 4294967295.0]]                     # Returns floats.
'''

defaultNBits = 8

def _fxGetKwargs(**kwargs): # {{{
    '''Decide the size and dtypes for fx*().
    '''
    nBits = kwargs.get("nBits", defaultNBits)
    assert isinstance(nBits, int)
    assert 0 < nBits, "nBits=%d must be a positive integer." % nBits

    # NOTE: If more kwargs are defined for fx*() then return as a tuple.

    return nBits
# }}} def _fxGetKwargs

def fxDtype(nBits, allowUnsafe=False): # {{{
    '''Decide and dtype for a number of bits.
    '''
    assert isinstance(nBits, int)
    assert 0 < nBits, "nBits=%d must be a positive integer." % nBits
    assert isinstance(allowUnsafe, bool)

    if 8 >= nBits:
        ret = np.uint8
    elif 16 >= nBits:
        ret = np.uint16
    elif 31 >= nBits:
        ret = np.uint32
    elif allowUnsafe and 64 >= nBits:
        ret = np.uint64
    else:
        assert False, "Larger fixed point representations unsupported."

    return ret
# }}} def fxDtype

def fxDtypeLargerSigned(nBits): # {{{
    '''Decide and dtype for a number of bits.

    This will always be twice as large and signed.
    '''
    assert isinstance(nBits, int)
    assert 0 < nBits, "nBits=%d must be a positive integer." % nBits

    if 8 >= nBits:
        ret = np.int16
    elif 16 >= nBits:
        ret = np.int32
    elif 31 >= nBits:
        ret = np.int64
    else:
        assert False, "Larger fixed point representations unsupported."

    return ret
# }}} def fxDtypeLargerSigned

def fxDtypeLargerUnsigned(nBits): # {{{
    '''Decide and dtype for a number of bits.

    This will always be twice as large and unsigned.
    '''
    assert isinstance(nBits, int)
    assert 0 < nBits, "nBits=%d must be a positive integer." % nBits

    if 8 >= nBits:
        ret = np.uint16
    elif 16 >= nBits:
        ret = np.uint32
    elif 31 >= nBits:
        ret = np.uint64
    else:
        assert False, "Larger fixed point representations unsupported."

    return ret
# }}} def fxDtypeLargerUnsigned

def fxAssert(*args, **kwargs): # {{{
    '''Assert args are of matching shapes and correct dtype.

    Optionally set the eq,leq,geq,lt,gt keywords to an array of the same size
    as the NumPy arrays in args to assert comparison properties.
    '''
    if __debug__:

        for i,a in enumerate(args):
            b = args[i-1]
            assert a.dtype == b.dtype, (a.dtype, b.dtype)
            assert a.shape == b.shape, (a.shape, b.shape)

        nBits = _fxGetKwargs(**kwargs)
        dtype1 = fxDtype(nBits)
        assert a.dtype == dtype1, (a.dtype, dtype1)

        eq = kwargs.get("eq")
        if eq is not None:
            assert a.dtype == eq.dtype, (a.dtype, eq.dtype)
            assert a.shape == eq.shape, (a.shape, eq.shape)
            for i,a in enumerate(args):
                assert np.all(a == eq), (a, eq)

        leq = kwargs.get("leq")
        if leq is not None:
            assert a.dtype == leq.dtype, (a.dtype, leq.dtype)
            assert a.shape == leq.shape, (a.shape, leq.shape)
            for i,a in enumerate(args):
                assert np.all(a <= leq), (a, leq)

        geq = kwargs.get("geq")
        if geq is not None:
            assert a.dtype == geq.dtype, (a.dtype, geq.dtype)
            assert a.shape == geq.shape, (a.shape, geq.shape)
            for i,a in enumerate(args):
                assert np.all(a >= geq), (a, geq)

        lt = kwargs.get("lt")
        if lt is not None:
            assert a.dtype == lt.dtype, (a.dtype, lt.dtype)
            assert a.shape == lt.shape, (a.shape, lt.shape)
            for i,a in enumerate(args):
                assert np.all(a < lt), (a, lt)

        gt = kwargs.get("gt")
        if gt is not None:
            assert a.dtype == gt.dtype, (a.dtype, gt.dtype)
            assert a.shape == gt.shape, (a.shape, gt.shape)
            for i,a in enumerate(args):
                assert np.all(a > gt), (a, gt)

    return
# }}} def fxAssert

def fxZero(**kwargs): # {{{
    '''Return representation closest to zero for fixed point (0, 1].
    '''
    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)

    ret = dtype1(0)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxZero

def fxOne(**kwargs): # {{{
    '''Return representation of one for fixed point (0, 1].
    '''
    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)

    ret = dtype1(2**nBits - 1)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxOne

def fxZeros(shape, **kwargs): # {{{
    '''Return array of fxZeros()'s of given shape for fixed point (0, 1].
    '''
    ret = np.broadcast_to(fxZero(**kwargs), shape)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxZeros

def fxOnes(shape, **kwargs): # {{{
    '''Return array of fxOne()'s of given shape for fixed point (0, 1].
    '''
    ret = np.broadcast_to(fxOne(**kwargs), shape)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxOnes

def fxToFloat(x, **kwargs): # {{{
    '''Convert NumPy array in fixed point (0, 1] to IEEE754 float.
    '''
    fxAssert(x, **kwargs)
    nBits = _fxGetKwargs(**kwargs)

    ret = (x.astype(np.float) + 1) / (2**nBits)

    assert 0.0 <= ret <= 1.0, (ret, x, nBits)
    return ret
# }}} def fxToFloat

def fxFromFloat(x, **kwargs): # {{{
    '''Convert NumPy array to fixed point (0, 1] from IEEE754 float.
    '''
    assert np.all(np.logical_and(0.0 <= x, x <= 1.0))

    nBits = _fxGetKwargs(**kwargs)

    dtype1 = fxDtype(nBits)
    ret_ = x * (2**nBits - 1)

    if np.isscalar(x):
        ret = dtype1(ret_)
    else:
        ret = (ret_).astype(dtype1)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxFromFloat

def fxAdd(x, y, **kwargs): # {{{
    '''Elementwise add two NumPy arrays for fixed point (0, 1].

    Take arrays x, y of equal shape and equal dtype.
    Return an array of same dtype and shape as x and y.
    '''
    fxAssert(x, y, **kwargs)

    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)

    with np.errstate(over="ignore"):
        ret_ = (x + y + 1).astype(dtype1)

    if nBits in [8, 16]:
        # Coercing dtype performs implicit masking.
        ret = ret_
    else:
        ret = np.bitwise_and(ret_, 2**nBits-1).astype(dtype1)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxAdd

def fxSub(x, y, **kwargs): # {{{
    '''Elementwise subtract two NumPy arrays for fixed point (0, 1].

    Take arrays x, y of equal shape and equal dtype.
    Return an array of same dtype and shape as x and y.

    NOTE: Saturates at the point closest to zero to prevent negative results.
    '''
    fxAssert(x, y, **kwargs)

    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)
    dtype2 = fxDtypeLargerSigned(nBits)

    # Convert to something larger and signed in order for maximum to work.
    d = x.astype(dtype2) - y.astype(dtype2)
    ret_ = np.maximum(0, d - 1).astype(dtype1)

    if nBits in [8, 16]:
        # Coercing dtype performs implicit masking.
        ret = ret_
    else:
        ret = np.bitwise_and(ret_, fxOne(**kwargs))

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxSub

def fxReflect(x, **kwargs): # {{{
    '''Elementwise reflect a NumPy array for fixed point (0, 1].

    Take array x.
    Return an array of same dtype and shape as x.
    '''
    fxAssert(x, **kwargs)

    ret = fxSub(fxOnes(x.shape, **kwargs), x, **kwargs)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxReflect

def fxHadp(x, y, **kwargs): # {{{
    '''Elementwise multiply two NumPy arrays for fixed point (0, 1].

    Take arrays x, y of equal shape and equal dtype.
    Return an array of same dtype and shape as x and y.
    '''
    fxAssert(x, y, **kwargs)

    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)
    dtype2S = fxDtypeLargerSigned(nBits)
    dtype2U = fxDtypeLargerUnsigned(nBits)

    # dtype2 provides an accumulator for the additions.
    # NOTE: Debugging code left only commented out to allow one to see for
    # themselves why it's written this way - NumPy weirdness!
    prodAccU = np.multiply(x, y, dtype=dtype2U) + x + y
    #prodAccS = np.multiply(x, y, dtype=dtype2S) + x + y
    #print(hex(x), hex(y))
    #print("prodAccU", hex(prodAccU), prodAccU.dtype, len(bin(prodAccU)[2:]))
    #print("prodAccS", hex(prodAccS), prodAccS.dtype, len(bin(prodAccS)[2:]))

    #retU = np.divide(prodAccU, 2**nBits).astype(dtype2U) # Right shift not supported for uint64!
    #retS = np.right_shift(prodAccS, nBits, dtype=dtype2S)
    #print("retU", hex(retU), retU.dtype)
    #print("retS", hex(retS), retS.dtype)
    #assert np.all(retU == retS), (nBits, hex(retU), hex(retS))

    ret = np.right_shift(prodAccU.astype(dtype2S), nBits).astype(dtype1)
    #print("ret", hex(ret), ret.dtype)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxHadp

def fxPow(x, n, **kwargs): # {{{
    '''Raise elements of NumPy array to integer power n for fixed point (0, 1].

    Take array x.
    Return a scalar with the same dtype as x.

    Uses the exponention-by-squaring algorithm.
    https://en.wikipedia.org/wiki/Exponentiation_by_squaring
    '''
    fxAssert(x, **kwargs)

    nBits = _fxGetKwargs(**kwargs)

    assert isinstance(n, int), "n=%s must be an integer" % str(n)
    assert 0 <= n, "n=%s must be a non-negative integer" % str(n)

    if 1 == n:
        return x

    y = fxOnes(x.shape, **kwargs)
    if 0 == n:
        return y

    x_ = x
    n_ = n
    y_ = y
    while n_ > 1:
        if n_ % 2:
            y_ = fxHadp(x_, y_, **kwargs)
            n_ = (n_ - 1) >> 1
        else:
            n_ = n_ >> 1
        x_ = fxHadp(x_, x_, **kwargs)

    ret = fxHadp(x_, y_, **kwargs)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxPow

def fxRatio(n, d, **kwargs): # {{{
    '''Return ratio of integers n/d as fixed point (0, 1].

    NOTE: Avoids the use of IEEE754 floats in order to demonstrate an algorithm
    which implements in hardware.
    '''
    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)

    # Cast numerator and denominator to Python ints rather than asserting.
    n = int(abs(n))
    d = int(abs(d))

    assert n <= d, "n/d=%d/%d must be less than 1" % (n, d)

    if n == 0:
        ret_ = 0
    elif n == d:
        ret_ = 2**nBits - 1
    else:
        ret_ = 0                                # ret_ modified in place
        n_ = n                                  # n_ modified in place
        i_ = 1                                  # Loop counter
        while 0 <= (nBits - i_) and 0 <= n_:    # 0 <= n is fast exit
            if (n_ * 2**i_) >= d:           # (n_ << i_) > d
                ret_ |= 1 << (nBits - i_)   # OR in fraction bit
                n_ -= d // (2**i_)          # n_ = n_ - (d >> i_)
            i_ += 1                         # Count loops
        ret_ -= 1                           # Qn.n format to fx format

    ret = dtype1(ret_)

    fxAssert(ret, **kwargs)
    assert ret < 2**nBits, (ret, n, d)
    return ret
# }}} def fxRatio

def fxArithMean(X, **kwargs): # {{{
    '''Arithmetic Mean of NumPy array for fixed point (0, 1].

    Take array X.
    Return a scalar with the same dtype as X.
    Length of X must be an integer power of 2.

    This is the operation desired:
      (sum(X + 1) / len(X)) - 1
    Rearrange:
      (sum(X + 1) / len(X)) - 1
        let l = len(X)
      = (sum(X + 1) / l) - 1
      = ((sum(X) + l) / l) - 1
        assert l is integer power of 2
      = ((sum(X) + l) >> clog2(l)) - 1
    '''
    fxAssert(X, **kwargs)
    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)
    dtype2 = fxDtypeLargerSigned(nBits)

    lenx = len(X)
    assert np.isscalar(lenx)
    assert isPow2(lenx), "len(X)=%d must be an integer power of 2" % lenx

    sumx = np.sum(X, dtype=dtype2)
    assert np.isscalar(sumx)

    ret = dtype1(((sumx + lenx) >> clog2(lenx)) - 1)
    fxAssert(ret, **kwargs)
    assert np.isscalar(ret)

    return ret
# }}} def fxArithMean

def fxNonNegDeriv(X, **kwargs): # {{{
    '''Non-Negative Derivative of NumPy array for fixed point (0, 1].

    Take array X.
    Return an array with the same dtype and shape as X.

    NOTE: Edge values are rolled.
    This is the desired operation:
    X = [x0, x1, x2, ..., xN-1, xN]
    X_m1 = [x0, x0, x1, x2, ..., xN-1]
    X' = max(0, (X - X_m1))
    '''
    fxAssert(X, **kwargs)
    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)
    dtype2 = fxDtypeLargerSigned(nBits)

    x_m1 = np.roll(X, 1)
    x_m1[0] = x_m1[1]

    # Convert to something larger and signed in order for maximum to work.
    x2, x2_m1 = X.astype(dtype2), x_m1.astype(dtype2)

    ret = np.maximum(0, (x2 - x2_m1 - 1)).astype(dtype1)

    fxAssert(ret, X, **kwargs)
    return ret
# }}} def fxNonNegDeriv

def fxExpectation(W, X, **kwargs): # {{{
    '''Expected value, E[X]

    Take rows W, X of equal length and equal dtype.
    Return a scalar of same dtype as W or X.

    Equivalent to weighted arithmetic mean.

    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    fxAssert(W, X, **kwargs)

    ret = fxArithMean(fxHadp(W, X, **kwargs), **kwargs)
    assert np.isscalar(ret)

    return ret
# }}} def fxExpectation

def fxConditional(W, X, Y, **kwargs): # {{{
    '''Calculate E[X|Y]

    Take rows W, X, Y of equal length and equal dtype.
    Return a scalar.

    https://en.wikipedia.org/wiki/Bayesian_inference
    https://en.wikipedia.org/wiki/Bayes%27_theorem
    https://en.wikipedia.org/wiki/Window_function
    '''
    fxAssert(W, X, Y, **kwargs)

    Y_Ex = fxExpectation(W, Y, **kwargs)

    xHadpY_Ex = fxExpectation(W, fxHadp(X, Y, **kwargs), **kwargs)
    fxAssert(Y_Ex, geq=xHadpY_Ex, **kwargs)

    # NOTE: This fixed point representation has no 0, so there is no need to
    # check if Y_Ex == 0 to avoid NaN.

    ret = fxRatio(xHadpY_Ex+1, Y_Ex+1, **kwargs)
    assert np.isscalar(ret)

    return ret
# }}} def fxConditional

def fxDep(W, X, Y, **kwargs): # {{{
    '''Calculate Dep(X,Y)

    Take rows W, X, Y of equal length, and a threshold epsilon.
    Return a scalar.

    https://arxiv.org/abs/1905.06386 Visualizations for Understanding SoC Behaviour
    https://arxiv.org/abs/1905.12465 Relationship Detection Metrics for Binary SoC Data
    https://en.wikipedia.org/wiki/Window_function
    https://en.wikipedia.org/wiki/Bayesian_inference
    https://en.wikipedia.org/wiki/Independence_(probability_theory)
    https://en.wikipedia.org/wiki/Conditional_independence
    '''
    fxAssert(W, X, Y, **kwargs)
    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)

    X_Ex = fxExpectation(W, X, **kwargs)

    if 0 == X_Ex: # NOTE: Close to zero, not equal to zero.
        return fxZero(**kwargs)

    Y_Ex = fxExpectation(W, Y, **kwargs)

    if 0 == Y_Ex: # NOTE: Close to zero, not equal to zero.
        return fxZero(**kwargs)

    XY_Ex = fxHadp(X_Ex, Y_Ex, **kwargs)
    fxAssert(X_Ex, Y_Ex, geq=XY_Ex, **kwargs)

    xHadpY_Ex = fxExpectation(W, fxHadp(X, Y, **kwargs), **kwargs)
    fxAssert(X_Ex, Y_Ex, geq=xHadpY_Ex, **kwargs)

    if xHadpY_Ex < XY_Ex:
        return fxZero(**kwargs)

    ret = fxReflect(fxRatio(XY_Ex+1, xHadpY_Ex+1, **kwargs), **kwargs)
    assert np.isscalar(ret)

    return ret
# }}} def fxDep

def fxCov(W, X, Y, **kwargs): # {{{
    '''Calculate Cov(X,Y)

    Take rows W, X, Y of equal length, and a threshold epsilon.
    Return a scalar.

    https://en.wikipedia.org/wiki/Window_function
    https://en.wikipedia.org/wiki/Variance
    https://en.wikipedia.org/wiki/Covariance
    '''
    fxAssert(W, X, Y, **kwargs)
    nBits = _fxGetKwargs(**kwargs)
    dtype1 = fxDtype(nBits)

    X_Ex = fxExpectation(W, X, **kwargs)

    if 0 == X_Ex: # NOTE: Close to zero, not equal to zero.
        return fxZero(**kwargs)

    Y_Ex = fxExpectation(W, Y, **kwargs)

    if 0 == Y_Ex: # NOTE: Close to zero, not equal to zero.
        return fxZero(**kwargs)

    XY_Ex = fxHadp(X_Ex, Y_Ex, **kwargs)
    fxAssert(X_Ex, Y_Ex, geq=XY_Ex, **kwargs)

    if 0 == XY_Ex: # NOTE: Close to zero, not equal to zero.
        return fxZero(**kwargs)

    xHadpY_Ex = fxExpectation(W, fxHadp(X, Y, **kwargs), **kwargs)
    fxAssert(X_Ex, Y_Ex, geq=xHadpY_Ex, **kwargs)

    if xHadpY_Ex < XY_Ex:
        return fxZero(**kwargs)

    s = fxSub(xHadpY_Ex, XY_Ex, **kwargs)
    fxAssert(s, leq=(fxOne(**kwargs) >> 2).astype(dtype1), **kwargs)

    ret = (s * 4 + 3).astype(dtype1) # 4(s+1)-1 = 4s+3
    assert np.isscalar(ret)

    fxAssert(ret, **kwargs)
    return ret
# }}} def fxCov

if __name__ == "__main__":
    assert False, "Not a standalone script."
