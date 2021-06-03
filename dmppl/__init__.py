
import sys

import toml

version = toml.load("pyproject.toml")["project"]["version"]

# Don't write .pyc or .pyo files unless it's a release.
if 0 != int(version.split('.')[-1]):
    sys.dont_write_bytecode = True

# NOTE: __all__ is *not* defined in order to avoid namespace conflicts with
# other modules (e.g. math).
