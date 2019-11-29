from dmppl.fx import *
import numpy as np
import unittest

def getFracs(nBits):
    '''Common fractions used in lots of tests
    '''
    h = (fxOne(nBits=nBits) >> 1).astype(fxDtype(nBits))
    q = (fxOne(nBits=nBits) >> 2).astype(fxDtype(nBits))
    e = (fxOne(nBits=nBits) >> 3).astype(fxDtype(nBits))
    s = (fxOne(nBits=nBits) >> 4).astype(fxDtype(nBits))
    t = fxAdd(h, q, nBits=nBits)
    return h, q, e, s, t

class Test_fxDtype(unittest.TestCase): # {{{

    def test_8b(self):
        for i in range(2, 8+1):
            self.assertEqual(fxDtype(i), np.uint8)

    def test_16b(self):
        for i in range(9, 16+1):
            self.assertEqual(fxDtype(i), np.uint16)

    def test_32b(self):
        for i in range(17, 31+1):
            self.assertEqual(fxDtype(i), np.uint32)

    def test_64b(self):
        for i in range(32, 64+1):
            self.assertRaises(AssertionError, fxDtype, i)
        for i in range(32, 64+1):
            self.assertEqual(fxDtype(i, allowUnsafe=True), np.uint64)

# }}} class Test_fxDtype

class Test_fxDtypeLargerSigned(unittest.TestCase): # {{{

    def test_8b(self):
        for i in range(2, 8+1):
            self.assertEqual(fxDtypeLargerSigned(i), np.int16)

    def test_16b(self):
        for i in range(9, 16+1):
            self.assertEqual(fxDtypeLargerSigned(i), np.int32)

    def test_32b(self):
        for i in range(17, 31+1):
            self.assertEqual(fxDtypeLargerSigned(i), np.int64)

    def test_64b(self):
        for i in range(32, 64+1):
            self.assertRaises(AssertionError, fxDtypeLargerSigned, i)

# }}} class Test_fxDtypeLargerSigned

class Test_fxDtypeLargerUnsigned(unittest.TestCase): # {{{

    def test_8b(self):
        for i in range(2, 8+1):
            self.assertEqual(fxDtypeLargerUnsigned(i), np.uint16)

    def test_16b(self):
        for i in range(9, 16+1):
            self.assertEqual(fxDtypeLargerUnsigned(i), np.uint32)

    def test_32b(self):
        for i in range(17, 31+1):
            self.assertEqual(fxDtypeLargerUnsigned(i), np.uint64)

    def test_64b(self):
        for i in range(32, 64+1):
            self.assertRaises(AssertionError, fxDtypeLargerUnsigned, i)

# }}} class Test_fxDtypeLargerUnsigned

