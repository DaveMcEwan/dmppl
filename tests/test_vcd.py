from dmppl.base import rdTxt
from dmppl.vcd import *
from dmppl.test import *
import os
import tempfile
import shutil
import types
import unittest

try:
    from io import StringIO
except: # Python <3.4
    from StringIO import StringIO

class Test_VcdReader(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        # NOTE: Forgiving parser accepts things obviously outside the spec such
        # as events with non-zero widths.
        self.vcd0 = u'''\
$version Handwritten basic0 $end
$date Monday 12th August $end
$comment hello world $end
$timescale 1ns $end
$scope module TOP $end
    $var wire 1 C clk $end
    $var wire 1 R rst $end
    $scope module myblock $end
        $var wire 1 C i_clk $end
        $var wire 1 R i_rst $end
        $var reg 8 Q counter [7:0] $end
    $upscope $end
    $var event  0   e0      zeroEvent   $end
    $var event  1   e1      oneEvent    $end
    $var event  2   e2      twoEvent    $end
    $var wire   1   w1      singleWire  $end
    $var wire   2   w2      doubleWire  $end
    $var wire   200 w200    hugeWire    $end
    $var reg    1   r1      singleReg   $end
    $var reg    2   r2      doubleReg   $end
    $var reg    200 r200    hugeReg     $end
    $var bit    1   b1      singleBit   $end
    $var bit    2   b2      doubleBit   $end
    $var bit    200 b200    hugeBit     $end
    $var logic  1   l1      singleLogic $end
    $var logic  2   l2      doubleLogic $end
    $var logic  200 l200    hugeLogic   $end
$upscope $end
$enddefinitions $end
#0
0C
0R
b00000000 Q

#1
1R

#2
1C
b00000001 Q

#3
0C

#4
1C
b00000010 Q
'''
        with open(os.path.join(self.tstDir, "tst0.vcd"), 'w') as fd:
            fd.write(self.vcd0)

        self.missingEnddefs = '''\
$version Handwritten missing end-defs $end
$timescale 1ns $end
'''
        with open(os.path.join(self.tstDir, "missingEnddefs.vcd"), 'w') as fd:
            fd.write(self.missingEnddefs)

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        fname = os.path.join(self.tstDir, "tst0.vcd")
        with VcdReader(fname) as vr:
            self.assertEqual(vr.vcdVersion, "Handwritten basic0")
            self.assertEqual(vr.vcdDate, "Monday 12th August")
            self.assertEqual(vr.vcdComment, "hello world")
            self.assertTupleEqual(vr.vcdTimescale, ('1', "ns"))

            goldenVarIdsUnique = [
                'C', 'Q', 'R',
                "b1", "b2", "b200",
                "e0", "e1", "e2",
                "l1", "l2", "l200",
                "r1", "r2", "r200",
                "w1", "w2", "w200",
            ]
            self.assertSequenceEqual(vr.varIdsUnique, goldenVarIdsUnique)

            goldenVarIds = ['C', 'C', 'Q', 'R', 'R'] + goldenVarIdsUnique[3:]
            self.assertSequenceEqual(vr.varIds, goldenVarIds)

            goldenVarTypes = [
                "wire", "wire", "reg", "wire", "wire", # clk, i_clk, counter rst, i_rst
                #
                "bit", "bit", "bit",
                "event", "event", "event",
                "logic", "logic", "logic",
                "reg", "reg", "reg",
                "wire", "wire", "wire",
            ]
            self.assertSequenceEqual(vr.varTypes, goldenVarTypes)

            goldenVarSizes = [
                1, 1, 8, 1, 1, # clk, i_clk, counter rst, i_rst
                #
                1, 2, 200,
                0, 1, 2,
                1, 2, 200,
                1, 2, 200,
                1, 2, 200,
            ]
            self.assertSequenceEqual(vr.varSizes, goldenVarSizes)

            goldenVarNames = [
                "module:TOP.clk",
                "module:TOP.myblock.i_clk",
                "module:TOP.myblock.counter[7:0]",
                "module:TOP.rst",
                "module:TOP.myblock.i_rst",
                #
                "module:TOP.singleBit", "module:TOP.doubleBit", "module:TOP.hugeBit",
                "module:TOP.zeroEvent", "module:TOP.oneEvent", "module:TOP.twoEvent",
                "module:TOP.singleLogic", "module:TOP.doubleLogic", "module:TOP.hugeLogic",
                "module:TOP.singleReg", "module:TOP.doubleReg", "module:TOP.hugeReg",
                "module:TOP.singleWire", "module:TOP.doubleWire", "module:TOP.hugeWire",
            ]
            self.assertSequenceEqual(vr.varNames, goldenVarNames)

            resultTimechunks = list(vr.timechunks)

            goldenTimechunks = [
                (0, ['C', 'R', 'Q'], ['0', '0', "00000000"]),
                (1, ['R'], ['1']),
                (2, ['C', 'Q'], ['1', "00000001"]),
                (3, ['C'], ['0']),
                (4, ['C', 'Q'], ['1', "00000010"]),
            ]
            self.assertSequenceEqual(resultTimechunks, goldenTimechunks)

    def test_Stdin(self):
        sysStdin = sys.stdin
        sys.stdin = StringIO(self.vcd0)
        with VcdReader() as vr:
            self.assertEqual(vr.vcdVersion, "Handwritten basic0")
            self.assertEqual(vr.vcdDate, "Monday 12th August")
            self.assertEqual(vr.vcdComment, "hello world")
            self.assertTupleEqual(vr.vcdTimescale, ('1', "ns"))
        sys.stdin = sysStdin

    def test_MissingEnddefs(self):
        fname = os.path.join(self.tstDir, "missingEnddefs.vcd")
        v = VcdReader(fname)
        self.assertRaises(StopIteration, v.__enter__)

# }}} class Test_VcdReader

class Test_VcdWriter(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.golden0 = '''\
$comment hello world $end
$date Monday 12th August $end
$version dmppl.vcd.VcdWriter $end
$timescale 10 us $end
$scope module TOP $end
$var wire 1 ! clk  $end
$var event 1 ( happening0  $end
$var event 1 ) happening1  $end
$scope module myblock $end
$var reg 8 # counter [7:0] $end
$var real 16 % floating16b [15:0] $end
$var real 32 & floating32b [31:0] $end
$var real 64 ' floating64b [63:0] $end
$var real 8 $ floating8b [7:0] $end
$var wire 1 ! i_clk  $end
$var wire 1 " i_rst  $end
$upscope $end
$var wire 1 " rst  $end
$upscope $end
$enddefinitions $end

#0
0!
0"
b00000000 #

#1
1"
0(
0)

#2
1!
b00000001 #

#3
0!
r0.500000 $

#4
1!
b00000010 #
'''
        with open(os.path.join(self.tstDir, "golden0.vcd"), 'w') as fd:
            fd.write(self.golden0)
        with open(os.path.join(self.tstDir, "golden1.vcd"), 'w') as fd:
            fd.write(self.golden0.replace("\n\n", '\n'))

        # NOTE: Order or vars determines their varIds, but not the order
        # they are written into the header.
        self.varlist0 = [
            ("TOP.clk",                 1,  "wire"),
            ("module:TOP.badtype:rst",  1,  "wire"),
            ("TOP.myblock.counter",     8,  "reg"),
            ("TOP.myblock.floating8b",  8,  "real"),
            ("TOP.myblock.floating16b", 16, "real"),
            ("TOP.myblock.floating32b", 32, "real"),
            ("TOP.myblock.floating64b", 64, "real"),
            ("TOP.happening0",          0,  "event"),
            ("TOP.happening1",          1,  "event"),
        ]

        self.varaliases0 = [
            ("TOP.clk", "TOP.myblock.i_clk", "logic"),
            ("TOP.rst", "TOP.myblock.i_rst", "bit"),
        ]

        self.golden0Chunks = [
            (0, ["TOP.clk", "TOP.rst", "TOP.myblock.counter"],
                [       0 ,        0 ,                    0 ]),
            (1, ["TOP.rst", "TOP.happening0", "TOP.happening1"],
                [       1 ,               0 ,               1 ]),
            (2, ["TOP.clk", "TOP.myblock.counter"],
                [       1 ,                    1 ]),
            (3, ["TOP.clk", "TOP.myblock.floating8b"],
                [       0 ,                     0.5 ]),
            (4, ["TOP.clk", "TOP.myblock.counter"],
                [       1 ,                    2 ]),
        ]

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        fname = os.path.join(self.tstDir, "result0.vcd")
        with VcdWriter(fname) as vw:

            vw.wrHeader(self.varlist0,
                comment="hello world",
                date="Monday 12th August",
                version="dmppl.vcd.VcdWriter",
                timescale="10us",
                varaliases=self.varaliases0,
            )

            self.assertEqual(vw.vcdVersion, "dmppl.vcd.VcdWriter")
            self.assertEqual(vw.vcdDate, "Monday 12th August")
            self.assertEqual(vw.vcdComment, "hello world")
            self.assertTupleEqual(vw.vcdTimescale, ('10', "us"))

            self.assertSequenceEqual(vw.varIds,
                ['!', '"', '#', '$', '%', '&', "'", '(', ')', '!', '"'])
            self.assertSequenceEqual(vw.varIdsUnique,
                ['!', '"', '#', '$', '%', '&', "'", '(', ')'])

            goldenVarSizes = [
                1, 1,           # clk, rst
                8,              # counter
                8, 16, 32, 64,  # floating*
                1, 1,           # happening0, happening1
                1, 1,           # i_clk, i_rst
            ]
            self.assertSequenceEqual(vw.varSizes, goldenVarSizes)

            goldenVarNames = [
                "TOP.clk",
                "TOP.rst",
                "TOP.myblock.counter",
                "TOP.myblock.floating8b",
                "TOP.myblock.floating16b",
                "TOP.myblock.floating32b",
                "TOP.myblock.floating64b",
                "TOP.happening0",
                "TOP.happening1",
                "TOP.myblock.i_clk",
                "TOP.myblock.i_rst",
            ]
            self.assertSequenceEqual(vw.varNames, goldenVarNames)

            for newTime,changedVarIds,newValues in self.golden0Chunks:
                tc = (newTime,changedVarIds,newValues)
                vw.wrTimechunk(tc)

        goldenTxt = rdTxt(os.path.join(self.tstDir, "golden0.vcd"))
        resultTxt = rdTxt(os.path.join(self.tstDir, fname))
        self.maxDiff = None
        self.assertEqual(goldenTxt, resultTxt)

    def test_NoSeparateTimechunks(self):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr), \
             VcdWriter() as vw:

            vw.separateTimechunks = False # The important line.

            vw.wrHeader(self.varlist0,
                comment="hello world",
                date="Monday 12th August",
                version="dmppl.vcd.VcdWriter",
                timescale="10us",
                varaliases=self.varaliases0,
            )

            for newTime,changedVarIds,newValues in self.golden0Chunks:
                tc = (newTime,changedVarIds,newValues)
                vw.wrTimechunk(tc)

        stdoutTxt, stderrTxt = stdout.getvalue(), stderr.getvalue()

        goldenTxt = rdTxt(os.path.join(self.tstDir, "golden1.vcd"))
        self.maxDiff = None
        self.assertEqual(goldenTxt, stdoutTxt)

# }}} class Test_VcdWriter
