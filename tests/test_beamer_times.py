from dmppl.scripts.beamer_times import entryPoint
from dmppl.base import rdTxt
from dmppl.test import runEntryPoint
import os
import tempfile
import shutil
import sys
import unittest

class Test_BeamerTimes(unittest.TestCase): # {{{

    def setUp(self):

        self.tstDir = tempfile.mkdtemp()

        self.tex0 = r'''
ignore
these lines
1m23s 23m45s also ignored
including lines with the word "frametitle"
\frametitle{Or missing time notation}
\frametitle{SingleWordA} % 1m23s
\frametitle{SingleWordB} More TeX \commands here. % foo bar 1m23s
\frametitle{SingleWordC} % A comment in here 1m23s
\frametitle{SingleWordD} more TeX \commands here % and a comment 1m23s
Some
lines between
the frame titles
\frametitle{A Multi Words} foo bar % foo bar 1m23s
\frametitle{B Just use the last time} % 1m23s 23m45s
\frametitle{C Allow X or x to denote 0 time.} foo % XmXs
\frametitle{D time counter continues afterwards} % 1m23s
\frametitle{E time not in a comment (invalid TeX)} 1m23s
\frametitle{F Some} 0m5s
\frametitle{G weird but allowed time notations} 12m345s
asdf
'''
        self.fnamei0 = os.path.join(self.tstDir, "tst0.tex")
        with open(self.fnamei0, 'w') as fd:
            fd.write(self.tex0)

        self.goldenOut0 = '''\
#  Slide  Finish  Title
1   1m23s   1m23s SingleWordA
2   1m23s   2m46s SingleWordB
3   1m23s   4m09s SingleWordC
4   1m23s   5m32s SingleWordD
5   1m23s   6m55s A Multi Words
6  23m45s  30m40s B Just use the last time
7   0m00s  30m40s C Allow X or x to denote 0 time.
8   1m23s  32m03s D time counter continues afterwards
9   1m23s  33m26s E time not in a comment (invalid TeX)
10  0m05s  33m31s F Some
11 17m45s  51m16s G weird but allowed time notations
'''

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        cmd = "beamer-times %s" % (self.fnamei0)
        stdout, stderr = runEntryPoint(cmd, entryPoint)
        self.assertEqual(stderr, "")
        self.assertEqual(self.goldenOut0, stdout)

    def test_FileIO(self):
        fnameo = self.fnamei0 + ".rpt"
        cmd = "beamer-times %s -o %s" % (self.fnamei0, fnameo)
        stdout, stderr = runEntryPoint(cmd, entryPoint, stdinput="fubar")
        self.assertEqual(stderr, "")
        resultTxt = rdTxt(os.path.join(self.tstDir, fnameo))
        self.assertEqual(self.goldenOut0, resultTxt)

    def test_StdIO(self):
        cmd = "beamer-times"
        stdout, stderr = runEntryPoint(cmd, entryPoint, stdinput=self.tex0)
        self.assertEqual(stderr, "")
        self.assertEqual(self.goldenOut0, stdout)

# }}} class Test_BeamerTimes