class Test_fxAssert(unittest.TestCase): # {{{

    def test_Type0(self):
        x8 = np.array([1, 2, 3], dtype=np.uint8)
        y8 = np.array([4, 5, 6], dtype=np.uint8)
        x16 = np.array([1, 2, 3], dtype=np.uint16)
        y16 = np.array([4, 5, 6], dtype=np.uint16)
        x32 = np.array([1, 2, 3], dtype=np.uint32)
        y32 = np.array([4, 5, 6], dtype=np.uint32)
        kwargs = {"nBits": 8}

        fxAssert(x8, x8, **kwargs) # No raise
        fxAssert(y8, y8, **kwargs) # No raise
        fxAssert(x8, y8, **kwargs) # No raise
        self.assertRaises(AssertionError, fxAssert, x8, x16, **kwargs)
        self.assertRaises(AssertionError, fxAssert, x8, y16, **kwargs)
        self.assertRaises(AssertionError, fxAssert, x8, y32, **kwargs)
        self.assertRaises(AssertionError, fxAssert, x16, y32, **kwargs)

    def test_Shape0(self):
        x8 = np.array([1, 2, 3], dtype=np.uint8)
        y8 = np.array([4, 5], dtype=np.uint8)
        z8 = np.array([[4], [5], [6]], dtype=np.uint8)
        kwargs = {"nBits": 8}
        self.assertRaises(AssertionError, fxAssert, x8, y8, **kwargs)
        self.assertRaises(AssertionError, fxAssert, x8, z8, **kwargs)
        self.assertRaises(AssertionError, fxAssert, y8, z8, **kwargs)

    def test_DefaultNBits(self):
        x16 = np.array([1, 2, 3], dtype=np.uint16)
        y16 = np.array([4, 5, 6], dtype=np.uint16)
        x32 = np.array([1, 2, 3], dtype=np.uint32)
        y32 = np.array([4, 5, 6], dtype=np.uint32)

        fxAssert(x16, y16, nBits=16) # No raise
        self.assertRaises(AssertionError, fxAssert, x16, y16)
        fxAssert(x32, y32, nBits=31) # No raise
        self.assertRaises(AssertionError, fxAssert, x32, y32)

    def test_Eq(self):
        x8 = np.array([1, 2, 3], dtype=np.uint8)
        y8 = np.array([1, 2, 3], dtype=np.uint8)
        arr123 = np.array([1, 2, 3], dtype=np.uint8)
        arr789 = np.array([7, 8, 9], dtype=np.uint8)

        fxAssert(x8, eq=arr123) # No raise
        fxAssert(y8, eq=arr123) # No raise
        fxAssert(x8, y8, eq=arr123) # No raise
        self.assertRaises(AssertionError, fxAssert, x8, eq=arr789)

    def test_Leq(self):
        x8 = np.array([1, 2, 3], dtype=np.uint8)
        y8 = np.array([4, 5, 6], dtype=np.uint8)
        arr123 = np.array([1, 2, 3], dtype=np.uint8)
        arr789 = np.array([7, 8, 9], dtype=np.uint8)

        fxAssert(x8, leq=arr123) # No raise
        fxAssert(x8, leq=arr789) # No raise
        fxAssert(y8, leq=arr789) # No raise
        fxAssert(x8, y8, leq=arr789) # No raise
        self.assertRaises(AssertionError, fxAssert, y8, leq=arr123)
        self.assertRaises(AssertionError, fxAssert, arr789, leq=arr123)
        self.assertRaises(AssertionError, fxAssert, arr789, leq=y8)

    def test_Geq(self):
        x8 = np.array([1, 2, 3], dtype=np.uint8)
        y8 = np.array([4, 5, 6], dtype=np.uint8)
        arr123 = np.array([1, 2, 3], dtype=np.uint8)
        arr789 = np.array([7, 8, 9], dtype=np.uint8)

        fxAssert(arr123, geq=x8) # No raise
        fxAssert(arr789, geq=x8) # No raise
        fxAssert(arr789, geq=y8) # No raise
        fxAssert(y8, arr789, geq=x8) # No raise
        self.assertRaises(AssertionError, fxAssert, arr123, geq=y8)
        self.assertRaises(AssertionError, fxAssert, arr123, geq=arr789)
        self.assertRaises(AssertionError, fxAssert, y8, geq=arr789)

    def test_Lt(self):
        x8 = np.array([1, 2, 3], dtype=np.uint8)
        y8 = np.array([4, 5, 6], dtype=np.uint8)
        arr123 = np.array([1, 2, 3], dtype=np.uint8)
        arr789 = np.array([7, 8, 9], dtype=np.uint8)

        fxAssert(x8, lt=arr789) # No raise
        fxAssert(y8, lt=arr789) # No raise
        fxAssert(x8, y8, lt=arr789) # No raise
        self.assertRaises(AssertionError, fxAssert, arr789, lt=arr123)

    def test_Gt(self):
        x8 = np.array([1, 2, 3], dtype=np.uint8)
        y8 = np.array([4, 5, 6], dtype=np.uint8)
        arr123 = np.array([1, 2, 3], dtype=np.uint8)
        arr789 = np.array([7, 8, 9], dtype=np.uint8)

        fxAssert(arr789, gt=x8) # No raise
        fxAssert(arr789, gt=y8) # No raise
        fxAssert(arr789, y8, gt=x8) # No raise
        self.assertRaises(AssertionError, fxAssert, arr123, gt=arr789)

# }}} class Test_fxAssert

class Test_fxZero(unittest.TestCase): # {{{

    def test_NBits(self):
        npZero = np.array([0])[0]

        for i in range(2, 8+1):
            self.assertEqual(fxZero(nBits=i), npZero.astype(np.uint8))
        for i in range(9, 16+1):
            self.assertEqual(fxZero(nBits=i), npZero.astype(np.uint16))
        for i in range(17, 31+1):
            self.assertEqual(fxZero(nBits=i), npZero.astype(np.uint32))
        for i in range(32, 64+1):
            self.assertRaises(AssertionError, fxZero, nBits=i)

