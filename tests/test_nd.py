
import math
from dmppl.math import powsineCoeffs
from dmppl.nd import *
import unittest

class Test_ndAssertScalarNorm(unittest.TestCase): # {{{

    def test_Shape(self):

        ndAssertScalarNorm(0) # No raise
        self.assertRaises(AssertionError, ndAssertScalarNorm, np.array([0.5]))
        self.assertRaises(AssertionError, ndAssertScalarNorm, np.zeros((1,1)))

    def test_Range(self):

        ndAssertScalarNorm(False) # No raise
        ndAssertScalarNorm(True) # No raise
        ndAssertScalarNorm(0) # No raise
        ndAssertScalarNorm(1) # No raise
        ndAssertScalarNorm(0.0001) # No raise
        ndAssertScalarNorm(0.9999) # No raise
        ndAssertScalarNorm(np.sum([0.6666, 0.3333])) # No raise

        self.assertRaises(AssertionError, ndAssertScalarNorm, -0.0001)
        self.assertRaises(AssertionError, ndAssertScalarNorm, 1.0001)

# }}} class Test_ndAssertScalarNorm

class Test_ndAssert(unittest.TestCase): # {{{

    def test_Shape(self):
        w = np.array([True, False, True])
        x = np.array([0.1, 0.2, 0.3, 0.4])
        y = np.array([0.11, 0.22, 0.33])

        ndAssert(w) # No raise
        ndAssert(x) # No raise
        ndAssert(y) # No raise
        ndAssert(w, y) # No raise
        self.assertRaises(AssertionError, ndAssert, w, x)
        self.assertRaises(AssertionError, ndAssert, x, y)

    def test_Range(self):
        w = np.array([True, False, True])
        x = np.array([0.1, 0.2, 0.3])
        y = np.array([0, -4.4, 5.5])

        ndAssert(x) # No raise
        ndAssert(w, x) # No raise
        self.assertRaises(AssertionError, ndAssert, y)
        self.assertRaises(AssertionError, ndAssert, w, x, y)
        self.assertRaises(AssertionError, ndAssert, y, assertRange=True)
        ndAssert(w, x, y, assertRange=False) # No raise

    def test_Eq(self):
        w = np.array([True, False, True])
        x = np.array([0.1, 0.2, 0.3])

        ndAssert(w, eq=w) # No raise
        ndAssert(w, w, eq=w) # No raise
        ndAssert(x, eq=x) # No raise
        ndAssert(x, x, eq=x) # No raise

        self.assertRaises(AssertionError, ndAssert, w, eq=x)
        self.assertRaises(AssertionError, ndAssert, x, eq=w)

    def test_Lt(self):
        v = np.array([False, False, False])
        w = np.array([True, True, True])
        x = np.array([0.1, 0.2, 0.3])
        y = np.array([0.11, 0.22, 0.33])

        ndAssert(v, lt=w) # No raise
        self.assertRaises(AssertionError, ndAssert, w, lt=v)

        ndAssert(x, lt=y) # No raise
        self.assertRaises(AssertionError, ndAssert, y, lt=x)

        ndAssert(v, lt=x) # No raise
        self.assertRaises(AssertionError, ndAssert, x, lt=v)

        ndAssert(x, lt=w) # No raise
        self.assertRaises(AssertionError, ndAssert, w, lt=x)

    def test_Leq(self):
        v = np.array([False, False, False])
        w = np.array([True, True, True])
        x = np.array([0.1, 0.2, 0.3])
        y = np.array([0.11, 0.22, 0.33])

        ndAssert(w, leq=w) # No raise
        ndAssert(w, w, leq=w) # No raise
        ndAssert(x, leq=x) # No raise
        ndAssert(x, x, leq=x) # No raise

        ndAssert(v, leq=w) # No raise
        self.assertRaises(AssertionError, ndAssert, w, leq=v)

        ndAssert(x, leq=y) # No raise
        self.assertRaises(AssertionError, ndAssert, y, leq=x)

        ndAssert(v, leq=x) # No raise
        self.assertRaises(AssertionError, ndAssert, x, leq=v)

        ndAssert(x, leq=w) # No raise
        self.assertRaises(AssertionError, ndAssert, w, leq=x)

    def test_Gt(self):
        v = np.array([False, False, False])
        w = np.array([True, True, True])
        x = np.array([0.1, 0.2, 0.3])
        y = np.array([0.11, 0.22, 0.33])

        ndAssert(w, gt=v) # No raise
        self.assertRaises(AssertionError, ndAssert, v, gt=w)

        ndAssert(y, gt=x) # No raise
        self.assertRaises(AssertionError, ndAssert, x, gt=y)

        ndAssert(x, gt=v) # No raise
        self.assertRaises(AssertionError, ndAssert, v, gt=x)

        ndAssert(w, gt=x) # No raise
        self.assertRaises(AssertionError, ndAssert, x, gt=w)

    def test_Geq(self):
        v = np.array([False, False, False])
        w = np.array([True, True, True])
        x = np.array([0.1, 0.2, 0.3])
        y = np.array([0.11, 0.22, 0.33])

        ndAssert(w, geq=w) # No raise
        ndAssert(w, w, geq=w) # No raise
        ndAssert(x, geq=x) # No raise
        ndAssert(x, x, geq=x) # No raise

        ndAssert(w, geq=v) # No raise
        self.assertRaises(AssertionError, ndAssert, v, geq=w)

        ndAssert(y, geq=x) # No raise
        self.assertRaises(AssertionError, ndAssert, x, geq=y)

        ndAssert(x, geq=v) # No raise
        self.assertRaises(AssertionError, ndAssert, v, geq=x)

        ndAssert(w, geq=x) # No raise
        self.assertRaises(AssertionError, ndAssert, x, geq=w)

