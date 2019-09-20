from dmppl.math import *
import math
import os
import tempfile
import shutil
import unittest

class Test_isPow2(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = isPow2(3)
        self.assertFalse(result)

    def test_Basic1(self):
        result = isPow2(4)
        self.assertTrue(result)

    def test_Int0(self):
        result = isPow2(7)
        self.assertFalse(result)

    def test_Int1(self):
        result = isPow2(8)
        self.assertTrue(result)

    def test_Neg0(self):
        self.assertRaises(AssertionError, isPow2, -8)

    def test_Float0(self):
        self.assertRaises(AssertionError, isPow2, 7.0)

# }}} class Test_isPow2

class Test_clog2(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = clog2(5)
        self.assertEqual(result, 3)

    def test_Int0(self):
        result = clog2(9)
        self.assertEqual(result, 4)

    def test_Float0(self):
        result = clog2(4.1)
        self.assertEqual(result, 3)

    def test_Neg0(self):
        self.assertRaises(AssertionError, clog2, -8)

# }}} class Test_clog2

class Test_clipNorm(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = clipNorm(0.3)
        self.assertEqual(result, 0.3)

    def test_Basic1(self):
        result = clipNorm(3, 0, 10)
        self.assertEqual(result, 0.3)

    def test_Basic2(self):
        result = clipNorm(0, -1, 1)
        self.assertEqual(result, 0.5)

    def test_Basic3(self):
        result = clipNorm(-0.25, -2.5, 2.5)
        self.assertEqual(result, 0.45)

    def test_Ints0(self):
        result = clipNorm(2, 1, 3)
        self.assertAlmostEqual(result, 0.5)

    def test_Floats0(self):
        result = clipNorm(2.0, 1.0, 3.0)
        self.assertAlmostEqual(result, 0.5)

    def test_Floats1(self):
        result = clipNorm(0.2, 0.1, 0.3)
        self.assertAlmostEqual(result, 0.5)

    def test_TypeMix0(self):
        result = clipNorm(2, 1, 3.0)
        self.assertAlmostEqual(result, 0.5)

    def test_TypeMix1(self):
        result = clipNorm(2, 1.0, 3)
        self.assertAlmostEqual(result, 0.5)

    def test_TypeMix2(self):
        result = clipNorm(2.0, 1, 3.0)
        self.assertAlmostEqual(result, 0.5)

    def test_TypeMix3(self):
        result = clipNorm(2.0, 1.0, 3)
        self.assertAlmostEqual(result, 0.5)

    def test_OutOfRangeLo0(self):
        result = clipNorm(0.1, 0.2, 0.3)
        self.assertEqual(result, 0.0)

    def test_OutOfRangeLo1(self):
        result = clipNorm(1, 2, 3)
        self.assertEqual(result, 0.0)

    def test_OutOfRangeLo2(self):
        result = clipNorm(0.1, 0.3, 0.2)
        self.assertEqual(result, 0.0)

    def test_OutOfRangeLo3(self):
        result = clipNorm(1, 3, 2)
        self.assertEqual(result, 0.0)

    def test_OutOfRangeHi0(self):
        result = clipNorm(0.4, 0.2, 0.3)
        self.assertEqual(result, 1.0)

    def test_OutOfRangeHi1(self):
        result = clipNorm(4, 2, 3)
        self.assertEqual(result, 1.0)

    def test_OutOfRangeHi2(self):
        result = clipNorm(0.4, 0.3, 0.2)
        self.assertEqual(result, 1.0)

    def test_OutOfRangeHi3(self):
        result = clipNorm(4, 3, 2)
        self.assertEqual(result, 1.0)

# }}} class Test_clipNorm

class Test_int2base(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = int2base(5, 2)
        self.assertEqual(result, "101")

    def test_Basic1(self):
        result = int2base(15, 16)
        self.assertEqual(result, "f")

    def test_Basic2(self):
        result = int2base(35**10-1, 35)
        self.assertEqual(result, "y"*10)

    def test_Float0(self):
        self.assertRaises(AssertionError, int2base, 8.0, 10)

    def test_Float1(self):
        self.assertRaises(AssertionError, int2base, 8, 10.0)

    def test_Neg0(self):
        self.assertRaises(AssertionError, int2base, -8, 10)

    def test_Neg1(self):
        self.assertRaises(AssertionError, int2base, 8, -10)

# }}} class Test_int2base

class Test_powsineCoeffs(unittest.TestCase): # {{{

    def test_Basic0(self):
        n = 10
        alpha = 0
        result = powsineCoeffs(n, alpha)
        self.assertEqual(len(result), n)
        self.assertEqual(result.shape, (n,))
        self.assertSequenceEqual(result.tolist(), np.ones(n).tolist())

    def test_Basic1(self):
        n = 5
        alpha = 1
        result = powsineCoeffs(n, alpha)
        self.assertEqual(result.shape, (n,))

        golden = np.array([0.0, 0.707, 1.0, 0.707, 0.0])
        self.assertTupleEqual(result.shape, golden.shape)

        for r,g in zip(result, golden):
            self.assertAlmostEqual(r, g, places=3)

    def test_Basic2(self):
        n = 10
        alpha = 2
        result = powsineCoeffs(n, alpha)
        self.assertEqual(result.shape, (n,))

        golden = np.array([0.000, 0.117, 0.413, 0.750, 0.970,
                           0.970, 0.750, 0.413, 0.117, 0.000])
        self.assertTupleEqual(result.shape, golden.shape)

        for r,g in zip(result, golden):
            self.assertAlmostEqual(r, g, places=3)

# }}} class Test_powsineCoeffs

class Test_saveNpy(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        arr = np.arange(5)
        fname = os.path.join(self.tstDir, "Basic0")
        result = saveNpy(arr, fname)
        self.assertEqual(result, None)

        # Load back in again with standard NumPy method.
        with gzip.GzipFile(fname + ".npy.gz", 'rb') as fd:
            rdbk = np.load(fd)

        for r,g in zip(rdbk, arr):
            self.assertEqual(r, g)

    def test_Basic1(self):
        arr = np.arange(6)
        fname = os.path.join(self.tstDir, "Basic1.npy.gz")
        result = saveNpy(arr, fname)
        self.assertEqual(result, None)

        # Load back in again with standard NumPy method.
        with gzip.GzipFile(fname, 'rb') as fd:
            rdbk = np.load(fd)

        for r,g in zip(rdbk, arr):
            self.assertEqual(r, g)

    def test_Basic2(self):
        arr = np.arange(7)
        fname = os.path.join(self.tstDir, "Basic2.npy")
        result = saveNpy(arr, fname)
        self.assertEqual(result, None)

        # Load back in again with standard NumPy method.
        with open(fname, 'rb') as fd:
            rdbk = np.load(fd)

        for r,g in zip(rdbk, arr):
            self.assertEqual(r, g)

# }}} class Test_saveNpy

class Test_loadNpy(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.arr0 = np.arange(5)
        fname0 = os.path.join(self.tstDir, "arr0.npy.gz")
        with gzip.GzipFile(fname0, 'wb') as fd:
            np.save(fd, self.arr0)

        self.arr1 = np.ones(6)
        fname1 = os.path.join(self.tstDir, "arr1.npy")
        with open(fname1, 'wb') as fd:
            np.save(fd, self.arr1)

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        fname = os.path.join(self.tstDir, "arr0")
        result = loadNpy(fname)

        for r,g in zip(result, self.arr0):
            self.assertEqual(r, g)

    def test_Basic1(self):
        fname = os.path.join(self.tstDir, "arr1.npy")
        result = loadNpy(fname)

        for r,g in zip(result, self.arr1):
            self.assertEqual(r, g)

    def test_Basic2(self):
        fname = os.path.join(self.tstDir, "arr0.npy.gz")
        result = loadNpy(fname)

        for r,g in zip(result, self.arr0):
            self.assertEqual(r, g)

# }}} class Test_loadNpy

class Test_ptScale(unittest.TestCase): # {{{

    def test_Int0(self):
        pt = (1, 2)
        scale = 3
        result = ptScale(pt, scale)
        self.assertTupleEqual(result, (3, 6))
        for r in result:
            self.assertIsInstance(r, int)

    def test_Float0(self):
        pt = (1.0, 2.0)
        scale = 3.5
        result = ptScale(pt, scale)
        self.assertTupleEqual(result, (3.5, 7.0))
        for r in result:
            self.assertIsInstance(r, float)

    def test_0D(self):
        self.assertRaises(AssertionError, ptScale, tuple(), 2.0)

    def test_1D(self):
        pt = (1,)
        scale = 3
        result = ptScale(pt, scale)
        self.assertTupleEqual(result, (3,))
        for r in result:
            self.assertIsInstance(r, int)

    def test_5D(self):
        pt = (1, 2, 3, 4, 5)
        scale = 10.0
        result = ptScale(pt, scale)
        self.assertTupleEqual(result, (10.0, 20.0, 30.0, 40.0, 50.0))
        for r in result:
            self.assertIsInstance(r, float)

# }}} class Test_ptScale

class Test_ptShift(unittest.TestCase): # {{{

    def test_Int0(self):
        pt = (1, 2)
        shift = [3, 4]
        result = ptShift(pt, shift)
        self.assertTupleEqual(result, (4, 6))
        for r in result:
            self.assertIsInstance(r, int)

    def test_Float0(self):
        pt = (1.0, 2.0)
        shift = [3.0, 4.0]
        result = ptShift(pt, shift)
        self.assertTupleEqual(result, (4.0, 6.0))
        for r in result:
            self.assertIsInstance(r, float)

    def test_NDimMismatch(self):
        self.assertRaises(AssertionError, ptShift, (1, 2), (3,))

    def test_0D(self):
        self.assertRaises(AssertionError, ptShift, tuple(), tuple())

    def test_1D(self):
        pt = (1,)
        shift = [3]
        result = ptShift(pt, shift)
        self.assertTupleEqual(result, (4,))
        for r in result:
            self.assertIsInstance(r, int)

    def test_5D(self):
        pt = (1, 2, 3, 4, 5)
        shift = [3, 4, 5, 6, 7]
        result = ptShift(pt, shift)
        self.assertTupleEqual(result, (4, 6, 8, 10, 12))
        for r in result:
            self.assertIsInstance(r, int)

# }}} class Test_ptShift

class Test_ptMirror(unittest.TestCase): # {{{

    def test_Int0(self):
        pt = (1, 2)
        mirror = [None, 3]
        result = ptMirror(pt, mirror)
        self.assertTupleEqual(result, (1, 4))
        for r in result:
            self.assertIsInstance(r, int)

    def test_Float0(self):
        pt = (1.0, 2.0)
        mirror = (3.5, None)
        result = ptMirror(pt, mirror)
        self.assertTupleEqual(result, (6.0, 2.0))
        for r in result:
            self.assertIsInstance(r, float)

    def test_0D(self):
        self.assertRaises(AssertionError, ptMirror, tuple(), [2.0])

    def test_NDimMismatch(self):
        self.assertRaises(AssertionError, ptShift, (1, 2), (3,))

    def test_1D(self):
        pt = (1,)
        mirror = (5.0,)
        result = ptMirror(pt, mirror)
        self.assertTupleEqual(result, (9.0,))
        for r in result:
            self.assertIsInstance(r, float)

    def test_5D(self):
        pt = (1, 2, 3, 4, 5)
        mirror = [10.0, None, 5, None, None]
        result = ptMirror(pt, mirror)
        self.assertTupleEqual(result, (19.0, 2, 7, 4, 5))
        for r in result:
            self.assertIsInstance(r, (float, int))

# }}} class Test_ptMirror

class Test_rotMat2D(unittest.TestCase): # {{{

    def test_Degrees90(self):
        result = rotMat2D(math.radians(90))
        self.assertAlmostEqual(result[0][0], 0);
        self.assertAlmostEqual(result[0][1], -1)
        self.assertAlmostEqual(result[1][0], 1);
        self.assertAlmostEqual(result[1][1], 0)

    def test_Degrees90CW(self):
        result = rotMat2D(math.radians(90), clockwise=True)
        self.assertAlmostEqual(result[0][0], 0);
        self.assertAlmostEqual(result[0][1], 1)
        self.assertAlmostEqual(result[1][0], -1);
        self.assertAlmostEqual(result[1][1], 0)

    def test_Degrees90CCW(self):
        result = rotMat2D(math.radians(90), clockwise=False)
        self.assertAlmostEqual(result[0][0], 0);
        self.assertAlmostEqual(result[0][1], -1)
        self.assertAlmostEqual(result[1][0], 1);
        self.assertAlmostEqual(result[1][1], 0)

# }}} class Test_rotMat2D

class Test_ptRotate(unittest.TestCase): # {{{

    def test_Basic0(self):
        rotation = rotMat2D(math.radians(90))
        pt = (0, 1) # Vertical
        result = ptRotate(pt, rotation)
        self.assertIsInstance(result, tuple)
        self.assertAlmostEqual(result[0], -1)
        self.assertAlmostEqual(result[1], 0)

    def test_Basic1(self):
        rotation = rotMat2D(math.radians(90))
        pt = (1, 0) # Horizontal
        result = ptRotate(pt, rotation)
        self.assertIsInstance(result, tuple)
        self.assertAlmostEqual(result[0], 0)
        self.assertAlmostEqual(result[1], 1)

    def test_Basic2(self):
        rotation = rotMat2D(math.radians(180))
        pt = (3, 3) # Horizontal
        center = (4, 4)
        result = ptRotate(pt, rotation, center)
        self.assertIsInstance(result, tuple)
        self.assertAlmostEqual(result[0], 5)
        self.assertAlmostEqual(result[1], 5)

# }}} class Test_ptRotate

class Test_ptRotate2D(unittest.TestCase): # {{{

    def test_Basic0(self):
        pt = (0, 1) # Vertical
        result = ptRotate2D(pt, math.radians(90))
        self.assertIsInstance(result, tuple)
        self.assertAlmostEqual(result[0], -1)
        self.assertAlmostEqual(result[1], 0)

    def test_Basic1(self):
        pt = (1, 0) # Horizontal
        result = ptRotate2D(pt, math.radians(90))
        self.assertIsInstance(result, tuple)
        self.assertAlmostEqual(result[0], 0)
        self.assertAlmostEqual(result[1], 1)

    def test_Basic2(self):
        pt = (3, 3) # Horizontal
        center = (4, 4)
        result = ptRotate2D(pt, math.radians(180), center)
        self.assertIsInstance(result, tuple)
        self.assertAlmostEqual(result[0], 5)
        self.assertAlmostEqual(result[1], 5)

# }}} class Test_ptRotate

class Test_ptsScale(unittest.TestCase): # {{{

    def test_NDimMismatch(self):
        pts = [(1, 2, 3), (4, 5)]
        scale = 10.0
        self.assertRaises(AssertionError, ptsScale, pts, scale)

    def test_5D(self):
        pts = [(1, 2, 3, 4, 5), (6, 7, 8, 9, 10)]
        scale = 10.0
        result = list(ptsScale(pts, scale))
        self.assertListEqual(result, [(10.0, 20.0, 30.0, 40.0, 50.0),
                                      (60.0, 70.0, 80.0, 90.0, 100.0)])

# }}} class Test_ptsScale

class Test_ptsShift(unittest.TestCase): # {{{

    def test_NDimMismatch(self):
        pts = [(1, 2, 3), (4, 5)]
        shift = (1, 2)
        self.assertRaises(AssertionError, ptsShift, pts, shift)

    def test_5D(self):
        pts = [(1, 2, 3, 4, 5), (6, 7, 8, 9, 10)]
        shift = [3, 4, 5, 6, 7]
        result = list(ptsShift(pts, shift))
        self.assertListEqual(result, [(4, 6, 8, 10, 12),
                                       (9, 11, 13, 15, 17)])

# }}} class Test_ptsShift

class Test_ptsMirror(unittest.TestCase): # {{{

    def test_NDimMismatch(self):
        pts = [(1, 2, 3), (4, 5)]
        mirror = [10.0, None, 5]
        self.assertRaises(AssertionError, ptsMirror, pts, mirror)

    def test_5D(self):
        pts = [(1, 2, 3, 4, 5), (6, 7, 8, 9, 10)]
        mirror = [10.0, None, 5, None, None]
        result = list(ptsMirror(pts, mirror))
        self.assertListEqual(result, [(19.0, 2, 7, 4, 5),
                                      (14.0, 7, 2, 9, 10)])
        for pt in result:
            for r in pt:
                self.assertIsInstance(r, (float, int))

# }}} class Test_ptsMirror

class Test_ptsRotate2D(unittest.TestCase): # {{{

    def test_Basic0(self):
        pts = [(0, 1), (5, 0)]
        result = list(ptsRotate2D(pts, math.radians(90)))
        self.assertAlmostEqual(result[0][0], -1.0)
        self.assertAlmostEqual(result[0][1], 0.0)
        self.assertAlmostEqual(result[1][0], 0.0)
        self.assertAlmostEqual(result[1][1], 5.0)
        for pt in result:
            for r in pt:
                self.assertIsInstance(r, float)

# }}} class Test_ptsRotate2D

class Test_ptPairDifference(unittest.TestCase): # {{{

    def test_Int0(self):
        ptA = (1, 2)
        ptB = [3, 4]
        result = ptPairDifference(ptA, ptB)
        self.assertTupleEqual(result, (2, 2))
        for r in result:
            self.assertIsInstance(r, int)

    def test_Float0(self):
        ptA = (1.0, 2.0)
        ptB = [3.0, 4.0]
        result = ptPairDifference(ptA, ptB)
        self.assertTupleEqual(result, (2.0, 2.0))
        for r in result:
            self.assertIsInstance(r, float)

    def test_NDimMismatch(self):
        self.assertRaises(AssertionError, ptPairDifference, (1, 2), (3,))

    def test_1D(self):
        ptA = [3,]
        ptB = (1,)
        result = ptPairDifference(ptA, ptB)
        self.assertTupleEqual(result, (-2,))
        for r in result:
            self.assertIsInstance(r, int)

    def test_5D(self):
        ptA = (1, 2, 3.0, 400, 5)
        ptB = (3, 40, 5, 6, 7.5)
        result = ptPairDifference(ptA, ptB)
        self.assertTupleEqual(result, (2, 38, 2.0, -394, 2.5))
        for r in result:
            self.assertIsInstance(r, (int, float))

# }}} class Test_ptPairDifference

class Test_ptPairPtBetween(unittest.TestCase): # {{{

    def test_Int0(self):
        ptA = (1, 2)
        ptB = [3, 4]
        result = ptPairPtBetween(ptA, ptB)
        self.assertTupleEqual(result, (2.0, 3.0))
        for r in result:
            self.assertIsInstance(r, float)

    def test_Float0(self):
        ptA = (1.0, 2.0)
        ptB = [3.0, 4.0]
        result = ptPairPtBetween(ptA, ptB)
        self.assertTupleEqual(result, (2.0, 3.0))
        for r in result:
            self.assertIsInstance(r, float)

    def test_Float1(self):
        ptA = (1.0, 2.0)
        ptB = [3.0, 4.0]
        fraction = 0.75
        result = ptPairPtBetween(ptA, ptB, fraction)
        self.assertTupleEqual(result, (2.5, 3.5))
        for r in result:
            self.assertIsInstance(r, float)

    def test_NDimMismatch(self):
        self.assertRaises(AssertionError, ptPairPtBetween, (1, 2), (3,))

    def test_NonFraction(self):
        self.assertRaises(AssertionError, ptPairPtBetween, (1, 2), (3, 4), 1.5)

    def test_1D(self):
        ptA = [3,]
        ptB = (1,)
        result = ptPairPtBetween(ptA, ptB)
        self.assertTupleEqual(result, (2.0,))
        for r in result:
            self.assertIsInstance(r, float)

    def test_5D(self):
        ptA = (1, 2, 3.0, 400, 5)
        ptB = (3, 40, 5, 6, 7.5)
        result = ptPairPtBetween(ptA, ptB)
        self.assertTupleEqual(result, (2.0, 21.0, 4.0, 203.0, 6.25))
        for r in result:
            self.assertIsInstance(r, float)

# }}} class Test_ptPairPtBetween

class Test_ptPairDistance(unittest.TestCase): # {{{

    def test_Int0(self):
        ptA = (1, 2)
        ptB = [3, 4]
        result = ptPairDistance(ptA, ptB)
        self.assertAlmostEqual(result, 2*math.sqrt(2))

    def test_Float0(self):
        ptA = (1.0, 2.0)
        ptB = [3.0, 4.0]
        result = ptPairDistance(ptA, ptB)
        self.assertAlmostEqual(result, 2*math.sqrt(2))

    def test_NDimMismatch(self):
        self.assertRaises(AssertionError, ptPairDistance, (1, 2), (3,))

    def test_1D(self):
        ptA = [3,]
        ptB = (1,)
        result = ptPairDistance(ptA, ptB)
        self.assertAlmostEqual(result, 2.0)

    def test_5D(self):
        ptA = (1, 2, 3.0, 400, 5)
        ptB = (3, 40, 5, 6, 7.5)
        result = ptPairDistance(ptA, ptB)
        golden = math.sqrt(sum([2**2, 38**2, 2.0**2, (-394)**2, 2.5**2]))
        self.assertAlmostEqual(result, golden)

# }}} class Test_ptPairDistance

class Test_ptPairsDifference(unittest.TestCase): # {{{

    def test_Basic0(self):
        ptPairs = [
            [(1, 2), (3, 4)],
            [(9, 8), (7, 6)],
            ((10, 20), (30, 40)),
            ((90, 80), (75, 65)),
            ((90, 80), (77, 67)),
        ]
        result = list(ptPairsDifference(ptPairs))
        self.assertListEqual(result, [(2, 2),
                                      (-2, -2),
                                      (20, 20),
                                      (-15, -15),
                                      (-13, -13)])

# }}} class Test_ptPairsDifference

class Test_ptPairsPtBetween(unittest.TestCase): # {{{

    def test_Basic0(self):
        ptPairs = [
            [(1, 2), (3, 4)],
            [(9, 8), (7, 6)],
        ]
        result = list(ptPairsPtBetween(ptPairs, fraction=0.75))
        self.assertListEqual(result, [(2.5, 3.5), (7.5, 6.5)])
# }}} class Test_ptPairsPtBetween

class Test_ptPairsDistance(unittest.TestCase): # {{{

    def test_Basic0(self):
        ptPairs = [
            [(1, 2), (3, 4)],
            [(9, 8), (7, 6)],
        ]
        result = list(ptPairsDistance(ptPairs))
        self.assertAlmostEqual(result[0], 2*math.sqrt(2))
        self.assertAlmostEqual(result[1], 2*math.sqrt(2))
# }}} class Test_ptPairsDistance

class Test_ptsMkPolygon(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = list(ptsMkPolygon(4))
        golden = [(1,0), (0,1), (-1,0), (0,-1)]
        np.testing.assert_almost_equal(result, golden)

    def test_Basic1(self):
        result = list(ptsMkPolygon(4, radius=[2]))
        golden = [(2,0), (0,2), (-2,0), (0,-2)]
        np.testing.assert_almost_equal(result, golden)

    def test_Basic2(self):
        result = list(ptsMkPolygon(4, radius=[2, 3]))
        golden = [(2,0), (0,3), (-2,0), (0,-3)]
        np.testing.assert_almost_equal(result, golden)

# }}} class Test_ptsMkPolygon

