from dmppl.scripts.parvec import entryPoint
from dmppl.base import rdTxt
from dmppl.test import runEntryPoint
import os
import tempfile
import shutil
import sys
import unittest

class Test_Parvec(unittest.TestCase): # {{{

    def setUp(self):

        # Different PRNGs between CPython versions.
        # Check against golden for 3.5, 3.6, 3.7, but for other versions just check
        # the same thing is generated twice using the same seed.
        self.knownPrng = sys.version_info[:2] in [(3, 5), (3, 6), (3, 7)]

        self.tstDir = tempfile.mkdtemp()

        self.yml0 = '''\
PP_CPU$_$:
    - [0, 1, 2]
    - ["LSU", "ALU"]
    - ["SS", "TT", "FF"]
PB_L$CACHE_EVICT:
    - [1, 2]
    - {pre-name: foo, post-value: bar}
    - ["PERIODIC", "ROUNDROBIN"]
PI_FIFO$_LAYOUT:
    - 0..10..2
    - ["LINE", "CIRC"]
PL_COUNTER$_THRESH$:
    - pre-value: "('d"
      post-value: ");"
      pre-name: "#blah "
    - 0..2
    - 0..5
    - 100..333..5
'''
        self.fnamei0 = os.path.join(self.tstDir, "tst0.yml")
        with open(self.fnamei0, 'w') as fd:
            fd.write(self.yml0)

        self.goldenOut0 = '''\
// seed: 0
fooPB_L1CACHE_EVICT ROUNDROBINbar
fooPB_L2CACHE_EVICT ROUNDROBINbar
`define PI_FIFO0_LAYOUT CIRC
`define PI_FIFO2_LAYOUT LINE
`define PI_FIFO4_LAYOUT LINE
`define PI_FIFO6_LAYOUT LINE
`define PI_FIFO8_LAYOUT LINE
#blah PL_COUNTER0_THRESH0 ('d250);
#blah PL_COUNTER0_THRESH1 ('d210);
#blah PL_COUNTER0_THRESH2 ('d285);
#blah PL_COUNTER0_THRESH3 ('d165);
#blah PL_COUNTER0_THRESH4 ('d260);
#blah PL_COUNTER1_THRESH0 ('d140);
#blah PL_COUNTER1_THRESH1 ('d190);
#blah PL_COUNTER1_THRESH2 ('d140);
#blah PL_COUNTER1_THRESH3 ('d130);
#blah PL_COUNTER1_THRESH4 ('d295);
`define PP_CPU0_ALU SS
`define PP_CPU0_LSU TT
`define PP_CPU1_ALU TT
`define PP_CPU1_LSU TT
`define PP_CPU2_ALU FF
`define PP_CPU2_LSU SS
'''

        self.yml1 = '''\
WEALTH_$:
    - [Alice, Bob]
    - 0..1000
GOODNESS_$_$:
    - [Alice, Bob, Charlie, Eve]
    - [Black, White, Gray]
    - [lovely, evil]
'''
        self.fnamei1 = os.path.join(self.tstDir, "tst1.yml")
        with open(self.fnamei1, 'w') as fd:
            fd.write(self.yml1)

        self.goldenOut1 = '''\
// seed: 123
`define GOODNESS_Alice_Black evil
`define GOODNESS_Alice_Gray lovely
`define GOODNESS_Alice_White evil
`define GOODNESS_Bob_Black lovely
`define GOODNESS_Bob_Gray lovely
`define GOODNESS_Bob_White evil
`define GOODNESS_Charlie_Black evil
`define GOODNESS_Charlie_Gray lovely
`define GOODNESS_Charlie_White lovely
`define GOODNESS_Eve_Black lovely
`define GOODNESS_Eve_Gray evil
`define GOODNESS_Eve_White evil
`define WEALTH_Alice 138
`define WEALTH_Bob 345
'''

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        self.maxDiff = None
        if self.knownPrng:
            cmd = "parvec --seed 123 %s" % (self.fnamei1)
            stdout, stderr = runEntryPoint(cmd, entryPoint)
            self.assertEqual(stderr, "")
            self.assertEqual(self.goldenOut1, stdout)
        else:
            pass

    def test_StdIO(self):
        self.maxDiff = None
        if self.knownPrng:
            cmd = "parvec --seed 0"
            stdout, stderr = runEntryPoint(cmd, entryPoint, stdinput=self.yml0)
            self.assertEqual(stderr, "")
            self.assertEqual(self.goldenOut0, stdout)
        else:
            pass

    def test_Features0(self):
        self.maxDiff = None
        if self.knownPrng:
            fnameo0 = self.fnamei0 + ".out"
            cmd = "parvec --seed 0 %s -o %s" % (self.fnamei0, fnameo0)
            stdout, stderr = runEntryPoint(cmd, entryPoint)
            self.assertEqual(stderr, "")
            self.assertEqual(stdout, "")
            resultTxt = rdTxt(os.path.join(self.tstDir, fnameo0))
            self.assertEqual(self.goldenOut0, resultTxt)
        else:
            fnameo0_A = self.fnamei0 + ".outA"
            fnameo0_B = self.fnamei0 + ".outB"
            cmdA = "parvec --seed 0 %s -o %s" % (self.fnamei0, fnameo0_A)
            cmdB = "parvec --seed 0 %s -o %s" % (self.fnamei0, fnameo0_B)
            stdoutA, stderrA = runEntryPoint(cmdA, entryPoint)
            #stdoutA, stderrA = runEntryPoint(cmdA, entryPoint, redirect=False)
            self.assertEqual(stderrA, "")
            self.assertEqual(stdoutA, "")
            stdoutB, stderrB = runEntryPoint(cmdB, entryPoint)
            #stdoutB, stderrB = runEntryPoint(cmdB, entryPoint, redirect=False)
            self.assertEqual(stderrB, "")
            self.assertEqual(stdoutB, "")
            resultTxtA = rdTxt(os.path.join(self.tstDir, fnameo0_A))
            resultTxtB = rdTxt(os.path.join(self.tstDir, fnameo0_B))
            self.assertEqual(resultTxtA, resultTxtB)

# }}} class Test_Parvec