# }}} class Test_ndAssert

class Test_ndAbsDiff(unittest.TestCase): # {{{

    def test_Float(self):
        x = np.array([1.1, 2.2, 3.3])
        y = np.array([0, -4.4, 5.5])
        result = ndAbsDiff(x, y)
        self.assertTrue(np.allclose(result, np.array([1.1, 6.6, 2.2])))

    def test_Bool(self):
        x = np.array([0, 1, 0, 1], dtype=np.bool)
        y = np.array([0, 0, 1, 1], dtype=np.bool)
        result = ndAbsDiff(x, y)
        self.assertTrue(np.array_equal(result, np.array([0, 1, 1, 0], dtype=np.bool)))

    def test_Broadcast(self):
        x = np.array(12)
        y = np.array([3.4, 5, 66])
        result = ndAbsDiff(x, y)
        self.assertTrue(np.array_equal(result, np.array([8.6, 7, 54])))

    def test_MultiDim(self):
        x = np.ones((2,4))
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndAbsDiff(x, y)
        self.assertTrue(np.array_equal(result, np.array([[0, 0, 0, 0],
                                                         [1, 1, 1, 1]])))

# }}} class Test_ndAbsDiff

class Test_ndConv(unittest.TestCase): # {{{

    def test_Float(self):
        x = np.array([1.1, 2.2, 3.3])
        y = np.array([0, -4.4, 5.5])
        result = ndConv(x, y)
        self.assertTrue(np.allclose(result, np.array([0.0, -9.68, 18.15])))

    def test_Bool(self):
        x = np.array([0, 1, 0, 1], dtype=np.bool)
        y = np.array([0, 0, 1, 1], dtype=np.bool)
        result = ndConv(x, y)
        self.assertTrue(np.array_equal(result, np.array([0, 0, 0, 1], dtype=np.bool)))

    def test_Broadcast(self):
        x = np.array(12)
        y = np.array([3.4, 5, 6])
        result = ndConv(x, y)
        self.assertTrue(np.array_equal(result, np.array([40.8, 60, 72])))

    def test_MultiDim(self):
        x = np.ones((2,4))
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndConv(x, y)
        self.assertTrue(np.array_equal(result, y))

# }}} class Test_ndConv

class Test_ndMax(unittest.TestCase): # {{{

    def test_Float(self):
        x = np.array([1.1, 2.2, 3.3])
        y = np.array([0, -4.4, 5.5])
        result = ndMax(x, y)
        self.assertTrue(np.allclose(result, np.array([1.1, 2.2, 5.5])))

    def test_Bool(self):
        x = np.array([0, 1, 0, 1], dtype=np.bool)
        y = np.array([0, 0, 1, 1], dtype=np.bool)
        result = ndMax(x, y)
        self.assertTrue(np.array_equal(result, np.array([0, 1, 1, 1], dtype=np.bool)))

    def test_Broadcast(self):
        x = np.array(12)
        y = np.array([3.4, 5, 66])
        result = ndMax(x, y)
        self.assertTrue(np.array_equal(result, np.array([12, 12, 66])))

    def test_MultiDim(self):
        x = np.ones((2,4))
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndMax(x, y)
        self.assertTrue(np.array_equal(result, x))

