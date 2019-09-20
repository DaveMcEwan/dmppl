from dmppl.yaml import *
import os
import gzip
import tempfile
import shutil
import unittest

class Test_saveYml(unittest.TestCase): # {{{

    def setUp(self):

        self.myobj0 = {
            "foo":      True,
            "bar":      False,
            "lorem":    123,
            "ipsum":    "abc",
            "decorum":  None,
            "est":      456.789,
            "Hi":       ["hello", "world"],
        }

        self.myobj1 = [
            True,
            False,
            123,
            "abc",
            None,
            456.789,
            ["hello", "world"],
        ]

        self.tstDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        fnameo = os.path.join(self.tstDir, "test_Basic0.yml")
        result = saveYml(self.myobj0, fnameo)
        self.assertEqual(result, None)

        with open(fnameo, 'r') as fd:
            rdbk = yaml.safe_load(fd)

        self.assertDictEqual(self.myobj0, rdbk)

    def test_Basic1(self):
        fnameo = os.path.join(self.tstDir, "test_Basic1")
        result = saveYml(self.myobj0, fnameo)
        self.assertEqual(result, None)

        with open(fnameo + ".yml", 'r') as fd:
            rdbk = yaml.safe_load(fd)

        self.assertDictEqual(self.myobj0, rdbk)

    def test_Basic2(self):
        fnameo = os.path.join(self.tstDir, "test_Basic2")
        result = saveYml(self.myobj1, fnameo)
        self.assertEqual(result, None)

        with open(fnameo + ".yml", 'r') as fd:
            rdbk = yaml.safe_load(fd)

        self.assertListEqual(self.myobj1, rdbk)

    def test_Compressed0(self):
        fnameo = os.path.join(self.tstDir, "test_Compressed0.yml.gz")
        result = saveYml(self.myobj0, fnameo)
        self.assertEqual(result, None)

        with gzip.GzipFile(fnameo, 'rb') as fd:
            rdbk = yaml.safe_load(fd)

        self.assertDictEqual(self.myobj0, rdbk)

# }}} class Test_saveYml

class Test_loadYml(unittest.TestCase): # {{{

    def setUp(self):

        self.tstDir = tempfile.mkdtemp()

        self.myobj0 = {
            "foo":      True,
            "bar":      False,
            "lorem":    123,
            "ipsum":    "abc",
            "decorum":  None,
            "est":      456.789,
            "Hi":       ["hello", "world"],
        }

        self.myobj1 = [
            True,
            False,
            123,
            "abc",
            None,
            456.789,
            ["hello", "world"],
        ]

        fname0 = os.path.join(self.tstDir, "myobj0.yml")
        fname1 = os.path.join(self.tstDir, "myobj1.yml")
        with open(fname0, 'w') as fd:
            yaml.safe_dump(self.myobj0, fd)

        with open(fname1, 'w') as fd:
            yaml.safe_dump(self.myobj1, fd)

        with gzip.GzipFile(fname0 + ".gz", 'wb') as fd:
            fd.write(yaml.safe_dump(self.myobj0).encode("utf-8"))

        with gzip.GzipFile(fname1 + ".gz", 'wb') as fd:
            fd.write(yaml.safe_dump(self.myobj1).encode("utf-8"))

        fromstr0 = '''
# comment
foo:        True
# comment

"lorem":    123
decorum: ~
Hi:
    - hello
    -  world
        '''

        fname2 = os.path.join(self.tstDir, "fromstr0.yml")
        with open(fname2, 'w') as fd:
            fd.write(fromstr0)

        with gzip.GzipFile(fname2 + ".gz", 'wb') as fd:
            fd.write(fromstr0.encode("utf-8"))

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        fname = os.path.join(self.tstDir, "myobj0")
        rdbk = loadYml(fname)
        self.assertDictEqual(self.myobj0, rdbk)

    def test_Basic1(self):
        fname = os.path.join(self.tstDir, "myobj1")
        rdbk = loadYml(fname)
        self.assertListEqual(self.myobj1, rdbk)

    def test_Basic2(self):
        fname = os.path.join(self.tstDir, "myobj0.yml")
        rdbk = loadYml(fname)
        self.assertDictEqual(self.myobj0, rdbk)

    def test_Compressed0(self):
        fname = os.path.join(self.tstDir, "myobj0.yml.gz")
        rdbk = loadYml(fname)
        self.assertDictEqual(self.myobj0, rdbk)

    def test_Marked0(self):
        fname = os.path.join(self.tstDir, "fromstr0.yml")
        rdbk = loadYml(fname, marked=True)
        for k,v in rdbk.items():

            ksl = k.start_mark.line
            ksc = k.start_mark.column
            vsl = v.start_mark.line
            vsc = v.start_mark.column
            kel = k.end_mark.line
            kec = k.end_mark.column
            vel = v.end_mark.line
            vec = v.end_mark.column

            if "foo" == k:
                self.assertEqual((ksl, ksc), (2, 0))
                self.assertEqual((kel, kec), (2, 3))
                self.assertEqual(v, True)
                self.assertEqual((vsl, vsc), (2, 12))
                self.assertEqual((vel, vec), (2, 16))

            elif "lorem" == k:
                self.assertEqual((ksl, ksc), (5, 0))
                self.assertEqual((kel, kec), (5, 7))
                self.assertEqual(v, 123)
                self.assertEqual((vsl, vsc), (5, 12))
                self.assertEqual((vel, vec), (5, 15))

            elif "decorum" == k:
                self.assertEqual((ksl, ksc), (6, 0))
                self.assertEqual((kel, kec), (6, 7))
                self.assertIsInstance(v, YamlConstructor.NoneNode)
                self.assertEqual((vsl, vsc), (6, 9))
                self.assertEqual((vel, vec), (6, 10))

            elif "Hi" == k:
                self.assertEqual((ksl, ksc), (7, 0))
                self.assertEqual((kel, kec), (7, 2))
                self.assertIsInstance(v, list)
                for i, vi in enumerate(v):
                    visl = vi.start_mark.line
                    visc = vi.start_mark.column
                    viel = vi.end_mark.line
                    viec = vi.end_mark.column

                    if 0 == i:
                        self.assertEqual(vi, "hello")
                        self.assertEqual((visl, visc), (8, 6))
                        self.assertEqual((viel, viec), (8, 11))
                    elif 1 == i:
                        self.assertEqual(vi, "world")
                        self.assertEqual((visl, visc), (9, 7))
                        self.assertEqual((viel, viec), (9, 12))

                self.assertEqual((vsl, vsc), (8, 4))
                self.assertEqual((vel, vec), (10, 8))

    def test_MarkedCompressed(self):
        fname = os.path.join(self.tstDir, "fromstr0.yml.gz")
        rdbk = loadYml(fname, marked=True)
        for k,v in rdbk.items():

            ksl = k.start_mark.line
            ksc = k.start_mark.column
            vsl = v.start_mark.line
            vsc = v.start_mark.column
            kel = k.end_mark.line
            kec = k.end_mark.column
            vel = v.end_mark.line
            vec = v.end_mark.column

            if "foo" == k:
                self.assertEqual((ksl, ksc), (2, 0))
                self.assertEqual((kel, kec), (2, 3))
                self.assertEqual(v, True)
                self.assertEqual((vsl, vsc), (2, 12))
                self.assertEqual((vel, vec), (2, 16))
        # NOTE: Cutting short marked+compressed as if any mark fails they all
        # should so this makes the test a bit more maintainable.

# }}} class Test_loadYml

