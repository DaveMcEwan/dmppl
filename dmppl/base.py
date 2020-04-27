
from __future__ import print_function

import errno
import fileinput
import functools
import operator
import os
import re
import sys
import time
import unicodedata

if 2 < sys.version_info[0]:
    long = int

class Object(): # {{{
    '''A generic object class which can be subclassed.

       E.g:
        >>> a = Object()
        >>> a.foo = 5
        >>> b.bar = "hello"
    '''
    pass
# }}} class Object

class Bunch(object): # {{{
    '''Return an object with attributes of the same names as the keys in the
       passed dict.

       E.g:
        >>> a = {"x": 1, "hello": "world"}
        >>> b = Bunch(a)

        >>> b.x
        1

        >>> b.hello
        "world"
    '''
    def __init__(self, d={}):
        assert isinstance(d, dict)
        d_ = {str(k): v for k,v in d.items()}
        self.__dict__.update(d_)
# }}} class Bunch

class Borg: # {{{
    '''All instances get the same state space, similar to a Singleton.

    Useful to avoid passing around large data stuctures.
    '''

    _shared_state = {} # type: ignore

    def __init__(self):
        self.__dict__ = self._shared_state
# }}} class Borg

class Fragile(object): # {{{
    '''Wrap `with` variable using this to allow breaking out of context manager
    by raising Fragile.Break.
    '''

    class Break(Exception):
        pass

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value.__enter__()

    def __exit__(self, etype, value, traceback):
        error = self.value.__exit__(etype, value, traceback)
        if etype == self.Break:
            return True
        return error
# }}} class Fragile

def indexDefault(xs, x, default=None): # {{{
    '''Return the first index of an item in a list, or a default value.

    Allows list comprehension without try/except.
    '''
    try:
        ret = xs.index(x)
    except ValueError:
        ret = default
    return ret
# }}} def indexDefault

def appendNonDuplicate(xs, x, key=None, replace=False, overwrite=False): # {{{
    '''Append x to xs, using key to find existing duplicate, replace or ignore.

    `key` must be either None or a callable returning the index of existing
    duplicate or None if there isn't an existing duplicate.
    E.g. If each x is a tuple and you find duplicates by comparing the 2nd
    element:
        key = (lambda xs, x: indexDefault([y[1] for y in xs], x[1]))

    If `replace` is True then existing is removed and new is either appended or
    overwritten, depending on `replace`.
    If replace is False then no append or overwrite operation occurs for
    duplicates.

    duplicate, replace=True, overwrite=True -> old overwritten by new in-place
    duplicate, replace=True, overwrite=False -> old removed, new appended
    duplicate, replace=False -> no change
    no duplicate -> new appended
    '''
    if key is None:
        if isinstance(x, (list, tuple)):
            # Compare first element if x is a tuple.
            k = (lambda xs, x: indexDefault([y[0] for y in xs], x[0]))
        else:
            # Compare directly.
            k = (lambda xs,x: indexDefault(xs, x))
    else:
        # Use a caller-specified key.
        k = key

    foundIndex = k(xs, x)

    if foundIndex is not None:
        assert isinstance(foundIndex, int), (type(foundIndex), foundIndex)
        assert foundIndex < len(xs)
        if replace:
            if overwrite:
                # duplicate, replace=True, overwrite=True ->
                #   old overwritten by new in-place
                xs[foundIndex] = x
            else:
                # duplicate, replace=True, overwrite=False ->
                #   old removed, new appended
                xs.pop(foundIndex)
                xs.append(x)
        else:
            # duplicate, replace=False ->
            #   no change
            pass
    else:
        # no duplicate ->
        #   new appended
        xs.append(x)

    return xs
# }}} def appendNonDuplicate

def stripSuffix(t, s): # {{{
    '''Remove an optional suffix from a string.

    NOTE: Different from rstrip(), os.path.splitext().
    '''
    assert isinstance(t, str)
    assert isinstance(s, str)

    if t.endswith(s):
        ret = t[:len(t) - len(s)]
    else:
        ret = t

    return ret
# }}} def stripSuffix