# }}} class Test_fxZero

class Test_fxOne(unittest.TestCase): # {{{

    def test_NBits(self):

        for i in range(2, 8+1):
            npOne = np.array([2**i-1])[0]
            self.assertEqual(fxOne(nBits=i), npOne.astype(np.uint8))
        for i in range(9, 16+1):
            npOne = np.array([2**i-1])[0]
            self.assertEqual(fxOne(nBits=i), npOne.astype(np.uint16))
        for i in range(17, 31+1):
            npOne = np.array([2**i-1])[0]
            self.assertEqual(fxOne(nBits=i), npOne.astype(np.uint32))
        for i in range(32, 64+1):
            self.assertRaises(AssertionError, fxOne, nBits=i)

# }}} class Test_fxOne

class Test_fxZeros(unittest.TestCase): # {{{

    def test_NBits(self):
        shape = (3, 4)
        npZero = np.array([0])

        for i in range(2, 8+1):
            self.assertTrue(np.all(fxZeros(shape, nBits=i) == npZero.astype(np.uint8)))
        for i in range(9, 16+1):
            self.assertTrue(np.all(fxZeros(shape, nBits=i) == npZero.astype(np.uint16)))
        for i in range(17, 31+1):
            self.assertTrue(np.all(fxZeros(shape, nBits=i) == npZero.astype(np.uint32)))
        for i in range(32, 64+1):
            self.assertRaises(AssertionError, fxZeros, shape, nBits=i)

    def test_Shapes(self):
        shapes = [
            (1,),
            (2,),
            (1, 2),
            (3, 4),
            (5, 6, 7),
            (8, 9, 10, 11),
        ]

        for shape in shapes:
            for i in range(2, 31+1):
                self.assertEqual(fxZeros(shape, nBits=i).shape, shape)

# }}} class Test_fxZeros

class Test_fxOnes(unittest.TestCase): # {{{

    def test_NBits(self):
        shape = (3, 4)
        npZero = np.array([0])

        for i in range(2, 8+1):
            npOne = np.array([2**i-1])[0].astype(np.uint8)
            self.assertTrue(np.all(fxOnes(shape, nBits=i) == npOne))
        for i in range(9, 16+1):
            npOne = np.array([2**i-1])[0].astype(np.uint16)
            self.assertTrue(np.all(fxOnes(shape, nBits=i) == npOne))
        for i in range(17, 31+1):
            npOne = np.array([2**i-1])[0].astype(np.uint32)
            self.assertTrue(np.all(fxOnes(shape, nBits=i) == npOne))
        for i in range(32, 64+1):
            self.assertRaises(AssertionError, fxOnes, shape, nBits=i)

    def test_Shapes(self):
        shapes = [
            (1,),
            (2,),
            (1, 2),
            (3, 4),
            (5, 6, 7),
            (8, 9, 10, 11),
        ]

        for shape in shapes:
            for i in range(2, 31+1):
                self.assertEqual(fxOnes(shape, nBits=i).shape, shape)

# }}} class Test_fxOnes

class Test_fxToFloat(unittest.TestCase): # {{{

    def test_ClosestToZero(self):
        for i in range(2, 31+1):
            z = fxZero(nBits=i)
            c = (2**i)**-1
            self.assertEqual(fxToFloat(z, nBits=i), c)

    def test_EqualToOne(self):
        for i in range(2, 31+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxToFloat(o, nBits=i), 1.0)

    def test_EqualToHalf(self):
        for i in range(2, 31+1):
            h = (fxOne(nBits=i) >> 1).astype(fxDtype(nBits=i))
            self.assertEqual(fxToFloat(h, nBits=i), 0.5)

    def test_EqualToQuarter(self):
        for i in range(2, 31+1):
            q = (fxOne(nBits=i) >> 2).astype(fxDtype(nBits=i))
            self.assertEqual(fxToFloat(q, nBits=i), 0.25)

# }}} class Test_fxToFloat

class Test_fxFromFloat(unittest.TestCase): # {{{

    def test_ClosestToZero(self):
        for i in range(2, 31+1):
            z = fxZero(nBits=i)
            c = (2**i)**-1
            self.assertEqual(fxFromFloat(c, nBits=i), z)

    def test_EqualToOne(self):
        for i in range(2, 31+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxFromFloat(1.0, nBits=i), o)

    def test_EqualToHalf(self):
        for i in range(2, 31+1):
            h = fxOne(nBits=i) >> 1
            self.assertEqual(fxFromFloat(0.5, nBits=i), h)

    def test_EqualToQuarter(self):
        for i in range(2, 31+1):
            q = fxOne(nBits=i) >> 2
            self.assertEqual(fxFromFloat(0.25, nBits=i), q)

