from dmppl.color import *
import unittest

class Test_colorspace1D(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.assertEqual((0xff, 0xff, 0xff), colorspace1D(0.0))
        self.assertEqual((0x7f, 0x7f, 0x7f), colorspace1D(0.5))
        self.assertEqual((0x00, 0x00, 0x00), colorspace1D(1.0))

# }}} class Test_colorspace1D

class Test_colorspace2D(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.assertEqual((0xff, 0xff, 0xff), colorspace2D(0.0, 0.0))
        self.assertEqual((0x7f, 0x7f, 0x7f), colorspace2D(0.5, 0.5))
        self.assertEqual((0x00, 0x00, 0x00), colorspace2D(1.0, 1.0))

# }}} class Test_colorspace2D

class Test_rgbStr(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.assertEqual("000000", rgbStr(0x00, 0x00, 0x00))
        self.assertEqual("123456", rgbStr(0x12, 0x34, 0x56))
        self.assertEqual("ffffff", rgbStr(0xff, 0xff, 0xff))

# }}} class Test_rgbStr

class Test_rgb1D(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.assertEqual("ffffff", rgb1D(0.0))
        self.assertEqual("7f7f7f", rgb1D(0.5))
        self.assertEqual("000000", rgb1D(1.0))

# }}} class Test_rgb1D

class Test_rgb2D(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.assertEqual("ffffff", rgb2D(0.0, 0.0))
        self.assertEqual("7f7f7f", rgb2D(0.5, 0.5))
        self.assertEqual("000000", rgb2D(1.0, 1.0))

# }}} class Test_rgb2D

class Test_identiconSprite(unittest.TestCase): # {{{

    def test_ZeroDefault(self):
        golden = [
            [True,  False, True,  False, True, ],
            [True,  True,  True,  True,  True, ],
            [True,  True,  False, True,  True, ],
            [True,  True,  False, True,  True, ],
            [False, False, True,  False, False,],
        ]
        result = identiconSprite(0)
        self.assertEqual(golden, result)

    def test_ZeroFour(self):
        golden = [
            [True,  False, False, True, ],
            [True,  False, False, True, ],
            [True,  True,  True,  True, ],
            [True,  True,  True,  True, ],
        ]
        result = identiconSprite(0, 4, 4)
        self.assertEqual(golden, result)

    def test_String(self):
        golden = [
            [True,  True,  True,  True,  True, ],
            [False, True,  False, True,  False,],
            [True,  True,  False, True,  True, ],
            [True,  True,  False, True,  True, ],
            [False, True,  False, True,  False,],
        ]
        result = identiconSprite("Hello World!")
        self.assertEqual(golden, result)

    def test_7x6(self):
        golden = [
            [True,  True,  False, False, True,  True, ],
            [False, True,  False, False, True,  False,],
            [True,  True,  False, False, True,  True, ],
            [True,  True,  True,  True,  True,  True, ],
            [False, False, False, False, False, False,],
            [True,  False, False, False, False, True, ],
            [True,  False, False, False, False, True,],
        ]
        result = identiconSprite("Hello World!", 7, 6)
        self.assertEqual(golden, result)

    def test_4x3(self):
        golden = [
            [True,  False, True, ],
            [False, True,  False,],
            [True,  True,  True, ],
            [True,  True,  True, ],
        ]
        result = identiconSprite("Hello World!", 4, 3)
        self.assertEqual(golden, result)

    def test_Int(self):
        golden = [
            [False, True,  True,  True,  False,],
            [False, False, True,  False, False,],
            [False, False, False, False, False,],
            [False, False, True,  False, False,],
            [False, False, False, False, False,],
        ]
        resultInt = identiconSprite(123)
        resultStr = identiconSprite("123")
        self.assertEqual(golden, resultInt)
        self.assertEqual(golden, resultStr)

# }}} class Test_identiconSprite

class Test_asciiart2dBool(unittest.TestCase): # {{{

    def test_Basic0(self):
        a = [
            [False, True,  True,  True,  False,],
            [False, False, True,  False, False,],
            [False, False, False, False, False,],
            [False, False, True,  False, False,],
            [False, False, False, False, False,],
        ]
        result = asciiart2dBool(a)
        golden = '\n'.join([" ### ",
                            "  #  ",
                            "     ",
                            "  #  ",
                            "     "])
        self.assertEqual(golden, result)

    def test_AltChars(self):
        a = [
            [False, True,  True,  True,  False,],
            [False, False, True,  False, False,],
            [False, False, False, False, False,],
            [False, False, True,  False, False,],
            [False, False, False, False, False,],
        ]
        result = asciiart2dBool(a, 'Y', 'n')
        golden = '\n'.join(["nYYYn",
                            "nnYnn",
                            "nnnnn",
                            "nnYnn",
                            "nnnnn"])
        self.assertEqual(golden, result)

# }}} class Test_asciiart2dBool