def fnameStripExt(fname, ext): # {{{
    '''Strip a given case-insensitive extension from a filename, if it exists.
    '''
    assert isinstance(fname, str)
    assert isinstance(ext, str)

    froot, fext = os.path.splitext(fname)

    # Remove dot separator
    fextClean = fext[1:]
    extClean = ext[1:] if ext.startswith('.') else ext

    return froot if fextClean.lower() == extClean.lower() else fname
# }}} def fnameStripExt

def fnameAppendExt(fname, ext): # {{{
    '''Append a given lowercase extension to a filename, if not already given.
    '''
    assert isinstance(fname, str)
    assert isinstance(ext, str)

    return (fname) if fname.lower().endswith('.' + ext.lower()) else \
           (fname + '.' + ext)
# }}} def fnameAppendExt

def lowerCamelCase(s): # {{{
#def lowerCamelCase(s:str) -> str:
    '''Convert a non-empty string to lower camel case.

    Replace punctuation with underscores.

    "foo"               -> "foo"
    "foOBAR"            -> "foOBAR"
    "fooBar"            -> "fooBar"
    "FooBar"            -> "fooBar"
    "foo bar baz"       -> "fooBarBaz"
    "foo Bar baz"       -> "fooBarBaz"
    "foo Bar    baz"    -> "fooBarBaz"
    "foo Bar 123"       -> "fooBar123"
    "foo -. Bar baz 123" -> "foo_BarBaz123"
    "foo# bar baz 123" -> "foo_BarBaz123" TODO: Is this really what I want?
    "foo#Bar baz 123" -> "foo_BarBaz123"
    '''
    assert isinstance(s, str)
    assert 0 < len(s)

    #words:List[str] = [w for w in s.split() if 0 < len(w)]
    words = [w for w in s.split() if 0 < len(w)]

    # Python2.7 doesn't support case folding so just use lowercase
    # which does a similar thing and will probably be good enough for
    # many usecases.
    # str.casefold() introduced in Python3.3
    #firstWord:str = words[0]
    firstWord = words[0]
    try:
        #firstCased:str = firstWord[0].casefold() + firstWord[1:]
        firstCased = firstWord[0].casefold() + firstWord[1:]
    except AttributeError:
        firstCased = firstWord[0].lower() + firstWord[1:]

    #nonFirstCased:List[str] = [w[0].upper() + w[1:] for w in words[1:]]
    nonFirstCased = [w[0].upper() + w[1:] for w in words[1:]]


    #cased:str = ''.join([firstCased] + nonFirstCased)
    cased = ''.join([firstCased] + nonFirstCased)

    #depunct:str = re.sub(r"\W+", '_', cased)
    depunct = re.sub(r"\W+", '_', cased)

    return depunct
# }}} def lowerCamelCase

def product(xs): # {{{
    '''Return the product of a list/tuple of numbers.
    '''
    return functools.reduce(operator.mul, xs, 1)
# }}} def product

def compose(f, g, unpack=False): # {{{
    '''Compose 2 functions together.

    Port from Collin Winter's functional module, now dead links.
    E.g:
    >>> compose(f, g)(5, 6)
    is equivalent to
    >>> f(g(5, 6))

    >>> compose(f, g, unpack=True)
    >>> f(*g(5, 6))
    '''
    assert callable(f)
    assert callable(g)

    if unpack:
        def composition(*args, **kwargs):
            return f(*g(*args, **kwargs))
    else:
        def composition(*args, **kwargs):
            return f(g(*args, **kwargs))

    return composition
# }}} def compose

def utf8NameToHtml(name): # {{{
    '''Return the HTML entity for a UTF character name.
    '''
    return "&#x{:04x};".format(ord(unicodedata.lookup(name)))
# }}} def utf8NameToHtml

