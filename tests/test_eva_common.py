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

class Test_MeaSearch(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.maxDiff = None
        initPaths(joinP(_tstd, "meaSearch"))

        name = "bstate.foo0"

        mkDirP(paths.dname_mea)
        shutil.copy(joinP(_tstd, name), paths.dname_mea)

        result = []
        for i in [12]:#range(13):
            r = (i, meaSearch(name, i, True), meaSearch(name, i, False))
            result.append(r)

        golden = [
            #(0,     -1, 0),
            #(1,     -1, 0),
            #(2,     -1, 0),
            #(3,     -1, 0),
            #(4,     -1, 0),
            #(5,     0,  0),
            #(6,     1,  1),
            #(7,     2,  2),
            #(8,     2,  3),
            #(9,     2,  3),
            #(10,    3,  3),
            #(11,    3,  None),
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

# }}} class Test_MeaSearch

