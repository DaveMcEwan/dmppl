from dmppl.prng import *
import os
import unittest

class Test_Xoroshiro128plus(unittest.TestCase): # {{{

    def test_Basic0(self):
        prng = Xoroshiro128plus()

        result = []
        for i in range(100):
            r = prng.next()
            result.append("%d 0x%x %d" % (i, r, r))

        for j in range(10):
            prng.jump()
            for i in range(10):
                r = prng.next()
                result.append("%d %d 0x%x %d" % (j, i, r, r))

        for j in range(10):
            prng.long_jump()
            for i in range(10):
                r = prng.next()
                result.append("%d %d 0x%x %d" % (j, i, r, r))

        fname = "golden_Xoroshiro128plus_Basic0"
        with open(os.path.join(os.path.dirname(__file__), fname), 'r') as fd:
            golden = [line.strip() for line in fd]

        self.assertListEqual(result, golden)

# }}} class Test_Xoroshiro128plus

