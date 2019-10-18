from dmppl.scripts.vcd_utils import entryPoint
from dmppl.base import rdTxt
from dmppl.test import runEntryPoint
import os
import tempfile
import shutil
import types
import unittest

class Test_Info(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.vcd0 = '''\
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
        self.fname0 = os.path.join(self.tstDir, "tst0.vcd")
        with open(self.fname0, 'w') as fd:
            fd.write(self.vcd0)

        self.goldenInfo0 = '''\
__version__ 0.1.0
filename %s
<id> <name> <size> <type>:
  C module:TOP.clk 1 wire
  C module:TOP.myblock.i_clk 1 wire
  Q module:TOP.myblock.counter[7:0] 8 reg
  R module:TOP.rst 1 wire
  R module:TOP.myblock.i_rst 1 wire
''' % (self.fname0)

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        cmd = "vcd-utils info %s" % self.fname0
        stdout, stderr = runEntryPoint(cmd, entryPoint)
        self.maxDiff = None
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, self.goldenInfo0)

# }}} class Test_Info

class Test_Clean(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.vcd0 = '''\
$version Handwritten 123 $end
$date
    Monday 19th August
$end
$comment Something to say here? $end
$comment
    More to say here.
$end
$timescale 1s $end
$scope module TOP $end
    $var wire 1 C clk $end
    $var wire 1 R rst $end
    $scope module myblock $end
        $var wire 1 C i_clk $end
        $var wire 1 R i_rst $end
        $var reg 8 Q counter [7:0] $end
        $var bit 1 F fastChanging $end
    $upscope $end
    $var event 99 E lookNow $end
    $var real 64 N aReal $end
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
1F

#3
0C
0E
r123.456 N
0F

#4
1C
b00000010 Q
1F

#5
0F
#6
1F
#7
1F
#8
0F
'''
        self.fname0 = os.path.join(self.tstDir, "tst0.vcd")
        with open(self.fname0, 'w') as fd:
            fd.write(self.vcd0)

        self.goldenVcd0 = '''\
$comment Something to say here? More to say here. $end
$date Monday 19th August $end
$version Handwritten 123<<< cleaned by vcd-utils 0.1.0 >>> $end
$timescale 1 s $end
$scope module TOP $end
$var real 64 % aReal [63:0] $end
$var wire 1 " clk  $end
$var event 1 & lookNow  $end
$scope module myblock $end
$var reg 8 $ counter [7:0] $end
$var bit 1 ! fastChanging  $end
$var wire 1 " i_clk  $end
$var wire 1 # i_rst  $end
$upscope $end
$var wire 1 # rst  $end
$upscope $end
$enddefinitions $end
#0
0"
0#
b00000000 $
#1
1#
#2
1!
1"
b00000001 $
#3
0!
0"
r123.456 %
0&
#4
1!
1"
b00000010 $
#5
0!
#6
1!
#7
1!
#8
0!
'''

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        cmd = "vcd-utils clean %s" % self.fname0
        stdout, stderr = runEntryPoint(cmd, entryPoint)
        self.maxDiff = None
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")
        fnameClean = self.fname0 + ".clean.vcd"
        resultTxt = rdTxt(os.path.join(self.tstDir, fnameClean))
        self.assertEqual(self.goldenVcd0, resultTxt)

# }}} class Test_Clean

class Test_Vcd2csv(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.vcd0 = '''\
$version This version is ignored $end
$date The date is also ignored $end
$comment Comments are ignored $end
$timescale 1ns $end
$scope module TOP $end
    $var wire 1 C clk $end
    $var wire 1 R rst $end
    $scope module myblock $end
        $var wire 1 C i_clk $end
        $var wire 1 R i_rst $end
        $var reg 8 Q counter [7:0] $end
    $upscope $end
    $var event 99 E lookNow $end
    $var real 64 N aReal $end
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
0E
r123.456 N

#4
1C
b00000010 Q
'''
        self.fname0 = os.path.join(self.tstDir, "tst0.vcd")
        with open(self.fname0, 'w') as fd:
            fd.write(self.vcd0)

        self.goldenCsv0 = '''\
Time,wire/1,event/99,real/64,reg/8,wire/1
vcdTime,TOP.clk,TOP.lookNow,TOP.aReal,TOP.myblock.counter,TOP.rst
0,0,-,-,0x0,0
1,0,-,-,0x0,1
2,1,-,-,0x1,1
3,0,*,123.456000,0x1,1
4,1,-,123.456000,0x2,1
'''

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        cmd = "vcd-utils vcd2csv %s" % self.fname0
        stdout, stderr = runEntryPoint(cmd, entryPoint)
        self.maxDiff = None
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")
        fnameCsv = self.fname0 + ".csv"
        resultTxt = rdTxt(os.path.join(self.tstDir, fnameCsv))
        self.assertEqual(self.goldenCsv0, resultTxt)

# }}} class Test_Vcd2csv

class Test_Csv2vcd(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.csv0 = '''\
Time,wire/1,event/99,real/64,reg/8,wire/1
vcdTime,TOP.clk,TOP.lookNow,TOP.aReal,TOP.myblock.counter,TOP.rst
0,0,-,-,0x0,0
1,0,-,-,0x0,1
2,1,-,-,0x1,1
3,0,*,123.456000,0x1,1
4,1,-,123.456000,0x2,1
'''
        self.fname0 = os.path.join(self.tstDir, "tst0.csv")
        with open(self.fname0, 'w') as fd:
            fd.write(self.csv0)

        self.goldenVcd0 = '''\
$timescale 1 ns $end
$scope module TOP $end
$var real 64 # aReal [63:0] $end
$var wire 1 ! clk  $end
$var event 1 " lookNow  $end
$scope module myblock $end
$var reg 8 $ counter [7:0] $end
$upscope $end
$var wire 1 % rst  $end
$upscope $end
$enddefinitions $end

#0
0!
b00000000 $
0%

#1
1%

#2
1!
b00000001 $

#3
0!
0"
r123.456000 #

#4
1!
b00000010 $
'''

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        cmd = "vcd-utils csv2vcd %s" % self.fname0
        self.maxDiff = None
        stdout, stderr = runEntryPoint(cmd, entryPoint)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")
        fnameVcd = self.fname0 + ".vcd"
        resultTxt = rdTxt(os.path.join(self.tstDir, fnameVcd))
        self.assertEqual(self.goldenVcd0, resultTxt)

# }}} class Test_Csv2vcd

class Test_Vcd2yml(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.vcd0 = '''\
$version This version is ignored $end
$date The date is also ignored $end
$comment Comments are ignored $end
$timescale 1ns $end
$scope module TOP $end
    $var wire 1 C clk $end
    $var wire 1 R rst $end
    $scope module myblock $end
        $var wire 1 C i_clk $end
        $var wire 1 R i_rst $end
        $var reg 8 Q counter [7:0] $end
    $upscope $end
    $var event 99 E lookNow $end
    $var real 64 N aReal $end
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
0E
r123.456 N

#4
1C
b00000010 Q
'''
        self.fname0 = os.path.join(self.tstDir, "tst0.vcd")
        with open(self.fname0, 'w') as fd:
            fd.write(self.vcd0)

        self.goldenYml0 = '''\
# Generated by vcd2yml 0.1.0
varlist:
  - ["module:TOP.clk", 1, wire, "C"]
  - ["module:TOP.lookNow", 99, event, "E"]
  - ["module:TOP.aReal", 64, real, "N"]
  - ["module:TOP.myblock.counter[7:0]", 8, reg, "Q"]
  - ["module:TOP.rst", 1, wire, "R"]
varaliases:
  - ["module:TOP.clk", "module:TOP.myblock.i_clk", wire]
  - ["module:TOP.rst", "module:TOP.myblock.i_rst", wire]
timechunks:
  0:
    - ["C", "0"]
    - ["R", "0"]
    - ["Q", "00000000"]
  1:
    - ["R", "1"]
  2:
    - ["C", "1"]
    - ["Q", "00000001"]
  3:
    - ["C", "0"]
    - ["E", "0"]
    - ["N", "123.456"]
  4:
    - ["C", "1"]
    - ["Q", "00000010"]
'''

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        cmd = "vcd-utils vcd2yml %s" % self.fname0
        stdout, stderr = runEntryPoint(cmd, entryPoint)
        self.maxDiff = None
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")
        fnameYml = self.fname0 + ".yml"
        resultTxt = rdTxt(os.path.join(self.tstDir, fnameYml))
        self.assertEqual(self.goldenYml0, resultTxt)

# }}} class Test_Vcd2yml

class Test_Yml2vcd(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.yml0 = '''\
# Handwritten YAML which looks like it could be generated.
# varIds are ignored by yml2vcd.
varlist:
  - ["module:TOP.clk", 1, wire, "C"]
  - ["module:TOP.lookNow", 99, event, "E"]
  - ["module:TOP.aReal", 64, real, "N"]
  - ["module:TOP.myblock.counter[7:0]", 8, reg, "Q"]
  - ["module:TOP.rst", 1, wire, "R"]
varaliases:
  - ["TOP.clk", "module:TOP.myblock.i_clk", wire]
  - ["TOP.rst", "module:TOP.myblock.i_rst", wire]
timechunks:
  0:
    - ["C", "0"]
    - ["R", "0"]
    - ["Q", "00000000"]
  1:
    - ["R", "1"]
  2:
    - ["C", "1"]
    - ["Q", "00000001"]
  3:
    - ["C", "0"]
    - ["E", "0"]
    - ["N", "123.456"]
  4:
    - ["C", "1"]
    - ["Q", "00000010"]
'''
        self.fname0 = os.path.join(self.tstDir, "tst0.yml")
        with open(self.fname0, 'w') as fd:
            fd.write(self.yml0)

        self.goldenVcd0 = '''\
$timescale 1 ns $end
$scope module TOP $end
$var real 64 # aReal [63:0] $end
$var wire 1 ! clk  $end
$var event 1 " lookNow  $end
$scope module myblock $end
$var reg 8 $ counter [7:0] $end
$var wire 1 ! i_clk  $end
$var wire 1 % i_rst  $end
$upscope $end
$var wire 1 % rst  $end
$upscope $end
$enddefinitions $end

#0
0!
b00000000 $
0%

#1
1%

#2
1!
b00000001 $

#3
0!
0"
r123.456 #

#4
1!
b00000010 $
'''

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        cmd = "vcd-utils yml2vcd %s" % self.fname0
        stdout, stderr = runEntryPoint(cmd, entryPoint)
        self.maxDiff = None
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")
        fnameVcd = self.fname0 + ".vcd"
        resultTxt = rdTxt(os.path.join(self.tstDir, fnameVcd))
        self.assertEqual(self.goldenVcd0, resultTxt)

# }}} class Test_Yml2vcd
