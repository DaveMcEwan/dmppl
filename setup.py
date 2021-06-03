
# This file is a wrapper around `pyproject.toml` which may be all that's
# required in future for setuptools.

# Install in editable mode:
#   python3.6 -m venv myVenv
#   source myVenv/bin/activate
#   pip install toml
#   pip install -e .

# Standard library
from setuptools import setup, find_packages
from os import path
import sys

# PyPI
import toml

pyproject = toml.load("pyproject.toml")

setup(
    name                = pyproject["project"]["name"],
    version             = pyproject["project"]["version"],
    description         = pyproject["project"]["description"],
    author              = pyproject["project"]["authors"][0],
    license             = pyproject["project"]["license"],
    url                 = pyproject["project"]["homepage"],
    classifiers         = pyproject["project"]["classifiers"],
    python_requires     = pyproject["project"]["python_requires"],
    entry_points        = {
        "console_scripts": ['='.join(i) for i in pyproject["entry_points"]["console_scripts"].items()],
        #"gui_scripts": ['='.join(i) for i in pyproject["entry_points"]["gui_scripts"].items()],
    },

    install_requires    = [' '.join(i) for i in pyproject["dependencies"]["install"].items()],
    extras_require      = {
        "dev": [' '.join(i) for i in pyproject["dependencies"]["dev"].items()]
    },

    packages=find_packages(exclude=pyproject["options"]["packages"]["find"]["exclude"]),
)
