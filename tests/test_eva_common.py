from dmppl.experiments.eva.eva_common import *
from dmppl.base import rdTxt, Bunch, joinP, mkDirP
from dmppl.test import runEntryPoint
from os import path
import tempfile
import shutil
import sys
import toml
import unittest

_curd = path.abspath(path.dirname(__file__)) # dmppl/tests
_topd = path.dirname(_curd)
_tstd = joinP(_topd, "dmppl", "experiments", "eva", "tst")

class Test_meaSearch(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.maxDiff = None
        initPaths(joinP(_tstd, "meaSearch"))

        name = "bstate.foo0"

        mkDirP(paths.dname_mea)
        shutil.copy(joinP(_tstd, name), paths.dname_mea)

        result = []
        for i in range(13):
            r = (i, meaSearch(name, i, True), meaSearch(name, i, False))
            result.append(r)

        golden = [
            (0,     -1, 0),
            (1,     -1, 0),
            (2,     -1, 0),
            (3,     -1, 0),
            (4,     -1, 0),
            (5,     0,  0),
            (6,     1,  1),
            (7,     2,  2),
            (8,     2,  3),
            (9,     2,  3),
            (10,    3,  3),
            (11,    3,  None),
            (12,    3,  None),
        ]
        self.assertEqual(golden, result)

    def test_Basic1(self):
        self.maxDiff = None
        initPaths(joinP(_tstd, "meaSearch"))

        name = "bstate.foo1"

        mkDirP(paths.dname_mea)
        shutil.copy(joinP(_tstd, name), paths.dname_mea)

        result = []
        for i in range(13):
            r = (i, meaSearch(name, i, True), meaSearch(name, i, False))
            result.append(r)

        golden = [
            (0,     -1, 0),
            (1,     -1, 0),
            (2,     -1, 0),
            (3,     -1, 0),
            (4,     -1, 0),
            (5,     0,  0),
            (6,     1,  1),
            (7,     2,  2),
            (8,     2,  None),
            (9,     2,  None),
            (10,    2,  None),
            (11,    2,  None),
            (12,    2,  None),
        ]
        self.assertEqual(golden, result)

# }}} class Test_meaSearch

class Test_dsfDeltas(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 5, 5, 0
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -5),
            (1,     -4),
            (1,     -3),
            (1,     -2),
            (1,     -1),
            (1,     0),
            (1,     1),
            (1,     2),
            (1,     3),
            (1,     4),
        ]
        self.assertEqual(golden, result)

    def test_Basic1(self):
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 3, 3, 0
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -3),
            (1,     -2),
            (1,     -1),
            (1,     0),
            (1,     1),
            (1,     2),
        ]
        self.assertEqual(golden, result)

    def test_ZeroBkBigFw(self):
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 0, 8, 0
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     0),
            (1,     1),
            (1,     2),
            (1,     3),
            (1,     4),
            (1,     5),
            (1,     6),
            (1,     7),
        ]
        self.assertEqual(golden, result)

    def test_BigBkOneFw(self):
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 8, 1, 0
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -8),
            (1,     -7),
            (1,     -6),
            (1,     -5),
            (1,     -4),
            (1,     -3),
            (1,     -2),
            (1,     -1),
            (1,     0),
        ]
        self.assertEqual(golden, result)

    def test_MinDelta(self):
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 0, 1, 0
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     0),
        ]
        self.assertEqual(golden, result)

    def test_SmallWin(self):
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 5, 50, 50, 0
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -2),
            (1,     -1),
            (1,     0),
            (1,     1),
        ]
        self.assertEqual(golden, result)

    def test_BigNonZoom(self):
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 3, 3, 10
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -3),
            (1,     -2),
            (1,     -1),
            (1,     0),
            (1,     1),
            (1,     2),
        ]
        self.assertEqual(golden, result)

    def test_ZoomOne(self): # 1 ==> no zooming
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 3, 3, 1
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -3),
            (1,     -2),
            (1,     -1),
            (1,     0),
            (1,     1),
            (1,     2),
        ]
        self.assertEqual(golden, result)

    def test_ZoomTwo(self): # Two deltas then double step
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 10, 10, 2
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -2),
            (1,     -1),
            (1,     0),
            (1,     1),
            (2,     -6),
            (2,     -4),
            (2,     2),
            (2,     4),
            (4,     -10),
            (4,     6),
        ]
        self.assertEqual(golden, result)

    def test_ZoomThree(self): # Three deltas then double step
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 10, 10, 3
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -3),
            (1,     -2),
            (1,     -1),
            (1,     0),
            (1,     1),
            (1,     2),
            (2,     -9),
            (2,     -7),
            (2,     -5),
            (2,     3),
            (2,     5),
            (2,     7),
            (4,     -10),
            (4,     9),
        ]
        self.assertEqual(golden, result)

    def test_ZoomFour(self): # Four deltas then double step
        self.maxDiff = None

        winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor = 50, 20, 20, 4
        result = dsfDeltas(winSize, reqNDeltasBk, reqNDeltasFw, reqZoomFactor)
        golden = [
            (1,     -4),
            (1,     -3),
            (1,     -2),
            (1,     -1),
            (1,     0),
            (1,     1),
            (1,     2),
            (1,     3),
            (2,     -12),
            (2,     -10),
            (2,     -8),
            (2,     -6),
            (2,     4),
            (2,     6),
            (2,     8),
            (2,     10),
            (4,     -20),
            (4,     -16),
            (4,     12),
            (4,     16),
        ]
        self.assertEqual(golden, result)

