from dmppl.toml import *
import toml
import os
import sys
import gzip
import tempfile
import shutil
import unittest

class Test_saveToml(unittest.TestCase): # {{{

    def setUp(self):

        # Check against golden for 3.6, 3.7, but for other versions just check
        # the same thing is generated twice using the same seed.
        self.orderedDict = sys.version_info[:2] in [(3, 6), (3, 7)]

        self.obj0 = {
            u"foo":      True,
            u"bar":      False,
            u"lorem":    123,
            u"ipsum":    u"abc",
            u"est":      456.789,
            u"Hi":       [u"hello", u"world"],
        }

        self.str0 = \
'''\
foo = true
bar = false
lorem = 123
ipsum = "abc"
est = 456.789
Hi = [ "hello", "world",]
'''

        self.tstDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        fnameo = os.path.join(self.tstDir, "test_Basic0.toml")
        result = saveToml(self.obj0, fnameo)
        self.assertEqual(result, None)

        rdbk = toml.load(fnameo)
        self.assertDictEqual(self.obj0, rdbk)

        if self.orderedDict:
            with open(fnameo, 'r') as fd:
                rdstr = fd.read()
            self.assertEqual(self.str0, rdstr)


    def test_Basic1(self):
        fnameo = os.path.join(self.tstDir, "test_Basic1")
        result = saveToml(self.obj0, fnameo)
        self.assertEqual(result, None)

        with open(fnameo + ".toml", 'r') as fd:
            rdbk = toml.load(fd)

        self.assertDictEqual(self.obj0, rdbk)

    def test_Compressed0(self):
        fnameo = os.path.join(self.tstDir, "test_Compressed0.toml.gz")
        result = saveToml(self.obj0, fnameo)
        self.assertEqual(result, None)

        with gzip.GzipFile(fnameo, 'rb') as fd:
            rdbk = toml.loads(fd.read().decode())

        self.assertDictEqual(self.obj0, rdbk)

# }}} class Test_saveToml

class Test_loadToml(unittest.TestCase): # {{{

    def setUp(self):

        self.tstDir = tempfile.mkdtemp()

        self.obj0 = {
            "foo":      True,
            "bar":      False,
            "lorem":    123,
            "ipsum":    "abc",
            "est":      456.789,
            "Hi":       ["hello", "world"],
        }

        fname0 = os.path.join(self.tstDir, "obj0.toml")
        with open(fname0, 'w') as fd:
            toml.dump(self.obj0, fd)

        with gzip.GzipFile(fname0 + ".gz", 'wb') as fd:
            fd.write(toml.dumps(self.obj0).encode("utf-8"))

        self.str0 = '''
# comment
foo =true
# comment

"lorem"=    123
Hi = [
    "hello",
   "world"
    ]
        '''

        fname2 = os.path.join(self.tstDir, "str0.toml")
        with open(fname2, 'w') as fd:
            fd.write(self.str0)

        with gzip.GzipFile(fname2 + ".gz", 'wb') as fd:
            fd.write(self.str0.encode("utf-8"))

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        fname = os.path.join(self.tstDir, "obj0")
        rdbk = loadToml(fname)
        self.assertDictEqual(self.obj0, rdbk)

    def test_Basic2(self):
        fname = os.path.join(self.tstDir, "obj0.toml")
        rdbk = loadToml(fname)
        self.assertDictEqual(self.obj0, rdbk)

    def test_Compressed0(self):
        fname = os.path.join(self.tstDir, "obj0.toml.gz")
        rdbk = loadToml(fname)
        self.assertDictEqual(self.obj0, rdbk)

# }}} class Test_loadToml

