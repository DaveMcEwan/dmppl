
from __future__ import absolute_import

import gzip
from toml import * # pip install toml
from .base import stripSuffix

def saveToml(obj, fname): # {{{
    '''Save a TOML object, optionally compressed with GZip.

    Append fname suffix if not provided.

    foo         -> foo.toml
    foo.toml    -> foo.toml
    foo.toml.gz -> foo.toml.gz
    '''

    # Allow null filename to prevent writing, such as in testing.
    if fname is None:
        return

    assert isinstance(fname, str)
    assert 0 < len(fname)

    freal = stripSuffix(stripSuffix(fname, ".gz"), ".toml")
    assert 0 < len(freal)

    if fname.endswith(".gz"):
        fname_ = freal + ".toml.gz"
        with gzip.GzipFile(fname_, 'wb') as fd:
            fd.write(dumps(obj).encode("utf-8")) # toml.dumps()
    else:
        fname_ = freal + ".toml"
        with open(fname_, 'w') as fd:
            dump(obj, fd) # toml.dump()

    return
# }}} def saveToml

def loadToml(fname): # {{{
    '''Load a TOML object.

    Automatically append fname suffix if not provided.
    If file doesn't exist return None, leaving the caller to check.
    This makes it usable in filtered list comprehensions.
    '''
    # TODO: TOML marked load

    assert isinstance(fname, str)
    assert 0 < len(fname)

    freal = stripSuffix(stripSuffix(fname, ".gz"), ".toml")
    assert 0 < len(freal)

    # NOTE: This odd structure is for planned marked-load feature similar to
    # that in yaml.py
    loader = loads # toml.loads()

    try:
        if fname.endswith(".gz"):
            fname_ = freal + ".toml.gz"
            with gzip.GzipFile(fname_, 'rb') as fd:
                obj = loader(fd.read().decode())
        else:
            fname_ = freal + ".toml"
            with open(fname_, 'rb') as fd:
                obj = loader(fd.read().decode())
    except IOError:
        obj = None

    return obj
# }}} def loadToml

if __name__ == "__main__":
    assert False, "Not a standalone script."
