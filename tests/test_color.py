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

