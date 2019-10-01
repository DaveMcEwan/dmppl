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
                u"vcdhierprefix": u"somepath.prefix.",
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
                    u"name": u"FOO{}-{}-{}",
                    u"hook": u"some{}.block{}.signal[{}]",
                    u"type": u"event",
                    u"subs": [
                        [u"blue", u"red"],
                        [123, 456],
                        [u"0..3"],
                    ],
                },
            ],
        }

        evc = loadEvc()
        self.assertDictEqual(obj0, evc)

# }}} class Test_LoadEvc

class Test_ExpandEvc(unittest.TestCase): # {{{

    def test_Basic0(self):
        self.maxDiff = None
        evc0 = toml.load(path.join(_tstd, "basic0.evc"))
        cfg0 = Bunch()
        cfg0.vcdhierprefix = "somepath.prefix."

        obj0 = {
            u"someNormal": {
                u"hook": u"somepath.prefix.normalHook",
                u"type": u"normal",
                u"idx": 0,
            },
            u"someState": {
                u"hook": u"somepath.prefix.binaryHook",
                u"type": u"binary",
                u"idx": 0,
            },
            u"FOOblue-123-0": {
                u"hook": u"somepath.prefix.someblue.block123.signal[0]",
                u"type": u"event",
                u"idx": 0,
            },
            u"FOOblue-123-1": {
                u"hook": u"somepath.prefix.someblue.block123.signal[1]",
                u"type": u"event",
                u"idx": 1,
            },
            u"FOOblue-123-2": {
                u"hook": u"somepath.prefix.someblue.block123.signal[2]",
                u"type": u"event",
                u"idx": 2,
            },
            u"FOOblue-456-0": {
                u"hook": u"somepath.prefix.someblue.block456.signal[0]",
                u"type": u"event",
                u"idx": 3,
            },
            u"FOOblue-456-1": {
                u"hook": u"somepath.prefix.someblue.block456.signal[1]",
                u"type": u"event",
                u"idx": 4,
            },
            u"FOOblue-456-2": {
                u"hook": u"somepath.prefix.someblue.block456.signal[2]",
                u"type": u"event",
                u"idx": 5,
            },
            u"FOOred-123-0": {
                u"hook": u"somepath.prefix.somered.block123.signal[0]",
                u"type": u"event",
                u"idx": 6,
            },
            u"FOOred-123-1": {
                u"hook": u"somepath.prefix.somered.block123.signal[1]",
                u"type": u"event",
                u"idx": 7,
            },
            u"FOOred-123-2": {
                u"hook": u"somepath.prefix.somered.block123.signal[2]",
                u"type": u"event",
                u"idx": 8,
            },
            u"FOOred-456-0": {
                u"hook": u"somepath.prefix.somered.block456.signal[0]",
                u"type": u"event",
                u"idx": 9,
            },
            u"FOOred-456-1": {
                u"hook": u"somepath.prefix.somered.block456.signal[1]",
                u"type": u"event",
                u"idx": 10,
            },
            u"FOOred-456-2": {
                u"hook": u"somepath.prefix.somered.block456.signal[2]",
                u"type": u"event",
                u"idx": 11,
            },
        }

        evcx0 = expandEvc(evc0, cfg0)

        self.assertDictEqual(obj0, evcx0)

    def test_Basic1(self):
        self.maxDiff = None
        evc1 = toml.load(path.join(_tstd, "basic1.evc"))
        cfg1 = Bunch()
        cfg1.vcdhierprefix = "somepath.prefix."

        obj1 = {
            u"eventNameOfThree0": {
                u"hook": u"somepath.prefix.eventHookOfThree[0]",
                u"type": u"event",
                u"idx": 0,
            },
            u"eventNameOfThree1": {
                u"hook": u"somepath.prefix.eventHookOfThree[1]",
                u"type": u"event",
                u"idx": 1,
            },
            u"eventNameOfThree2": {
                u"hook": u"somepath.prefix.eventHookOfThree[2]",
                u"type": u"event",
                u"idx": 2,
            },
        }

        evcx1 = expandEvc(evc1, cfg1)

        self.assertDictEqual(obj1, evcx1)

# }}} class Test_ExpandEvc
