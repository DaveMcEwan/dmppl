
from __future__ import absolute_import
from __future__ import division

import numpy as np

# TODO: eva
#   weightedMedian
#   downsample
#   deltashift

def ndAssertScalarNorm(x, **kwargs): # {{{
    '''Assert x is a scalar in normal range [0, 1]
    '''

    if np.isnan(x) and kwargs.get("allowNan", False):
        pass
    else:
        assert np.isscalar(x)
        assert 0.0 <= x <= 1.0, x

# }}} def ndAssertScalarNorm

def ndAssert(*args, **kwargs): # {{{
    '''Assert args are of matching shapes and correct range.

    Optionally set the eq,leq,geq,lt,gt keywords to an array of the same shape
    as the NumPy arrays in args to assert comparison properties.
    '''
    if __debug__:

        assertRange = kwargs.get("assertRange", True)

        for i,a in enumerate(args):
            b = args[i-1]
            assert a.shape == b.shape, (a.shape, b.shape)

            # NOTE: dtype assertions removed to allow forgiving type coercion.
            #assert a.dtype == b.dtype, (a.dtype, b.dtype)

            if assertRange:
                assert np.all(np.logical_and(0.0 <= a, a <= 1.0))


        eq = kwargs.get("eq")
        if eq is not None:
            #assert a.dtype == eq.dtype, (a.dtype, eq.dtype)
            assert a.shape == eq.shape, (a.shape, eq.shape)
            for i,a in enumerate(args):
                assert np.all(a == eq), (a, eq)

        leq = kwargs.get("leq")
        if leq is not None:
            #assert a.dtype == leq.dtype, (a.dtype, leq.dtype)
            assert a.shape == leq.shape, (a.shape, leq.shape)
            for i,a in enumerate(args):
                assert np.all(a <= leq), (a, leq)

        geq = kwargs.get("geq")
        if geq is not None:
            #assert a.dtype == geq.dtype, (a.dtype, geq.dtype)
            assert a.shape == geq.shape, (a.shape, geq.shape)
            for i,a in enumerate(args):
                assert np.all(a >= geq), (a, geq)

        lt = kwargs.get("lt")
        if lt is not None:
            #assert a.dtype == lt.dtype, (a.dtype, lt.dtype)
            assert a.shape == lt.shape, (a.shape, lt.shape)
            for i,a in enumerate(args):
                assert np.all(a < lt), (a, lt)

        gt = kwargs.get("gt")
        if gt is not None:
            #assert a.dtype == gt.dtype, (a.dtype, gt.dtype)
            assert a.shape == gt.shape, (a.shape, gt.shape)
            for i,a in enumerate(args):
                assert np.all(a > gt), (a, gt)

    return
# }}} def ndAssert

def ndAbsDiff(x, y): # {{{
    '''Elementwise difference of ndarrays.

    Boolean arrays use faster bitwise operations.
    On sets this is the symmetric difference.
    '''
    ret = np.logical_xor(x, y) if (np.bool == x.dtype == y.dtype) \
        else np.fabs(x - y)
    return ret
# }}} def ndAbsDiff

def ndHadp(x, y): # {{{
    '''Hadamard product of ndarrays, (elementwise multiplication).

    Boolean arrays use faster bitwise operations.
    On sets this is the intersection.
    '''
    ret = np.logical_and(x, y) if (np.bool == x.dtype == y.dtype) \
        else np.multiply(x, y)
    return ret
# }}} def ndHadp

def ndMax(x, y): # {{{
    '''Elementwise maximum.

    Boolean arrays use faster bitwise operations.
    On sets this is the union.
    '''
    ret = np.logical_or(x, y) if (np.bool == x.dtype == y.dtype) \
        else np.maximum(x, y)
    return ret
# }}} def ndMax