# }}} class Test_fxFromFloat

class Test_fxAdd(unittest.TestCase): # {{{

    def test_ZeroZero(self):
        z = fxZero()
        self.assertEqual(fxAdd(z, z), np.array(1, dtype=np.uint8))
        for i in range(2, 8+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxAdd(z, z, nBits=i), np.array(1, dtype=np.uint8))
        for i in range(9, 16+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxAdd(z, z, nBits=i), np.array(1, dtype=np.uint16))
        for i in range(17, 31+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxAdd(z, z, nBits=i), np.array(1, dtype=np.uint32))

    def test_ZerosZeros(self):
        for i in range(2, 8+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxAdd(z, z, nBits=i) == np.ones(shape, dtype=np.uint8)))
        for i in range(9, 16+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxAdd(z, z, nBits=i) == np.ones(shape, dtype=np.uint16)))
        for i in range(17, 31+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxAdd(z, z, nBits=i) == np.ones(shape, dtype=np.uint32)))

    def test_OneOne(self):
        o = fxOne()
        self.assertEqual(fxAdd(o, o), np.array(0xff, dtype=np.uint8))
        for i in range(2, 8+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxAdd(o, o, nBits=i), np.array(2**i-1, dtype=np.uint8))
        for i in range(9, 16+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxAdd(o, o, nBits=i), np.array(2**i-1, dtype=np.uint16))
        for i in range(17, 31+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxAdd(o, o, nBits=i), np.array(2**i-1, dtype=np.uint32))

    def test_OnesOnes(self):
        for i in range(2, 8+1):
            shape = (3, 4)
            o = fxOnes(shape, nBits=i)
            ob = np.broadcast_to(o.astype(np.uint8), shape)
            self.assertTrue(np.all(fxAdd(o, o, nBits=i) == ob))
        for i in range(9, 16+1):
            shape = (3, 4)
            o = fxOnes(shape, nBits=i)
            ob = np.broadcast_to(o.astype(np.uint16), shape)
            self.assertTrue(np.all(fxAdd(o, o, nBits=i) == ob))
        for i in range(17, 31+1):
            shape = (3, 4)
            o = fxOnes(shape, nBits=i)
            ob = np.broadcast_to(o.astype(np.uint32), shape)
            self.assertTrue(np.all(fxAdd(o, o, nBits=i) == ob))

    def test_QuarterQuarter(self):
        q = np.array(0x3f, dtype=np.uint8)
        h = np.array(0x7f, dtype=np.uint8)
        self.assertEqual(fxAdd(q, q), h)

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxAdd(q, q, nBits=i), h)

    def test_HalfHalf(self):
        h = np.array(0x7f, dtype=np.uint8)
        self.assertEqual(fxAdd(h, h), fxOne())

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxAdd(h, h, nBits=i), fxOne(nBits=i))

    def test_QuarterHalf(self):
        q = np.array(0x3f, dtype=np.uint8)
        h = np.array(0x7f, dtype=np.uint8)
        t = np.array(0xbf, dtype=np.uint8) # 3/4
        self.assertEqual(fxAdd(q, h), t)
        self.assertEqual(fxAdd(h, q), t)

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxAdd(q, h, nBits=i), t)
            self.assertEqual(fxAdd(h, q, nBits=i), t)

# }}} class Test_fxAdd

