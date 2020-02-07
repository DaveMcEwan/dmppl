
PYPITEST ?= 1
PKGNAME=dmppl

# Allow the use of `source` in makerules working with venv.
SHELL := /bin/bash

default: clean unittest-coverage dist

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
venv2.7:
	python2.7 -m pip install --user virtualenv
	python2.7 -m virtualenv --no-wheel venv2.7
	$(VENV2.7) pip install coverage pyyaml numpy toml
	$(VENV2.7) pip install -e .
venv3.5:
	python3.5 -m pip install --user virtualenv
	python3.5 -m virtualenv --no-wheel venv3.5
	$(VENV3.5) pip install coverage pyyaml numpy toml
	$(VENV3.5) pip install -e .
venv3.6:
	python3.6 -m venv venv3.6
	$(VENV3.6) pip install coverage mypy pyyaml numpy toml
	$(VENV3.6) pip install -e .
venv3.7:
	python3.7 -m venv venv3.7
	$(VENV3.7) pip install coverage mypy pyyaml numpy toml
	$(VENV3.7) pip install joblib matplotlib prettytable seaborn
	$(VENV3.7) pip install 'tensorflow==2.0.0' graphviz pydot
	$(VENV3.7) pip install -e .
venv3.8:
	python3.8 -m venv venv3.8
	$(VENV3.8) pip install coverage mypy pyyaml numpy toml
	$(VENV3.8) pip install -e .

venv: venv2.7
venv: venv3.5
venv: venv3.6
venv: venv3.7
venv: venv3.8

# Run unit tests like this:
#   python -m unittest tests                        # All modules
#   python -m unittest tests.test_math              # One module
#   python -m unittest tests.test_math.isPow2       # One function
unittest: venv
	$(VENV2.7) python -m unittest tests
	$(VENV3.5) python -m unittest tests
	$(VENV3.6) python -m unittest tests
	$(VENV3.7) python -m unittest tests
	$(VENV3.8) python -m unittest tests

# Collect coverage and produces HTML reports from unit tests.
COVRC = --rcfile=tests/.coveragerc_
unittest-coverage: venv
	$(VENV2.7) coverage run $(COVRC)2.7 -m unittest tests && \
		coverage html $(COVRC)2.7
	$(VENV3.5) coverage run $(COVRC)3.5 -m unittest tests && \
		coverage html $(COVRC)3.5
	$(VENV3.6) coverage run $(COVRC)3.6 -m unittest tests && \
		coverage html $(COVRC)3.6
	$(VENV3.7) coverage run $(COVRC)3.7 -m unittest tests && \
		coverage html $(COVRC)3.7
	$(VENV3.8) coverage run $(COVRC)3.8 -m unittest tests && \
		coverage html $(COVRC)3.8


# Use a specific Python version for packaging to aid reproducability.
venv3.7/lib/python3.7/site-packages/wheel:
	$(VENV3.7) pip install setuptools wheel twine

# https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives
.PHONY: dist
dist: venv3.7 venv3.7/lib/python3.7/site-packages/wheel
	$(VENV3.7) python setup.py sdist bdist_wheel


# Upload to PyPI test server by default.
# https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives
ifeq ($(PYPITEST), 0)
upload:
	$(VENV3.7) python -m twine upload dist/*
else
REPOURL=https://test.pypi.org/legacy/
upload:
	$(VENV3.7) python -m twine upload --repository-url $(REPOURL) dist/*
endif

# Install from PyPI test server without dependencies.
# https://packaging.python.org/tutorials/packaging-projects/#installing-your-newly-uploaded-package
ifeq ($(PYPITEST), 0)
install: venv
	$(VENV2.7) pip install $(PKGNAME)
	$(VENV3.5) pip install $(PKGNAME)
	$(VENV3.6) pip install $(PKGNAME)
	$(VENV3.7) pip install $(PKGNAME)
else
INDEXURL=https://test.pypi.org/simple/
install: venv
	$(VENV2.7) pip install --index-url $(INDEXURL) --no-deps $(PKGNAME)
	$(VENV3.5) pip install --index-url $(INDEXURL) --no-deps $(PKGNAME)
	$(VENV3.6) pip install --index-url $(INDEXURL) --no-deps $(PKGNAME)
	$(VENV3.7) pip install --index-url $(INDEXURL) --no-deps $(PKGNAME)
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