def ndEx(w, x, **kwargs): # {{{
    '''Expected value, E[X] of ndarray.

    Take weights w and ndarray x of equal shape.
    Return a scalar.

    assertRange optionally disables asserts allowing values in x outside [0,1].
    w_Area optionally provides pre-calculated sum of weights.

    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    ndAssert(w, x, **kwargs)

    _w_Area = kwargs.get("w_Area", None)
    w_Area = np.sum(w) if _w_Area is None else _w_Area
    assert np.isscalar(w_Area), type(w_Area)
    assert w_Area <= np.prod(w.shape), (w_Area, w.shape)

    wHadpX_Area = np.sum(ndHadp(w, x))
    assert np.isscalar(wHadpX_Area), type(wHadpX_Area)
    if kwargs.get("assertRange", True):
        assert wHadpX_Area <= w_Area, (wHadpX_Area, w_Area)

    ret = wHadpX_Area / w_Area if 0.0 < abs(w_Area) else w_Area
    ndAssertScalarNorm(ret)

    return ret
# }}} def ndEx

def ndCex(w, x, y, **kwargs): # {{{
    '''Conditional expected value, E[X|Y].

    Take weights w and ndarrays x, y of equal shape.
    Return a scalar.

    assertRange optionally disables asserts allowing values in x outside [0,1].
    y_Ex optionally provides pre-calculated E[Y].

    https://en.wikipedia.org/wiki/Bayesian_inference
    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    ndAssert(w, x, y, **kwargs)

    _y_Ex = kwargs.get("y_Ex", None)
    y_Ex = ndEx(w, y, **kwargs) if _y_Ex is None else _y_Ex
    ndAssertScalarNorm(y_Ex)

    if 0.0 == y_Ex:
        ret = np.nan
    else:
        _xHadpY_Ex = kwargs.get("xHadpY_Ex", None)
        xHadpY_Ex = ndEx(w, ndHadp(x, y), **kwargs) \
            if _xHadpY_Ex is None else _xHadpY_Ex
        ndAssertScalarNorm(xHadpY_Ex)
        assert xHadpY_Ex <= y_Ex, (xHadpY_Ex, y_Ex)

        ret = xHadpY_Ex / y_Ex
        ndAssertScalarNorm(ret)

    assert np.isnan(ret) or np.isscalar(ret), type(ret)

    return ret
# }}} def ndCex

def ndHam(w, x, y, **kwargs): # {{{
    '''Hamming similarity (weighted) between ndarrays X and Y.

    Take weights w and ndarrays x, y of equal shape.
    Return a scalar.

    assertRange optionally disables asserts allowing values in x outside [0,1].

    https://en.wikipedia.org/wiki/Hamming_distance
    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    ndAssert(w, x, y, **kwargs)

    _xDiffY_Ex = kwargs.get("xDiffY_Ex", None)
    xDiffY_Ex = ndEx(w, ndAbsDiff(x, y), **kwargs) \
        if _xDiffY_Ex is None else _xDiffY_Ex
    ndAssertScalarNorm(xDiffY_Ex)

    ret = 1.0 - xDiffY_Ex
    ndAssertScalarNorm(ret)

    return ret
# }}} def ndHam

def ndTmt(w, x, y, **kwargs): # {{{
    '''Tanimoto coefficient (weighted) between ndarrays X and Y.

    Take weights w and ndarrays x, y of equal shape.
    Return a scalar.

    assertRange optionally disables asserts allowing values in x outside [0,1].

    https://en.wikipedia.org/wiki/Jaccard_index
    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    ndAssert(w, x, y, **kwargs)

    _y_Ex = kwargs.get("y_Ex", None)
    y_Ex = ndEx(w, y, **kwargs) if _y_Ex is None else _y_Ex
    ndAssertScalarNorm(y_Ex)

    _x_Ex = kwargs.get("x_Ex", None)
    x_Ex = ndEx(w, x, **kwargs) if _x_Ex is None else _x_Ex
    ndAssertScalarNorm(x_Ex)

    _xHadpY_Ex = kwargs.get("xHadpY_Ex", None)
    xHadpY_Ex = ndEx(w, ndHadp(x, y), **kwargs) \
            if _xHadpY_Ex is None else _xHadpY_Ex
    ndAssertScalarNorm(xHadpY_Ex)

    denominator = x_Ex + y_Ex - xHadpY_Ex
    ret = 0.0 if 0.0 == denominator else (xHadpY_Ex / denominator)
    ndAssertScalarNorm(ret)

    return ret
# }}} def ndTmt