class Test_fxSub(unittest.TestCase): # {{{

    def test_ZeroZero(self):
        z = fxZero()
        self.assertEqual(fxSub(z, z), np.array(0, dtype=np.uint8))
        for i in range(2, 8+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxSub(z, z, nBits=i), np.array(0, dtype=np.uint8))
        for i in range(9, 16+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxSub(z, z, nBits=i), np.array(0, dtype=np.uint16))
        for i in range(17, 31+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxSub(z, z, nBits=i), np.array(0, dtype=np.uint32))

    def test_ZerosZeros(self):
        for i in range(2, 8+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxSub(z, z, nBits=i) == np.zeros(shape, dtype=np.uint8)))
        for i in range(9, 16+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxSub(z, z, nBits=i) == np.zeros(shape, dtype=np.uint16)))
        for i in range(17, 31+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxSub(z, z, nBits=i) == np.zeros(shape, dtype=np.uint32)))

    def test_OneOne(self):
        o = fxOne()
        self.assertEqual(fxSub(o, o), np.array(0, dtype=np.uint8))
        for i in range(2, 31+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxSub(o, o, nBits=i), 0)

    def test_OnesOnes(self):
        shape = (3, 4)
        for i in range(2, 31+1):
            o = fxOnes(shape, nBits=i)
            self.assertTrue(np.all(fxSub(o, o, nBits=i) == np.zeros(shape)))

    def test_QuarterQuarter(self):
        q = np.array(0x3f, dtype=np.uint8)
        self.assertEqual(fxSub(q, q), fxZero())

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxSub(q, q, nBits=i), fxZero(nBits=i))

    def test_HalfHalf(self):
        h = np.array(0x7f, dtype=np.uint8)
        self.assertEqual(fxSub(h, h), fxZero())

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxSub(h, h, nBits=i), fxZero(nBits=i))

    def test_QuarterHalf(self):
        q = np.array(0x3f, dtype=np.uint8)
        h = np.array(0x7f, dtype=np.uint8)
        t = np.array(0xbf, dtype=np.uint8) # 3/4
        self.assertEqual(fxSub(t, q), h)
        self.assertEqual(fxSub(t, h), q)
        self.assertEqual(fxSub(h, q), q)

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxSub(t, q, nBits=i), h)
            self.assertEqual(fxSub(t, h, nBits=i), q)
            self.assertEqual(fxSub(h, q, nBits=i), q)

# }}} class Test_fxSub

class Test_fxReflect(unittest.TestCase): # {{{

    def test_ClosestToZero(self):
        z = fxZero()
        o = fxOne() - 1 # Closest to one, but not equal.
        self.assertEqual(fxReflect(z), o)
        for i in range(2, 31+1):
            z = fxZero(nBits=i)
            o = fxOne(nBits=i) - 1
            self.assertEqual(fxReflect(z, nBits=i), o)

    def test_Zeros(self):
        shape = (3, 4)
        for i in range(2, 31+1):
            z = fxZeros(shape, nBits=i)
            o = fxOnes(shape, nBits=i) - 1 # Closest to one, but not equal.
            self.assertTrue(np.all(fxReflect(z, nBits=i) == o))

    def test_One(self):
        o = fxOne()
        self.assertEqual(fxReflect(o), np.array(0, dtype=np.uint8))
        for i in range(2, 31+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxReflect(o, nBits=i), 0)

    def test_OnesOnes(self):
        shape = (3, 4)
        for i in range(2, 31+1):
            o = fxOnes(shape, nBits=i)
            self.assertTrue(np.all(fxReflect(o, nBits=i) == np.zeros(shape)))

    def test_Quarter(self):
        h = np.array(0x7f, dtype=np.uint8)
        q = np.array(0x3f, dtype=np.uint8)
        t = np.array(0xbf, dtype=np.uint8) # 3/4
        self.assertEqual(fxAdd(h, q), t)
        self.assertEqual(fxReflect(q), t)

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxReflect(q, nBits=i), t)

    def test_Half(self):
        h = np.array(0x7f, dtype=np.uint8)
        self.assertEqual(fxReflect(h), h)

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxReflect(h, nBits=i), h)

# }}} class Test_fxReflect

