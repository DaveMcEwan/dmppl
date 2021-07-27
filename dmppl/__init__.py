
from os import path
import sys

import toml


# Don't write .pyc or .pyo files unless it's a release.
# If pyproject.toml can't be found, then assume it's a release.
try:
    _parentDir = path.dirname(path.abspath(path.dirname(__file__)))
    _pyproject = path.join(_parentDir, "pyproject.toml")
    version = toml.load(_pyproject)["project"]["version"]

    # https://semver.org/
    # 9. A pre-release version MAY be denoted by appending a hyphen and a
    # series of dot separated identifiers immediately following the patch
    # version.
    # Identifiers MUST comprise only ASCII alphanumerics and hyphens
    # [0-9A-Za-z-]. Identifiers MUST NOT be empty.
    # Numeric identifiers MUST NOT include leading zeroes.
    # Pre-release versions have a lower precedence than the associated normal
    # version.
    # A pre-release version indicates that the version is unstable and might
    # not satisfy the intended compatibility requirements as denoted by its
    # associated normal version.
    # Examples: 1.0.0-alpha, 1.0.0-alpha.1, 1.0.0-0.3.7, 1.0.0-x.7.z.92
    if version.find('-') < 0:
        raise
    else:
        pass
except:
    sys.dont_write_bytecode = True

# NOTE: __all__ is *not* defined in order to avoid namespace conflicts with
# other modules (e.g. math).