# }}} class Test_ndMax

class Test_ndEx(unittest.TestCase): # {{{
    # TODO: assertRange
    # TODO: w_Area

    def test_ZeroWin(self):
        w = np.array([0, 0, 0])
        x = np.array([1, 1, 1])
        result = ndEx(w, x)
        self.assertAlmostEqual(result, 0)

    def test_AllZero(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 0, 0])
        result = ndEx(w, x)
        self.assertAlmostEqual(result, 0)

    def test_AllOne(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 1, 1])
        result = ndEx(w, x)
        self.assertAlmostEqual(result, 1)

    def test_MultiDim(self):
        w = np.ones((2,4))
        x = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndEx(w, x)
        self.assertAlmostEqual(result, 0.5)

    def test_SineWin(self):
        w = powsineCoeffs(6, 2)
        x = np.array([1, 1, 1, 0, 0, 0])
        result = ndEx(w, x)
        self.assertAlmostEqual(result, 0.5)

# }}} class Test_ndEx

class Test_ndCex(unittest.TestCase): # {{{
    # TODO: assertRange
    # TODO: y_Ex
    # TODO: xConvY_Ex

    def test_ZeroWin(self):
        w = np.array([0, 0, 0])
        x = np.array([1, 1, 1])
        y = np.array([1, 1, 1])
        result = ndCex(w, x, y)
        self.assertTrue(np.isnan(result))

    def test_AllZero(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 0, 0])
        y = np.array([0, 0, 0])
        result = ndCex(w, x, y)
        self.assertTrue(np.isnan(result))

    def test_AllOne(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 1, 1, 1])
        result = ndCex(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_MultiDim(self):
        w = np.ones((2,4))
        x = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndCex(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_SineWin(self):
        w = powsineCoeffs(6, 2)
        x = np.array([1, 1, 1, 0, 0, 0])
        y = np.array([1, 1, 1, 0, 0, 0])
        result = ndCex(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_ZeroCex(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 0, 1, 0])
        y = np.array([0, 1, 0, 1])
        result = ndCex(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_HalfCex(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndCex(w, x, y)
        self.assertAlmostEqual(result, 0.5)

# }}} class Test_ndCex

class Test_ndHam(unittest.TestCase): # {{{
    # TODO: assertRange
    # TODO: xDiffY_Ex
    # TODO: bool x,y

    def test_ZeroWin(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 1, 0])
        y = np.array([1, 0, 1])
        result = ndHam(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_AllZero(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 0, 0])
        y = np.array([0, 0, 0])
        result = ndHam(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_AllOne(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 1, 1, 1])
        result = ndHam(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_MultiDim(self):
        w = np.ones((2,4))
        x = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndHam(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_SineWin(self):
        w = powsineCoeffs(6, 2)
        x = np.array([1, 1, 1, 0, 0, 0])
        y = np.array([1, 1, 1, 0, 0, 0])
        result = ndHam(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_ZeroHam(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 0, 1, 0])
        y = np.array([0, 1, 0, 1])
        result = ndHam(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_HalfHam(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndHam(w, x, y)
        self.assertAlmostEqual(result, 0.5)

    def test_QuarterHam(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndHam(w, x, y)
        self.assertAlmostEqual(result, 0.25)

# }}} class Test_ndHam

class Test_ndTmt(unittest.TestCase): # {{{
    # TODO: assertRange
    # TODO: xConvY_Ex
    # TODO: bool x,y

    def test_ZeroWin(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 1, 0])
        y = np.array([1, 0, 1])
        result = ndTmt(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_AllZero(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 0, 0])
        y = np.array([0, 0, 0])
        result = ndTmt(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_AllOne(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 1, 1, 1])
        result = ndTmt(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_MultiDim(self):
        w = np.ones((2,4))
        x = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndTmt(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_SineWin(self):
        w = powsineCoeffs(6, 2)
        x = np.array([1, 1, 1, 0, 0, 0])
        y = np.array([1, 1, 1, 0, 0, 0])
        result = ndTmt(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_ZeroTmt(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 0, 1, 0])
        y = np.array([0, 1, 0, 1])
        result = ndTmt(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_ThirdTmt(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndTmt(w, x, y)
        self.assertAlmostEqual(result, 1.0/3)

    def test_QuarterTmt(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndTmt(w, x, y)
        self.assertAlmostEqual(result, 0.25)

# }}} class Test_ndTmt

class Test_ndCls(unittest.TestCase): # {{{
    # TODO: assertRange
    # TODO: xConvY_Ex
    # TODO: bool x,y

    def test_ZeroWin(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 1, 0])
        y = np.array([1, 0, 1])
        result = ndCls(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_AllZero(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 0, 0])
        y = np.array([0, 0, 0])
        result = ndCls(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_AllOne(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 1, 1, 1])
        result = ndCls(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_MultiDim(self):
        w = np.ones((2,4))
        x = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndCls(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_ZeroCls(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 0, 1, 0])
        y = np.array([0, 1, 0, 1])
        result = ndCls(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_HalfCls(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndCls(w, x, y)
        self.assertAlmostEqual(result, 1-math.sqrt(0.5))

    def test_OneCls(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 1, 0, 1])
        result = ndCls(w, x, y)
        self.assertAlmostEqual(result, 1.0)

# }}} class Test_ndCls

class Test_ndCos(unittest.TestCase): # {{{
    # TODO: assertRange
    # TODO: xConvY_Ex
    # TODO: bool x,y

    def test_ZeroWin(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 1, 0])
        y = np.array([1, 0, 1])
        result = ndCos(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_AllZero(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 0, 0])
        y = np.array([0, 0, 0])
        result = ndCos(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_AllOne(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 1, 1, 1])
        result = ndCos(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_MultiDim(self):
        w = np.ones((2,4))
        x = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndCos(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_ZeroCos(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 0, 1, 0])
        y = np.array([0, 1, 0, 1])
        result = ndCos(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_HalfCos(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndCos(w, x, y)
        self.assertAlmostEqual(result, 0.5)

    def test_OneCos(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 1, 0, 1])
        result = ndCos(w, x, y)
        self.assertAlmostEqual(result, 1.0)

# }}} class Test_ndCos

class Test_ndCov(unittest.TestCase): # {{{
    # TODO: assertRange
    # TODO: xConvY_Ex
    # TODO: bool x,y

    def test_ZeroWin(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 1, 0])
        y = np.array([1, 0, 1])
        result = ndCov(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_AllZero(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 0, 0])
        y = np.array([0, 0, 0])
        result = ndCov(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_AllOne(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 1, 1, 1])
        result = ndCov(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_MultiDim(self):
        w = np.ones((2,4))
        x = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndCov(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_NegOneCov(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 0, 1, 0])
        y = np.array([0, 1, 0, 1])
        result = ndCov(w, x, y)
        self.assertAlmostEqual(result, 1.0)

    def test_ZeroCov(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndCov(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_OneCov(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 1, 0, 1])
        result = ndCov(w, x, y)
        self.assertAlmostEqual(result, 1.0)

# }}} class Test_ndCov

class Test_ndDep(unittest.TestCase): # {{{
    # TODO: assertRange
    # TODO: xConvY_Ex
    # TODO: bool x,y

    def test_ZeroWin(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 1, 0])
        y = np.array([1, 0, 1])
        result = ndDep(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_AllZero(self):
        w = np.array([0, 0, 0])
        x = np.array([0, 0, 0])
        y = np.array([0, 0, 0])
        result = ndDep(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_AllOne(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 1, 1, 1])
        result = ndDep(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_MultiDim(self):
        w = np.ones((2,4))
        x = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        y = np.array([[1, 1, 1, 1],
                      [0, 0, 0, 0]])
        result = ndDep(w, x, y)
        self.assertAlmostEqual(result, 0.5)

    def test_ZeroDepA(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([1, 0, 1, 0])
        y = np.array([0, 1, 0, 1])
        result = ndDep(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_ZeroDepB(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        result = ndDep(w, x, y)
        self.assertAlmostEqual(result, 0.0)

    def test_HalfDep(self):
        w = np.array([1, 1, 1, 1])
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 1, 0, 1])
        result = ndDep(w, x, y)
        self.assertAlmostEqual(result, 0.5)

# }}} class Test_ndDep