class Test_fxMul(unittest.TestCase): # {{{

    def test_ZeroZero(self):
        z = fxZero()
        self.assertEqual(fxHadp(z, z), np.array(0, dtype=np.uint8))
        for i in range(2, 8+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxHadp(z, z, nBits=i), np.array(0, dtype=np.uint8))
        for i in range(9, 16+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxHadp(z, z, nBits=i), np.array(0, dtype=np.uint16))
        for i in range(17, 31+1):
            z = fxZero(nBits=i)
            self.assertEqual(fxHadp(z, z, nBits=i), np.array(0, dtype=np.uint32))

    def test_ZerosZeros(self):
        for i in range(2, 8+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxHadp(z, z, nBits=i) == np.zeros(shape, dtype=np.uint8)))
        for i in range(9, 16+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxHadp(z, z, nBits=i) == np.zeros(shape, dtype=np.uint16)))
        for i in range(17, 31+1):
            shape = (3, 4)
            z = fxZeros(shape, nBits=i)
            self.assertTrue(np.all(fxHadp(z, z, nBits=i) == np.zeros(shape, dtype=np.uint32)))

    def test_OneOne(self):
        o = fxOne()
        self.assertEqual(fxHadp(o, o), np.array(0xff, dtype=np.uint8))
        for i in range(2, 8+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxHadp(o, o, nBits=i), np.array(2**i-1, dtype=np.uint8))
        for i in range(9, 16+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxHadp(o, o, nBits=i), np.array(2**i-1, dtype=np.uint16))
        for i in range(17, 31+1):
            o = fxOne(nBits=i)
            self.assertEqual(fxHadp(o, o, nBits=i), np.array(2**i-1, dtype=np.uint32))

    def test_Large(self):
        i = 16
        o = (fxOne(nBits=i) - 10).astype(fxDtype(i))
        b = ((fxOne(nBits=i) >> 1) + 10).astype(fxDtype(i))
        fxHadp(o, b, nBits=i) # No assertion should raise.

    def test_OnesOnes(self):
        for i in range(2, 8+1):
            shape = (3, 4)
            o = fxOnes(shape, nBits=i)
            ob = np.broadcast_to(o.astype(np.uint8), shape)
            self.assertTrue(np.all(fxHadp(o, o, nBits=i) == ob))
        for i in range(9, 16+1):
            shape = (3, 4)
            o = fxOnes(shape, nBits=i)
            ob = np.broadcast_to(o.astype(np.uint16), shape)
            self.assertTrue(np.all(fxHadp(o, o, nBits=i) == ob))
        for i in range(17, 31+1):
            shape = (3, 4)
            o = fxOnes(shape, nBits=i)
            ob = np.broadcast_to(o.astype(np.uint32), shape)
            self.assertTrue(np.all(fxHadp(o, o, nBits=i) == ob))

    def test_QuarterQuarter(self):
        q = np.array(0x3f, dtype=np.uint8)
        s = np.array(0x0f, dtype=np.uint8) # 1/16
        self.assertEqual(fxHadp(q, q), s)

        for i in range(2, 31+1):
            #h = (fxOne(nBits=i) >> 1).astype(fxDtype(nBits=i))
            q = (fxOne(nBits=i) >> 2).astype(fxDtype(nBits=i))
            e = (fxOne(nBits=i) >> 3).astype(fxDtype(nBits=i))
            s = (fxOne(nBits=i) >> 4).astype(fxDtype(nBits=i))

            self.assertEqual(fxHadp(q, q, nBits=i), s)

    def test_HalfHalf(self):
        h = np.array(0x7f, dtype=np.uint8)
        q = np.array(0x3f, dtype=np.uint8)
        self.assertEqual(fxHadp(h, h), q)

        for i in range(2, 31+1):
            h = (fxOne(nBits=i) >> 1).astype(fxDtype(nBits=i))
            q = (fxOne(nBits=i) >> 2).astype(fxDtype(nBits=i))
            #e = (fxOne(nBits=i) >> 3).astype(fxDtype(nBits=i))
            #s = (fxOne(nBits=i) >> 4).astype(fxDtype(nBits=i))

            self.assertEqual(fxHadp(h, h, nBits=i), q)

    def test_QuarterHalf(self):
        q = np.array(0x3f, dtype=np.uint8)
        h = np.array(0x7f, dtype=np.uint8)
        e = np.array(0x1f, dtype=np.uint8) # 1/8
        self.assertEqual(fxHadp(q, h), e)
        self.assertEqual(fxHadp(h, q), e)

        for i in range(2, 31+1):
            h = (fxOne(nBits=i) >> 1).astype(fxDtype(nBits=i))
            q = (fxOne(nBits=i) >> 2).astype(fxDtype(nBits=i))
            e = (fxOne(nBits=i) >> 3).astype(fxDtype(nBits=i))
            #s = (fxOne(nBits=i) >> 4).astype(fxDtype(nBits=i))

            self.assertEqual(fxHadp(q, h, nBits=i), e)
            self.assertEqual(fxHadp(h, q, nBits=i), e)

# }}} class Test_fxMul