def tmdiff_wdhms2s(weeks, days, hours, minutes, seconds): # {{{
    '''Convert a time difference in a tuple of (weeks, days, hours, minutes,
       seconds) to seconds.
    '''
    assert isinstance(weeks, (int, long))
    assert isinstance(days, (int, long))
    assert isinstance(hours, (int, long))
    assert isinstance(minutes, (int, long))
    assert isinstance(seconds, (int, long, float))

    assert 0 <= weeks
    assert 0 <= days
    assert 0 <= hours
    assert 0 <= minutes
    assert 0 <= seconds

    s_in_week   = 60*60*24*7
    s_in_day    = 60*60*24
    s_in_hour   = 60*60
    s_in_minute = 60

    ret = [weeks   * s_in_week,
           days    * s_in_day,
           hours   * s_in_hour,
           minutes * s_in_minute,
           seconds]

    return sum(ret)
# }}} def tmdiff_wdhms2s

def tmdiff_s2wdhms(s): # {{{
    '''Convert a time difference in seconds to a tuple of (weeks, days, hours,
       minutes, seconds).

    Larger time units like months are irregular.
    '''
    assert isinstance(s, (int, long, float))
    assert 0 <= s

    s_in_week   = 60*60*24*7
    s_in_day    = 60*60*24
    s_in_hour   = 60*60
    s_in_minute = 60

    weeks, s_week    = divmod(s,      s_in_week)
    days, s_day      = divmod(s_week, s_in_day)
    hours, s_hour    = divmod(s_day,  s_in_hour)
    minutes, seconds = divmod(s_hour, s_in_minute)

    assert 0 <= weeks
    assert 0 <= days
    assert 0 <= hours
    assert 0 <= minutes
    assert 0 <= seconds

    return int(weeks), int(days), int(hours), int(minutes), float(seconds)
# }}} def tmdiff_s2wdhms

def tmdiffStr(weeks, days, hours, minutes, seconds): # {{{
    '''Return string of text showing the
       number of weeks, days, hours, minutes, and seconds.

       E.g:
       >>> tmdiffStr(0, 0, 1, 1, 1)
       "1h1m1s"
    '''
    assert isinstance(weeks, (int, long))
    assert isinstance(days, (int, long))
    assert isinstance(hours, (int, long))
    assert isinstance(minutes, (int, long))
    assert isinstance(seconds, (int, long, float))

    assert 0 <= weeks
    assert 0 <= days
    assert 0 <= hours
    assert 0 <= minutes
    assert 0 <= seconds

    ret = []
    if 0 < weeks:   ret.append("%dw" % weeks)
    if 0 < days:    ret.append("%dd" % days)
    if 0 < hours:   ret.append("%dh" % hours)
    if 0 < minutes: ret.append("%dm" % minutes)
    ret.append("%0.3fs" % seconds)

    return ''.join(ret)
# }}} def tmdiff_s2text
tmdiff = compose(tmdiffStr, tmdiff_s2wdhms, unpack=True)

def deduplicateSpaces(s): # {{{
    '''Collapse multiple spaces in a string to single spaces.
    '''
    assert isinstance(s, str)

    return re.sub(" +", ' ', s)
# }}} def deduplicateSpaces

def isCommentLine(s, c='#'): # {{{
    '''Return True if a left-striped string starts with '#'.
    '''
    assert isinstance(s, str)
    assert isinstance(c, str)

    return s.lstrip().startswith(c)
# }}} def isCommentLine

def notCommentLine(s, c='#'): # {{{
    '''Return False if a left-striped string starts with '#'.
    '''
    assert isinstance(s, str)
    assert isinstance(c, str)

    return not isCommentLine(s, c)
# }}} def notCommentLine

