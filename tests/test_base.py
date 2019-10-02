from dmppl.base import *
import os
import tempfile
import shutil
import types
import unittest

class Test_Object(unittest.TestCase): # {{{

    def test_Basic0(self):
        myobj = Object()
        myobj.someAttr = "foo"
        self.assertEqual(myobj.someAttr, "foo")
        self.assertEqual(getattr(myobj, "someAttr"), "foo")

# }}} class Test_Object

class Test_Bunch(unittest.TestCase): # {{{

    def test_Basic0(self):
        mydict = {"hello": "world", "foo": 123}
        myobj = Bunch(mydict)
        self.assertEqual(myobj.hello, "world")
        self.assertEqual(myobj.foo, 123)

    def test_IntKeys0(self):
        mydict = {123: "foo", 456: 789}
        myobj = Bunch(mydict)
        self.assertEqual(getattr(myobj, "123"), "foo")
        self.assertEqual(getattr(myobj, "456"), 789)

    def test_MixKeyTypes0(self):
        mydict = {123: "foo", "hello": "world"}
        myobj = Bunch(mydict)
        self.assertEqual(myobj.hello, "world")
        self.assertEqual(getattr(myobj, "123"), "foo")

# }}} class Test_Bunch

class Test_Borg(unittest.TestCase): # {{{

    class EgClass0(Borg):
        def __init__(self, arg0, arg1="foo"):
            Borg.__init__(self) # NOTE: Essential!
            self.arg0 = arg0
            self.arg1 = arg1

    def test_Basic0(self):
        myinst0 = self.EgClass0(123)
        self.assertEqual(myinst0.arg0, 123)
        self.assertEqual(myinst0.arg1, "foo")

        myinst1 = self.EgClass0(456)
        self.assertEqual(myinst0.arg0, 456)
        self.assertEqual(myinst0.arg1, "foo")
        self.assertEqual(myinst1.arg0, 456)
        self.assertEqual(myinst1.arg1, "foo")

        myinst2 = self.EgClass0(789, "bar")
        self.assertEqual(myinst0.arg0, 789)
        self.assertEqual(myinst0.arg1, "bar")
        self.assertEqual(myinst1.arg0, 789)
        self.assertEqual(myinst1.arg1, "bar")
        self.assertEqual(myinst2.arg0, 789)
        self.assertEqual(myinst2.arg1, "bar")

        myinst0.hello = "world"
        self.assertEqual(myinst0.hello, "world")
        self.assertEqual(myinst1.hello, "world")
        self.assertEqual(myinst2.hello, "world")

# }}} class Test_Borg

class Test_indexDefault(unittest.TestCase): # {{{

    def test_Basic0(self):
        xs = ["foo", "bar", "baz"]
        result = indexDefault(xs, "bar")
        self.assertEqual(result, 1)

    def test_Basic1(self):
        xs = ["foo", "bar", "baz"]
        result = indexDefault(xs, "zoo")
        self.assertEqual(result, None)

    def test_Default0(self):
        xs = ["foo", "bar", "baz"]
        result = indexDefault(xs, "bar", default=False)
        self.assertEqual(result, 1)

    def test_Default1(self):
        xs = ["foo", "bar", "baz"]
        result = indexDefault(xs, "zoo", default=False)
        self.assertEqual(result, False)

# }}} class Test_indexDefault

class Test_appendNonDuplicate(unittest.TestCase): # {{{

    def test_NonDup(self):
        # Straighforward append of new item.
        xs = ["foo", "bar", "baz"]
        x = "blue"
        result = appendNonDuplicate(xs, x)
        self.assertListEqual(result, ["foo", "bar", "baz", "blue"])

    def test_NoReplace(self):
        # No change since duplicate exists.
        xs = ["foo", "bar", "baz"]
        x = "bar"
        result = appendNonDuplicate(xs, x)
        self.assertListEqual(result, ["foo", "bar", "baz"])

    def test_Replace(self):
        # Old removed and new appended.
        xs = ["foo", "bar", "baz"]
        x = "bar"
        result = appendNonDuplicate(xs, x, replace=True)
        self.assertListEqual(result, ["foo", "baz", "bar"])

    def test_Key(self):
        # Old removed and new appended.
        xs = [("foo", 1), ("bar", 2), ("baz", 3)]
        x = ("bar", 5)

        # Example from docstring, compare by first element.
        k = (lambda xs, x: indexDefault([y[0] for y in xs], x[0]))

        result = appendNonDuplicate(xs, x, key=k, replace=True)
        self.assertListEqual(result, [("foo", 1), ("baz", 3), ("bar", 5)])

    def test_Overwrite(self):
        # Old removed and new appended.
        xs = [("foo", 1), ("bar", 2), ("baz", 3)]
        x = ("bar", 5)

        # Example from docstring, compare by first element.
        k = (lambda xs, x: indexDefault([y[0] for y in xs], x[0]))

        result = appendNonDuplicate(xs, x, key=k, replace=True, overwrite=True)
        self.assertListEqual(result, [("foo", 1), ("bar", 5), ("baz", 3)])