# }}} class Test_dsfDeltas

class Test_measureSiblings(unittest.TestCase): # {{{

    def test_Event0(self):
        self.maxDiff = None
        result = measureSiblings("event.measure.foo")
        golden = (
            "event.measure.foo",
        )
        self.assertEqual(golden, result)

    def test_Event1(self):
        self.maxDiff = None
        result = measureSiblings("event.measure.foo.bar.baz")
        golden = (
            "event.measure.foo.bar.baz",
        )
        self.assertEqual(golden, result)

    def test_Bstate0(self):
        self.maxDiff = None
        result = measureSiblings("bstate.measure.foo")
        golden = (
            "bstate.measure.foo",
            "bstate.reflection.foo",
            "bstate.rise.foo",
            "bstate.fall.foo",
        )
        self.assertEqual(golden, result)

    def test_Bstate1(self):
        self.maxDiff = None
        result = measureSiblings("bstate.reflection.foo")
        golden = (
            "bstate.measure.foo",
            "bstate.reflection.foo",
            "bstate.rise.foo",
            "bstate.fall.foo",
        )
        self.assertEqual(golden, result)

    def test_Bstate2(self):
        self.maxDiff = None
        result = measureSiblings("bstate.rise.foo")
        golden = (
            "bstate.measure.foo",
            "bstate.reflection.foo",
            "bstate.rise.foo",
            "bstate.fall.foo",
        )
        self.assertEqual(golden, result)

    def test_Bstate3(self):
        self.maxDiff = None
        result = measureSiblings("bstate.fall.foo")
        golden = (
            "bstate.measure.foo",
            "bstate.reflection.foo",
            "bstate.rise.foo",
            "bstate.fall.foo",
        )
        self.assertEqual(golden, result)

    def test_Threshold0(self):
        self.maxDiff = None
        result = measureSiblings("threshold.measure.foo.bar.baz")
        golden = (
            "threshold.measure.foo.bar.baz",
            "threshold.reflection.foo.bar.baz",
            "threshold.rise.foo.bar.baz",
            "threshold.fall.foo.bar.baz",
        )
        self.assertEqual(golden, result)

    def test_Normal0(self):
        self.maxDiff = None
        result = measureSiblings("normal.raw.foo.bar.baz")
        golden = (
            "normal.measure.foo.bar.baz",
        )
        self.assertEqual(golden, result)

# }}} class Test_SiblingMeasurements

