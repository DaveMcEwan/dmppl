
import sys

if sys.version_info[0] > 2:
    long = int

class Xoroshiro128plus: # {{{
    '''Port of C code from http://xoshiro.di.unimi.it/xoroshiro128plus.c

    From the original header:
    This is xoroshiro128+ 1.0, our best and fastest small-state generator
    for floating-point numbers. We suggest to use its upper bits for
    floating-point generation, as it is slightly faster than
    xoroshiro128**. It passes all tests we are aware of except for the four
    lower bits, which might fail linearity tests (and just those), so if
    low linear complexity is not considered an issue (as it is usually the
    case) it can be used to generate 64-bit outputs, too; moreover, this
    generator has a very mild Hamming-weight dependency making our test
    (http://prng.di.unimi.it/hwd.php) fail after 5 TB of output; we believe
    this slight bias cannot affect any application. If you are concerned,
    use xoroshiro128** or xoshiro256+.

    We suggest to use a sign test to extract a random Boolean value, and
    right shifts to extract subsets of bits.

    The state must be seeded so that it is not everywhere zero. If you have
    a 64-bit seed, we suggest to seed a splitmix64 generator and use its
    output to fill _s.

    NOTE: the parameters (a=24, b=16, b=37) of this version give slightly
    better results in our test than the 2016 version (a=55, b=14, c=36).


    Test against C implementation with something like this:

        prng = Xoroshiro128plus()
        with open("xoroshiro128plus.tst", 'w') as fd:
            for i in range(100):
                r = prng.next()
                print("%d 0x%x %d" % (i, r, r), file=fd)

            for j in range(10):
                prng.jump()
                for i in range(10):
                    r = prng.next()
                    print("%d %d 0x%x %d" % (j, i, r, r), file=fd)

            for j in range(10):
                prng.long_jump()
                for i in range(10):
                    r = prng.next()
                    print("%d %d 0x%x %d" % (j, i, r, r), file=fd)
    '''
    _mask64 = 2**64 - 1

    # PRNG parameters
    #_a,_b,_c = 55,14,36 # 2016
    _a,_b,_c = 24,16,37 # 2018

    def __init__(self): # {{{
        assert isinstance(self._a, int) and self._a < 64
        assert isinstance(self._b, int) and self._b < 64
        assert isinstance(self._c, int) and self._c < 64
        assert isinstance(self._mask64, (int,long))

        self._s = [0, 0]
        self.seed()
    # }}} def __init__

    def seed(self, s0=3141592654, s1=1618033989): # {{{
        '''Place seed values in 128b state as 2 64b integers.
        Default values are just the first 10 digits of pi and the golden ratio.
        '''
        assert isinstance(s0, (int,long))
        assert isinstance(s1, (int,long))

        self._s[0] = s0
        self._s[1] = s1
    # }}} def seed

    def _rotl(self, x, k): # {{{
        '''Rotate uint64_t x left by k places
        '''
        assert isinstance(x, (int,long)), type(x)
        assert isinstance(k, int)
        assert 0 <= k < 64
        assert k in [self._a, self._b, self._c]

        return ( (x << k) | (x >> (64 - k)) ) & self._mask64
    # }}} def _rotl

    def next(self): # {{{
        '''Generate next number in sequence (ctypes.c_uint64).
        '''
        s0 = self._s[0]
        s1 = self._s[1]

        result = (s0 + s1) & self._mask64

        s1_tmp = s0 ^ s1
        assert isinstance(s1_tmp, (int,long))

        new_s0 = self._rotl(s0, self._a) ^ \
                 s1_tmp ^ \
                 ((s1_tmp << self._b) & self._mask64)
        new_s1 = self._rotl(s1_tmp, self._c)
        self.seed(new_s0, new_s1)

        assert isinstance(result, (int,long))
        return result
    # }}} def next

    def jump(self): # {{{
        '''This is the jump function for the generator.
           It is equivalent to 2**64 calls to next();
           It can be used to generate 2**64 non-overlapping subsequences for
           parallel computations.
        '''
        JUMP = [0xdf900294d8f554a5, 0x170865df4b3201fc]

        s0 = 0
        s1 = 0
        for i in range(2):
            for b in range(64):
                if (JUMP[i] & (1 << b)) != 0:
                    s0 ^= self._s[0]
                    s1 ^= self._s[1]
                _ = self.next()

        self.seed(s0, s1)
    # }}} def jump

    def long_jump(self): # {{{
        '''This is the long-jump function for the generator.
           It is equivalent to 2**96 calls to next();
           It can be used to generate 2**32 starting points, from each of which
           jump() will generate 2**32 non-overlapping subsequences for parallel
           distributed computations.
        '''
        LONG_JUMP = [0xd2a98b26625eee7b, 0xdddf9b1090aa7ac1]

        s0 = 0
        s1 = 0
        for i in range(2):
            for b in range(64):
                if (LONG_JUMP[i] & (1 << b)) != 0:
                    s0 ^= self._s[0]
                    s1 ^= self._s[1]
                _ = self.next()

        self.seed(s0, s1)
    # }}} def long_jump

# }}} class Xoroshiro128plus

if __name__ == "__main__":
    assert False, "Not a standalone script."
