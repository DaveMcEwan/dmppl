from dmppl.experiments.eva.eva_init import *
from dmppl.base import rdTxt, Bunch
from dmppl.test import runEntryPoint
from os import path
import tempfile
import shutil
import sys
import unittest

_curd = path.abspath(path.dirname(__file__)) # dmppl/tests
_topd = path.dirname(_curd)
_tstd = path.join(_topd, "dmppl", "experiments", "eva", "tst")

class Test_LoadEvc(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.maxDiff = None
        eva.initPaths(path.join(_tstd, "basic0"))

        obj0 = {
            u"anotherAttribute": 123,
            u"title": u"This attribute is not used.",
            u"config": {
                u"fxbits": 123,
                u"vcdhierprefix": u"module:TOP.blk0.",
            },
            u"measure": [
                {
                    u"name": u"someNormal",
                    u"hook": u"normalHook",
                    u"type": u"normal",
                },
                {
                    u"name": u"someState",
                    u"hook": u"binaryHook",
                    u"type": u"binary",
                },
                {
                    u"name": u"bar{}-{}-{}",
                    u"hook": u"some{}.block{}.signal[{}]",
                    u"type": u"event",
                    u"subs": [
                        [u"blue", u"blah"],
                        [123, 456, 789],
                        [u"0..5"],
                    ],
                },
            ],
        }

        evc = loadEvc()
        self.assertDictEqual(obj0, evc)

# }}} class Test_LoadEvc