# }}} class Test_appendNonDuplicate

class Test_stripSuffix(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = stripSuffix("hello.world.txt", ".txt")
        self.assertEqual(result, "hello.world")

    def test_Basic1(self):
        result = stripSuffix("hello.world.txt", "txt")
        self.assertEqual(result, "hello.world.")

    def test_Basic2(self):
        result = stripSuffix("hello.world.txt", ".foo")
        self.assertEqual(result, "hello.world.txt")

    def test_EmptySuffix(self):
        result = stripSuffix("hello.world.txt", "")
        self.assertEqual(result, "hello.world.txt")

    def test_EmptyText(self):
        result = stripSuffix("", ".txt")
        self.assertEqual(result, "")

# }}} class Test_stripSuffix

class Test_fnameAppendExt(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = fnameAppendExt("hello.world", "txt")
        self.assertEqual(result, "hello.world.txt")

    def test_Basic1(self):
        result = fnameAppendExt("hello.world.txt", "txt")
        self.assertEqual(result, "hello.world.txt")

    def test_Basic2(self):
        result = fnameAppendExt("hello.world.foo", "txt")
        self.assertEqual(result, "hello.world.foo.txt")

    def test_Basic3(self):
        result = fnameAppendExt("hello.world.foo.txt", "txt")
        self.assertEqual(result, "hello.world.foo.txt")

    def test_EmptyText(self):
        result = fnameAppendExt("", "txt")
        self.assertEqual(result, ".txt")

# }}} class Test_fnameAppendExt

class Test_compose(unittest.TestCase): # {{{

    def test_Basic0(self):

        def times2(x): # Take 1, give 1
            return x * 2

        def add1(x): # Take 1, give 1
            return x + 1

        doubleThenIncr = compose(add1, times2)
        incrThenDouble = compose(times2, add1)
        incrThenDoubleThenDouble = compose(times2, incrThenDouble)

        result0 = doubleThenIncr(10)
        result1 = incrThenDouble(10)
        result2 = incrThenDoubleThenDouble(10)
        self.assertEqual(result0, 21)
        self.assertEqual(result1, 22)
        self.assertEqual(result2, 44)

    def test_MultiArgRHS0(self):

        def times2(x): # Take 1, give 1
            return x * 2

        def f(a, b): # Take 2, give 1
            return a + b

        doubleF = compose(times2, f)

        result = doubleF(10, 5)
        self.assertEqual(result, 30)

    def test_Packed0(self):

        def f(a, b): # Take 2, give 2
            return (a + b, a - b)

        def g(c, d): # Take 2, give 2
            return (c * d, c // d)

        fThenG = compose(g, f, unpack=True) # g(*f(x, y))
        gThenF = compose(f, g, unpack=True) # f(*g(x, y))

        result0 = fThenG(10, 5)
        result1 = gThenF(10, 5)
        self.assertEqual(result0, (75, 3))
        self.assertEqual(result1, (52, 48))

    def test_Unpacked0(self):

        def f(x): # Take 1, give 2
            a, b = x
            return (a + b, a - b)

        def g(y): # Take 1, give 2
            c, d = y
            return (c * d, c // d)

        fThenG = compose(g, f) # unpack=False is default
        gThenF = compose(f, g, unpack=False)

        result0 = fThenG((10, 5))
        result1 = gThenF((10, 5))
        self.assertEqual(result0, (75, 3))
        self.assertEqual(result1, (52, 48))

    # TODO: Tests showing use of kwargs.

# }}} class Test_compose

class Test_tmdiff_wdhms2s(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = tmdiff_wdhms2s(1, 2, 3, 4, 5)
        self.assertEqual(result, 788645)

    def test_Basic1(self):
        result = tmdiff_wdhms2s(1, 2, 3, 4, 5.678)
        self.assertEqual(result, 788645.678)

# }}} class Test_tmdiff_wdhms2s

class Test_tmdiff_s2wdhms(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = tmdiff_s2wdhms(788645)
        self.assertEqual(result, (1, 2, 3, 4, 5))

    def test_Basic1(self):
        result = tmdiff_s2wdhms(788645.678)
        for r,g in zip(result, (1, 2, 3, 4, 5.678)):
            self.assertAlmostEqual(r, g, places=3)

# }}} class Test_tmdiff_wdhms2s

class Test_tmdiffStr(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = tmdiffStr(1, 2, 3, 4, 5)
        self.assertEqual(result, "1w2d3h4m5.000s")

    def test_Basic1(self):
        result = tmdiffStr(1, 2, 3, 4, 5.678)
        self.assertEqual(result, "1w2d3h4m5.678s")

    def test_Basic2(self):
        result = tmdiffStr(0, 0, 0, 4, 5.678)
        self.assertEqual(result, "4m5.678s")

# }}} class Test_tmdiffStr

class Test_tmdiff(unittest.TestCase): # {{{

    def test_Basic0(self):
        result = tmdiff(788645)
        self.assertEqual(result, "1w2d3h4m5.000s")

    def test_Basic1(self):
        result = tmdiff(788645.678)
        self.assertEqual(result, "1w2d3h4m5.678s")

    def test_Basic2(self):
        result = tmdiff(245.678)
        self.assertEqual(result, "4m5.678s")

# }}} class Test_tmdiff

class Test_deduplicateSpaces(unittest.TestCase): # {{{

    def test_Basic0(self):
        s = "hello  world"
        self.assertEqual(deduplicateSpaces(s), "hello world")

    def test_Basic1(self):
        s = "foo  bar    baz foo"
        self.assertEqual(deduplicateSpaces(s), "foo bar baz foo")

    def test_OtherWhitespace(self):
        s = "foo  \nbar\t  \n  baz\r foo"
        self.assertEqual(deduplicateSpaces(s), "foo \nbar\t \n baz\r foo")

# }}} class Test_deduplicateSpaces

class Test_isCommentLine(unittest.TestCase): # {{{

    def test_Basic0(self):
        lines = [
            "nope",
            " nope",
            " nope#",
            " nope\t\n\r    nope",
            "# yep",
            " # yep",
            " \t\n\r# yep",
        ]
        result = [isCommentLine(line) for line in lines]
        golden = ["yep" in line for line in lines]
        self.assertEqual(result, golden)

    def test_Basic1(self):
        lines = [
            "nope",
            " nope",
            " nope%",
            " nope\t\n\r    nope",
            "% yep",
            " % yep",
            " \t\n\r% yep",
        ]
        result = [isCommentLine(line, '%') for line in lines]
        golden = ["yep" in line for line in lines]
        self.assertEqual(result, golden)

# }}} class Test_isCommentLine

class Test_notCommentLine(unittest.TestCase): # {{{

    def test_Basic0(self):
        lines = [
            "nope",
            " nope",
            " nope#",
            " nope\t\n\r    nope",
            "# yep",
            " # yep",
            " \t\n\r# yep",
        ]
        result = [notCommentLine(line) for line in lines]
        golden = ["nope" in line for line in lines]
        self.assertEqual(result, golden)

    def test_Basic1(self):
        lines = [
            "nope",
            " nope",
            " nope%",
            " nope\t\n\r    nope",
            "% yep",
            " % yep",
            " \t\n\r% yep",
        ]
        result = [notCommentLine(line, '%') for line in lines]
        golden = ["nope" in line for line in lines]
        self.assertEqual(result, golden)

# }}} class Test_notCommentLine

class Test_rdLines(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.txt0 = '''\
hello world
# comment
    # indented comment
% altcomment TeX
// altcomment C++
with\t\t\ttabs
lower aNd UPPER
   some left space
''' + "some right space   \n " + "   space on both ends   \n"
        fname0 = os.path.join(self.tstDir, "txt0")
        with open(fname0, 'w') as fd:
            fd.write(self.txt0)

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_LineGenerator(self):
        fname = os.path.join(self.tstDir, "txt0")
        result = rdLines(fname)
        self.assertIsInstance(result, types.GeneratorType)

    def test_NonExistent(self):
        fname = os.path.join(self.tstDir, "nonexistent")
        self.assertEqual(list(rdLines(fname)), [None])

    def test_Basic0(self):
        fname = os.path.join(self.tstDir, "txt0")
        golden = [
            "hello world",
            "% altcomment TeX",
            "// altcomment C++",
            "with tabs",
            "lower aNd UPPER",
            "some left space",
            "some right space",
            "space on both ends",
        ]

        for line, g in zip(rdLines(fname), golden):
            self.assertEqual(line, g)

    def test_NoComment(self):
        fname = os.path.join(self.tstDir, "txt0")
        golden = [
            "hello world",
            "# comment",
            "# indented comment",
            "% altcomment TeX",
            "// altcomment C++",
            "with tabs",
            "lower aNd UPPER",
            "some left space",
            "some right space",
            "space on both ends",
        ]

        for line, g in zip(rdLines(fname, commentLines=False), golden):
            self.assertEqual(line, g)

    def test_AltComment0(self):
        fname = os.path.join(self.tstDir, "txt0")
        golden = [
            "hello world",
            "# comment",
            "# indented comment",
            "// altcomment C++",
            "with tabs",
            "lower aNd UPPER",
            "some left space",
            "some right space",
            "space on both ends",
        ]

        for line, g in zip(rdLines(fname, commentMark='%'), golden):
            self.assertEqual(line, g)

    def test_AltComment1(self):
        fname = os.path.join(self.tstDir, "txt0")
        golden = [
            "hello world",
            "# comment",
            "# indented comment",
            "% altcomment TeX",
            "with tabs",
            "lower aNd UPPER",
            "some left space",
            "some right space",
            "space on both ends",
        ]

        for line, g in zip(rdLines(fname, commentMark="//"), golden):
            self.assertEqual(line, g)

    def test_NoExpandTabs(self):
        fname = os.path.join(self.tstDir, "txt0")
        golden = [
            "hello world",
            "% altcomment TeX",
            "// altcomment C++",
            "with\t\t\ttabs",
            "lower aNd UPPER",
            "some left space",
            "some right space",
            "space on both ends",
        ]

        for line, g in zip(rdLines(fname, expandTabs=False), golden):
            self.assertEqual(line, g)

    def test_NoLeftStrip(self):
        fname = os.path.join(self.tstDir, "txt0")
        golden = [
            "hello world",
            "% altcomment TeX",
            "// altcomment C++",
            "with tabs",
            "lower aNd UPPER",
            " some left space",
            "some right space",
            " space on both ends",
        ]

        for line, g in zip(rdLines(fname, leftStrip=False), golden):
            self.assertEqual(line, g)

    def test_NoRightStrip(self):
        fname = os.path.join(self.tstDir, "txt0")
        golden = [
            "hello world\n",
            "% altcomment TeX\n",
            "// altcomment C++\n",
            "with tabs\n",
            "lower aNd UPPER\n",
            "some left space\n",
            "some right space \n",
            "space on both ends \n",
        ]

        for line, g in zip(rdLines(fname, rightStrip=False), golden):
            self.assertEqual(line, g)

    def test_CaseFold(self):
        fname = os.path.join(self.tstDir, "txt0")
        golden = [
            "hello world",
            "% altcomment tex",
            "// altcomment c++",
            "with tabs",
            "lower and upper",
            "some left space",
            "some right space",
            "space on both ends",
        ]

        for line, g in zip(rdLines(fname, caseFold=True), golden):
            self.assertEqual(line, g)

# }}} class Test_rdLines

class Test_rdTxt(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

        self.txt0 = "Lorem ipsum\ndecorum est."
        fname0 = os.path.join(self.tstDir, "txt0")
        with open(fname0, 'w') as fd:
            fd.write(self.txt0)

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        fname = os.path.join(self.tstDir, "txt0")
        result = rdTxt(fname)
        self.assertEqual(result, self.txt0)

    def test_Basic1(self):
        fname = os.path.join(self.tstDir, "nonexistent")
        result = rdTxt(fname)
        self.assertEqual(result, None)

# }}} class Test_rdTxt

class Test_mkDirP(unittest.TestCase): # {{{

    def setUp(self):
        self.tstDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tstDir)

    def test_Basic0(self):
        dname = os.path.join(self.tstDir, "foo", "bar")
        mkDirP(dname)
        self.assertTrue(os.path.exists(dname))
        self.assertTrue(os.path.isdir(dname))

# }}} class Test_mkDirP