def ndCls(w, x, y, **kwargs): # {{{
    '''Euclidean closeness (weighted) between ndarrays X and Y.

    Take weights w and ndarrays x, y of equal shape.
    Return a scalar.

    assertRange optionally disables asserts allowing values in x outside [0,1].

    https://en.wikipedia.org/wiki/Closeness_(mathematics)
    https://en.wikipedia.org/wiki/Euclidean_distance
    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    ndAssert(w, x, y, **kwargs)

    xDiffY = ndAbsDiff(x, y)
    ndAssert(xDiffY, **kwargs)

    xDiffY2_Ex = ndEx(w, ndHadp(xDiffY, xDiffY), **kwargs)

    ret = 1.0 - np.sqrt(xDiffY2_Ex)
    ndAssertScalarNorm(ret)

    return ret
# }}} def ndCls

def ndCos(w, x, y, **kwargs): # {{{
    '''Cosine similarity (weighted) between ndarrays X and Y.

    Take weights w and ndarrays x, y of equal shape.
    Return a scalar.

    assertRange optionally disables asserts allowing values in x outside [0,1].

    https://en.wikipedia.org/wiki/Cosine_similarity
    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    ndAssert(w, x, y, **kwargs)

    _xHadpY_Ex = kwargs.get("xHadpY_Ex", None)
    xHadpY_Ex = ndEx(w, ndHadp(x, y), **kwargs) \
            if _xHadpY_Ex is None else _xHadpY_Ex
    ndAssertScalarNorm(xHadpY_Ex)

    x_Ex2 = ndEx(w, ndHadp(x, x), **kwargs)
    ndAssertScalarNorm(x_Ex2)

    y_Ex2 = ndEx(w, ndHadp(y, y), **kwargs)
    ndAssertScalarNorm(y_Ex2)

    # Finite precision with very high dimensional vectors means ret can
    # sometimes slightly exceed 1.0.
    ret = np.minimum(1.0,
                     0.0 if 0.0 in [x_Ex2, y_Ex2] else
                        (xHadpY_Ex / (np.sqrt(x_Ex2) * np.sqrt(y_Ex2))))
    ndAssertScalarNorm(ret)

    return ret
# }}} def ndCos

def ndCov(w, x, y, **kwargs): # {{{
    '''Covariance (weighted, positive) between ndarrays X and Y.

    Take weights w and ndarrays x, y of equal shape.
    Return a scalar.

    assertRange optionally disables asserts allowing values in x outside [0,1].

    https://en.wikipedia.org/wiki/Variance
    https://en.wikipedia.org/wiki/Covariance
    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    ndAssert(w, x, y, **kwargs)

    _y_Ex = kwargs.get("y_Ex", None)
    y_Ex = ndEx(w, y, **kwargs) if _y_Ex is None else _y_Ex
    ndAssertScalarNorm(y_Ex)

    _x_Ex = kwargs.get("x_Ex", None)
    x_Ex = ndEx(w, x, **kwargs) if _x_Ex is None else _x_Ex
    ndAssertScalarNorm(x_Ex)

    _xHadpY_Ex = kwargs.get("xHadpY_Ex", None)
    xHadpY_Ex = ndEx(w, ndHadp(x, y), **kwargs) \
            if _xHadpY_Ex is None else _xHadpY_Ex
    ndAssertScalarNorm(xHadpY_Ex)

    ret = 4 * np.fabs(xHadpY_Ex - (x_Ex * y_Ex))
    ndAssertScalarNorm(ret)

    return ret
# }}} def ndCov

def ndDep(w, x, y, **kwargs): # {{{
    '''Dependence between ndarrays X and Y.

    Take weights w and ndarrays x, y of equal shape.
    Return a scalar.

    assertRange optionally disables asserts allowing values in x outside [0,1].

    https://en.wikipedia.org/wiki/Bayesian_inference
    https://en.wikipedia.org/wiki/Independence_(probability_theory)
    https://en.wikipedia.org/wiki/Conditional_independence
    https://en.wikipedia.org/wiki/Expected_value
    https://en.wikipedia.org/wiki/Window_function
    '''
    ndAssert(w, x, y, **kwargs)

    _x_Ex = kwargs.get("x_Ex", None)
    x_Ex = ndEx(w, x, **kwargs) if _x_Ex is None else _x_Ex
    ndAssertScalarNorm(x_Ex)

    _x_Cex_Y = kwargs.get("x_Cex_Y", None)
    x_Cex_Y = ndCex(w, x, y, **kwargs) if _x_Cex_Y is None else _x_Cex_Y
    ndAssertScalarNorm(x_Cex_Y, allowNan=True)

    ret = ((x_Cex_Y - x_Ex) / x_Cex_Y) if x_Cex_Y > x_Ex else 0.0
    ndAssertScalarNorm(ret)

    return ret
# }}} def ndDep

if __name__ == "__main__":
    assert False, "Not a standalone script."