class Test_fxPow(unittest.TestCase): # {{{

    def test_ZeroNumber(self):
        for n in range(1, 10):
            z = fxZero()
            self.assertEqual(fxPow(z, n), np.array(0, dtype=np.uint8))
            for i in range(2, 31+1):
                z = fxZero(nBits=i)
                self.assertEqual(fxPow(z, n, nBits=i), z)

    def test_ZerosNumber(self):
        for n in range(1, 10):
            for i in range(2, 31+1):
                shape = (3, 4)
                z = fxZeros(shape, nBits=i)
                self.assertTrue(np.all(fxPow(z, n, nBits=i) == z))

    def test_ZeroExponent(self):
        self.assertEqual(fxPow(fxZero(), 0), fxOne())
        shape = (3, 4)
        self.assertTrue(np.all(fxPow(fxZeros(shape), 0) == fxOnes(shape)))

        for i in range(2, 31+1):
            self.assertEqual(fxPow(fxZero(nBits=i), 0, nBits=i), fxOne(nBits=i))
            shape = (3, 4)
            self.assertTrue(np.all(fxPow(fxZeros(shape, nBits=i), 0, nBits=i) == fxOnes(shape, nBits=i)))

    def test_HalfSquared(self):
        h = np.array(0x7f, dtype=np.uint8)
        q = np.array(0x3f, dtype=np.uint8)
        self.assertEqual(fxPow(h, 2), q)

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxPow(h, 2, nBits=i), q)

    def test_HalfCubed(self):
        h = np.array(0x7f, dtype=np.uint8)
        e = np.array(0x1f, dtype=np.uint8) # 1/8
        self.assertEqual(fxPow(h, 3), e)

        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            self.assertEqual(fxPow(h, 3, nBits=i), e)

# }}} class Test_fxPow

class Test_fxRatio(unittest.TestCase): # {{{

    def test_ClosestToZero(self):
        pairs = [
            (0, 2),
            (0, 4),
            (0, 10),
            (0, 2**35),
        ]
        for n,d in pairs:
            for i in range(2, 31+1):
                h,q,e,s,t = getFracs(i)
                self.assertGreater(fxToFloat(fxRatio(n, d, nBits=i), nBits=i), 0.0)
                # TODO: Could do with a better test here.

    def test_Halfs(self):
        pairs = [
            (1, 2),
            (2, 4),
            (5, 10),
            (2**35, 2**36),
        ]
        for n,d in pairs:
            for i in range(2, 31+1):
                h,q,e,s,t = getFracs(i)
                self.assertEqual(fxRatio(n, d, nBits=i), h)
                self.assertEqual(fxToFloat(fxRatio(n, d, nBits=i), nBits=i), 0.5)

    def test_Quarters(self):
        pairs = [
            (1, 4),
            (2, 8),
            (5, 20),
            (2**35, 2**37),
        ]
        for n,d in pairs:
            for i in range(2, 31+1):
                h,q,e,s,t = getFracs(i)
                self.assertEqual(fxRatio(n, d, nBits=i), q)
                self.assertEqual(fxToFloat(fxRatio(n, d, nBits=i), nBits=i), 0.25)

    def test_ThreeQuarters(self):
        pairs = [
            (3, 4),
            (6, 8),
            (15, 20),
            (2**35 + 2**36, 2**37),
        ]
        for n,d in pairs:
            for i in range(2, 31+1):
                h,q,e,s,t = getFracs(i)
                self.assertEqual(fxRatio(n, d, nBits=i), t)
                self.assertEqual(fxToFloat(fxRatio(n, d, nBits=i), nBits=i), 0.75)

# }}} class Test_fxRatio

class Test_fxArithMean(unittest.TestCase): # {{{

    def test_Basic0(self):
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([q, t], dtype=fxDtype(i))
            self.assertEqual(fxArithMean(X, nBits=i), h)

# }}} class Test_fxArithMean

class Test_fxNonNegDeriv(unittest.TestCase): # {{{

    def test_Basic0(self):
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([q, h, t, q, h, t], dtype=fxDtype(i))
            Xp = np.array([0, q, q, 0, q, q], dtype=fxDtype(i))
            self.assertTrue(np.all(fxNonNegDeriv(X, nBits=i) == Xp))

# }}} class Test_fxNonNegDeriv

class Test_fxExpectation(unittest.TestCase): # {{{

    def test_Basic0(self):
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([q, h, t, q, h, t, h, h], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxExpectation(W, X, nBits=i), h)

# }}} class Test_fxExpectation