def rdLines(fname, **kwargs): # {{{
    '''Open a file in text mode, yield lines.

    If fname is None then use STDOUT.
    Each line is passed through a series of filters and mappings (configurable
    with kwargs) before yielding.

    Keyword arguments control behaviour:
        commentLines = { True | False }
            Ignore lines beginning with '#', using isCommentLine().
        commentMark = <str>
            Character, or short string, denoting comment line.
        expandTabs = { True | False }
            Transform tab characters into spaces.
        deduplicateSpaces = { True | False }
            Collapse multiple spaces to single space.
        rightStrip = { True | False }
            Remove trailing whitespace.
        leftStrip = { True | False }
            Remove leading whitespace.
        caseFold = { True | False }
            Transform to lowercase but more aggressive with unicode.
            On Python2 this only converts to lowercase.

    If file doesn't exist return None, leaving the caller to check.
    This makes it usable in filtered list comprehensions.
    '''
    kwarg_commentLines        = kwargs.get("commentLines",        True)
    kwarg_commentMark         = kwargs.get("commentMark",         '#')
    kwarg_expandTabs          = kwargs.get("expandTabs",          True)
    kwarg_deduplicateSpaces   = kwargs.get("deduplicateSpaces",   True)
    kwarg_rightStrip          = kwargs.get("rightStrip",          True)
    kwarg_leftStrip           = kwargs.get("leftStrip",           True)
    kwarg_caseFold            = kwargs.get("caseFold",            False)

    try:
        fd_0 = sys.stdin if (fname is None) else fileinput.input(fname)

        _notCommentLine = functools.partial(notCommentLine, c=kwarg_commentMark)
        fd_1 = filter(_notCommentLine, fd_0) \
            if kwarg_commentLines else fd_0

        fd_2 = map(str.expandtabs, fd_1) \
            if kwarg_expandTabs else fd_1

        fd_3 = map(deduplicateSpaces, fd_2) \
            if kwarg_deduplicateSpaces else fd_2

        fd_4 = map(str.rstrip, fd_3) \
            if kwarg_rightStrip else fd_3

        fd_5 = map(str.lstrip, fd_4) \
            if kwarg_leftStrip else fd_4

        # Python2.7 doesn't support case folding so just use lowercase
        # which does a similar thing and will probably be good enough for
        # many usecases.
        # str.casefold() introduced in Python3.3
        if kwarg_caseFold:
            try:
                fd_6 = map(str.casefold, fd_5)
            except AttributeError:
                fd_6 = map(str.lower, fd_5)
        else:
            fd_6 = fd_5

        for line in fd_6:
            yield line

    except IOError:
        yield None

# }}} def rdLines

def rdTxt(fname): # {{{
    '''Open a file in text mode, and return the full contents in memory.

    If file doesn't exist return None, leaving the caller to check.
    This makes it usable in filtered list comprehensions.
    '''
    try:
        with open(fname, 'r') as fd:
            # Universal newlines aren't quite as universal as they should be!
            ret = fd.read().replace("\r\n", '\n').replace('\r', '\n')
    except IOError:
        ret = None

    return ret
# }}} def rdTxt

def mkDirP(path): # {{{
    '''Make a directory just like `mkdir -p DIRECTORY`.
    '''
    assert isinstance(path, str)
    assert 0 < len(path)

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
    return
# }}} def mkDirP

joinP = os.path.join # Just a convenient alias

def verb(msg='', end='\n', sv_tm=False, rpt_tm=False): # {{{
    '''Print a message to STDOUT when verbose flag is set.

    Each line is prefixed with it's number which is kept track with a static
    variable, so this should not be called from parallel code.
    Optionally save and/or report time difference since last call, which is
    useful for coarse profiling.

    Intended for use with argparse - Set `verb.flag = True` once.
    '''

    tm_now = time.time()

    # Initialize static variables on first execution.
    static_vars = ["linenum", "newline", "tm_saved"]
    if False in [hasattr(verb, x) for x in static_vars]:
        verb.linenum = 1     # Strictly incrementing counter of printed lines.
        verb.newline = True  # FSM used for counting lines and printing numbers.
        verb.tm_saved = None # Storage for time state.

    if verb.flag:
        if verb.newline:
            outstr = "%d %s" % (verb.linenum, str(msg))
        else:
            outstr = str(msg)

        if rpt_tm:
            outstr += " [%s]" % tmdiff(tm_now - verb.tm_saved)

        fd = sys.stdout

        print(outstr, end=end, file=fd)
        fd.flush()

        if end == '\n':
            verb.linenum += 1
            verb.newline = True
        else:
            verb.newline = False

    if sv_tm:
        verb.tm_saved = time.time()
# }}} def verb

# Initialise flag to quiet.
verb.flag = False # type: ignore

