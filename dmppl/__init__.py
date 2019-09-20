
from os import path
import sys

# Read version number from file.
# https://packaging.python.org/en/latest/single_source_version.html
_curd = path.abspath(path.dirname(__file__))
_version_fname = path.join(_curd, "VERSION")
with open(_version_fname, 'r') as fd:
    for line in fd:
        if not line.startswith('#'):
            version = line.strip()
            break

# Don't write .pyc or .pyo files unless it's a release.
# This doesn't affect eva_common.
# Only affects eva-exo, eva-exc, ...
if 0 != int(version.split('.')[-1]):
    sys.dont_write_bytecode = True

# NOTE: __all__ is *not* defined in order to avoid namespace conflicts with
# other modules (e.g. math).