class Test_fxConditional(unittest.TestCase): # {{{

    def test_Basic0(self):
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([q, h, t, q, h, t, h, h], dtype=fxDtype(i))
            Y = np.array([h, h, h, h, h, h, h, h], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxConditional(W, X, Y, nBits=i), h)

    def test_Breakdown(self):
        # Break down for E[Y] is very close to zero gives E[X|Y]=1,
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([q, h, t, q, h, t, h, h], dtype=fxDtype(i))
            Y = np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxConditional(W, X, Y, nBits=i), fxOne(nBits=i))

# }}} class Test_fxConditional

class Test_fxDependency(unittest.TestCase): # {{{

    def test_Basic0(self):
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([q, h, t, q, h, t, h, h], dtype=fxDtype(i))
            Y = np.array([h, h, h, h, h, h, h, h], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxDep(W, X, Y, nBits=i), fxZero(nBits=i))

    def test_Basic1(self):
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([fxZero(nBits=i), fxOne(nBits=i)], dtype=fxDtype(i))
            Y = np.array([fxZero(nBits=i), fxOne(nBits=i)], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxDep(W, X, Y, nBits=i), h)

    def test_Basic2(self):
        for i in range(4, 31+1): # NOTE: Breakdown at nBits<4
            h,q,e,s,t = getFracs(i)
            X = np.array([fxZero(nBits=i), fxOne(nBits=i),fxZero(nBits=i),fxZero(nBits=i)], dtype=fxDtype(i))
            Y = np.array([fxZero(nBits=i), fxOne(nBits=i),fxZero(nBits=i),fxZero(nBits=i)], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxDep(W, X, Y, nBits=i), t)

    def test_Breakdown(self):
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([q, h, t, q, h, t, h, h], dtype=fxDtype(i))
            Y = np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxDep(W, X, Y, nBits=i), fxZero(nBits=i))

    @unittest.skip("long runtime")
    def test_UpperLimit(self):
        # Randomized testing since full space of 2**nBits is not feasible.
        # NOTE: This test takes a lot longer than the others.
        for i in range(2, 31+1):
            for arrlen in [2, 4, 8, 16]:
                for _ in range(2000): # NOTE: Arbitrary large number.
                    W = fxOnes(arrlen, nBits=i)
                    dtype1 = fxDtype(nBits=i)
                    X = np.random.randint(0, 2**i, arrlen).astype(dtype1)
                    Y = np.random.randint(0, 2**i, arrlen).astype(dtype1)
                    try:
                        a = fxDep(W, X, Y, nBits=i)
                    except Exception as e:
                        print(i, i, dtype1, X, Y)
                        raise e
                    self.assertLessEqual(fxToFloat(a, nBits=i), (1 - 1/arrlen))

# }}} class Test_fxDependency

class Test_fxCovariance(unittest.TestCase): # {{{

    def test_Basic0(self):
        for i in range(3, 31+1): # Breakdown at nBits<3
            h,q,e,s,t = getFracs(i)
            X = np.array([q, h, t, q, h, t, h, h], dtype=fxDtype(i))
            Y = np.array([h, h, h, h, h, h, h, h], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxCov(W, X, Y, nBits=i), np.array(3, dtype=fxDtype(i)))

    def test_Basic1(self):
        for i in range(3, 31+1): # Breakdown at nBits<3
            h,q,e,s,t = getFracs(i)
            X = np.array([fxZero(nBits=i), fxOne(nBits=i)], dtype=fxDtype(i))
            Y = np.array([fxZero(nBits=i), fxOne(nBits=i)], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxCov(W, X, Y, nBits=i), fxOne(nBits=i))

    def test_Basic2(self):
        for i in range(5, 31+1): # NOTE: Breakdown at nBits<5
            h,q,e,s,t = getFracs(i)
            X = np.array([fxZero(nBits=i), fxOne(nBits=i),fxZero(nBits=i),fxZero(nBits=i)], dtype=fxDtype(i))
            Y = np.array([fxZero(nBits=i), fxOne(nBits=i),fxZero(nBits=i),fxZero(nBits=i)], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxCov(W, X, Y, nBits=i), t)

    def test_Breakdown(self):
        for i in range(2, 31+1):
            h,q,e,s,t = getFracs(i)
            X = np.array([q, h, t, q, h, t, h, h], dtype=fxDtype(i))
            Y = np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=fxDtype(i))
            W = fxOnes(X.shape, nBits=i)
            self.assertEqual(fxCov(W, X, Y, nBits=i), fxZero(nBits=i))

# }}} class Test_fxCovariance

