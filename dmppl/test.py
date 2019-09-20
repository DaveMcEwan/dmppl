
import sys

try:
    from contextlib import redirect_stdout, redirect_stderr
    from io import StringIO
except: # Python <3.4
    from contextlib import contextmanager
    from StringIO import StringIO

    @contextmanager
    def redirect_stdout(stream):
        realStdout, sys.stdout = sys.stdout, stream
        try:
            yield
        finally:
            sys.stdout = realStdout

    @contextmanager
    def redirect_stderr(stream):
        realStderr, sys.stderr = sys.stderr, stream
        try:
            yield
        finally:
            sys.stderr = realStderr

def runEntryPoint(cmd, entryPoint, redirect=True, stdinput=""): # {{{
    '''Run a script of the structure from setuptools.

    Provide the entry_point and the command used to run it.
    Return what was written to STDOUT and STDERR.

    Useful for unittest'ing console_scripts.
    '''
    assert isinstance(cmd, str), (type(cmd), cmd)
    argv = cmd.split()

    stdin, stdout, stderr = StringIO(stdinput), StringIO(), StringIO()

    # Redirection can be turned off for debugging.
    if redirect:
        # Prevent closing stdout,stderr by application to allow snooping with
        # getvalue().
        # These will be GC'd after this function returns.
        #
        # class StringIO:
        #     def close(self):
        #         if not self.closed:
        #             self.closed = True
        #             del self.buf, self.pos
        # close() frees memory by deleting references to buf and pos.
        # If self is garbage collected then its attributes will also be
        # GC'd, having the same effect as StringIO.close().
        stdout.close, stderr.close = (lambda: None), (lambda: None)

        # NOTE: No Exceptions are expected so entryPoint() should *not* be
        # called in a try/finally block, allowing Exception/Trackbacks to be
        # displayed as normal.
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                _sysStdin = sys.stdin
                sys.stdin = stdin

                entryPoint(argv=argv)
            finally:
                sys.stdin = _sysStdin
    else:
        entryPoint(argv=argv)

    stdoutTxt, stderrTxt = stdout.getvalue(), stderr.getvalue()

    return stdoutTxt, stderrTxt
# }}} def runEntryPoint
