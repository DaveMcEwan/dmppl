
PYPITEST ?= 1
PKGNAME=dmppl

# Allow the use of `source` in makerules working with venv.
SHELL := /bin/bash

default: unittest

# Convenience variables just to keep Makefile tidy.
VENV2.7 = source venv2.7/bin/activate &&
VENV3.5 = source venv3.5/bin/activate &&
VENV3.6 = source venv3.6/bin/activate &&
VENV3.7 = source venv3.7/bin/activate &&
VENV3.8 = source venv3.8/bin/activate &&

# Create the virtual environments and install dependencies.
# In Python2.7 virtualenv is not in the standard library.
# In Python3.6+ venv is in standard library.
# This requires multiple versions to be installed on the system, probably
# with something like:
#    ...download CPython tarball, extract, cd to there...
#	 ./configure && make && sudo make altinstall
# NOTE: TOML module is installed first to read pyproject.toml
venv2.7:
	python2.7 -m pip install --user virtualenv
	python2.7 -m virtualenv --no-wheel venv2.7
	$(VENV2.7) pip install toml
	$(VENV2.7) pip install -e .
venv3.5:
	python3.5 -m pip install --user virtualenv
	python3.5 -m virtualenv --no-wheel venv3.5
	$(VENV3.5) pip install toml
	$(VENV3.5) pip install -e .
venv3.6:
	python3.6 -m venv venv3.6
	$(VENV3.6) pip install toml
	$(VENV3.6) pip install -e .
venv3.7:
	python3.7 -m venv venv3.7
	$(VENV3.7) pip install toml
	$(VENV3.7) pip install -e .
#	$(VENV3.7) pip install 'tensorflow~=2.4.1'
venv3.8:
	python3.8 -m venv venv3.8
	$(VENV3.8) pip install toml
	$(VENV3.8) pip install -e .

venv: venv3.6
venv: venv3.7
venv: venv3.8

# Run unit tests like this:
#   python -m unittest tests                        # All modules
#   python -m unittest tests.test_math              # One module
#   python -m unittest tests.test_math.isPow2       # One function
unittest: venv
	$(VENV3.6) python -m unittest tests
	$(VENV3.7) python -m unittest tests
	$(VENV3.8) python -m unittest tests

# Collect coverage and produces HTML reports from unit tests.
COVRC = --rcfile=tests/.coveragerc_
unittest-coverage: venv
	$(VENV3.6) coverage run $(COVRC)3.6 -m unittest tests && \
		coverage html $(COVRC)3.6
	$(VENV3.7) coverage run $(COVRC)3.7 -m unittest tests && \
		coverage html $(COVRC)3.7
	$(VENV3.8) coverage run $(COVRC)3.8 -m unittest tests && \
		coverage html $(COVRC)3.8


# Use a specific Python version for packaging to aid reproducability.
DIST_PYVER = 3.7
DIST_VENVDIR = venv$(DIST_PYVER)
DIST_VENV = source $(DIST_VENVDIR)/bin/activate &&
$(DIST_VENVDIR)/lib/python$(DIST_PYVER)/site-packages/wheel:
	$(DIST_VENV) pip install setuptools wheel twine

# https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives
.PHONY: dist
dist: $(DIST_VENVDIR) $(DIST_VENVDIR)/lib/python$(DIST_PYVER)/site-packages/wheel
	$(DIST_VENV) python setup.py sdist bdist_wheel

# Upload to PyPI test server by default.
# https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives
ifeq ($(PYPITEST), 0)
upload:
	$(DIST_VENV) python -m twine upload dist/*
else
REPOURL=https://test.pypi.org/legacy/
upload:
	$(DIST_VENV) python -m twine upload --repository-url $(REPOURL) dist/*
endif


clean:
	rm -rf build
	rm -rf dist
	rm -rf $(PKGNAME).egg-info
	rm -rf `find . -name '*__pycache__*'`
	rm -rf `find . -name '*.pyc'`
	rm -rf `find . -name '*.pyo'`
	rm -rf venv*
	rm -rf .coverage_*
	rm -rf coverage*_html*

# Print out all lines containing uppercase "todo".
# Note this will always include itself so when using "make todo | wc -l" the
# result will be one too large.
todo:
	@grep --color -n TODO `find \`git ls-tree -r HEAD --name-only\` -type f`
