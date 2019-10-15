
# Standard library imports
import os
import sys

# PyPI library imports

# Local library imports
from dmppl.base import dbg, info, verb

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
import dmppl.experiments.eva.eva_common as eva

def evaHtml(args): # {{{
    '''Read in result directory like ./foo.eva/ and serve HTML visualizations.
    '''
    assert eva.initPathsDone


    return 0
# }}} def evaHtml

if __name__ == "__main__":
    assert False, "Not a standalone script."