def dbg(x='', *args, **kwargs): # {{{
    '''Print a debug message to STDERR.

    These messages won't appear when running Python with -O.
    Most uses of this are temorary and should be removed from codebase.

    Prefix is useful for distinguishing between threads and suchlike.
    '''
    prefix = kwargs.get("prefix", None)
    assert isinstance(prefix, str) or prefix is None

    if __debug__:

        _str = str
        if sys.version_info[0] == 2:
            _str = unicode

        func = sys._getframe().f_back.f_code.co_name
        line = sys._getframe().f_back.f_lineno
        fd = sys.stderr

        for arg in [x]+list(args):
            typename = type(arg).__name__

            msg = "%s():%s:%s:" % (func, line, typename)
            msg += ' ' if prefix is None else "%s: " % prefix

            if isinstance(arg, list) or isinstance(arg, tuple) or isinstance(arg, set):
                msg += ", ".join([_str(i) for i in arg])
            elif isinstance(arg, dict):
                msg += ", ".join(["%s: %s" % (_str(k), _str(arg[k])) for k in arg])
            else:
                msg += _str(arg)


            print(msg, file=fd)

        fd.flush()
# }}} def dbg

def info(msg='', end='\n', prefix="INFO: ", fd=sys.stdout): # {{{
    '''Print a human-friendly, but not necessarily machine-friendly,
       informational message to STDOUT (changeable).

    Prefix token "INFO" used to allow easy removal with grep.
    '''
    assert isinstance(msg, str)
    assert isinstance(end, str)
    assert isinstance(prefix, str)

    outstr = prefix + str(msg)
    print(outstr, end=end, file=fd)
    fd.flush()
# }}} def info

def run(parent_name, argv=sys.argv): # {{{
    '''Run a module using a consistent framework.

    Relies on existence of argparser and main() in calling module.

    E.g
    First define argparser and main(args) then use like this
    >>> if __name__ == "__main__":
    >>>     sys.exit(run(__name__))
    '''

    try:
        import importlib
        caller = importlib.import_module(parent_name)
        assert hasattr(caller, "argparser")
        assert hasattr(caller, "main")
        assert hasattr(caller, "__version__")

        # A copy of argparser is modified rather than the original.
        # This allows run() to be called multiple times, such as within
        # unittesting.
        # Dropping support for Python <3.7 would make life easier.
        try:
            import copy
            argparser = copy.deepcopy(caller.argparser)
        except:# TypeError: # CPython <3.7 bug can't copy ArgumentParser.
            try:
                importlib.reload(caller)
            except:# AttributeError: # Python <3.4 reload is elsewhere.
                try:
                    reload(caller)
                except:# ImportError Cannot re-init internal module __main__
                    pass
            argparser = caller.argparser

        argparser.add_argument("--version",
            action='version',
            version = caller.__version__,
            help="Print version and exit.")

        argparser.add_argument("-v", "--verbose",
            default=False,
            action='store_true',
            help="Display verbose messages.")

        argparser.add_argument("--profile",
            default=False,
            action='store_true',
            help="Enable deterministic profiling.")

        args = argparser.parse_args(argv[1:])

        args.__caller__ = caller # Reference back to calling module.

    except IOError as e:
        msg = "IOError: %s: %s\n" % (e.strerror, e.filename)
        sys.stderr.write(msg)
        return 1 # sys.exit(1)

    # Extract verbose flag and delete so that application doesn't need to worry
    # about it, can still detect when set though.
    verb.flag = args.verbose
    delattr(args, "verbose")

    # Extract profile flag and delete so that application can't fake behaviour.
    profile = args.profile
    delattr(args, "profile")

    if profile:
        import cProfile
        import pstats
        pr = cProfile.Profile()
        pr.enable()

    ret = caller.main(args)

    if profile:
        pr.disable()
        ps = pstats.Stats(pr, stream=sys.stderr)
        ps.sort_stats("cumulative")
        ps.print_stats()
        #ps.print_stats(.1) # Restrict printing to the top 10%.

    return ret
# }}} def run

if __name__ == "__main__":
    assert False, "Not a standalone script."
