
dmppl - Dave McEwan's Personal Python Library
=============================================

Library is split into several modules:

  - base - Useful in almost every project.
  - color - Color (colour in English) related stuff.
  - math - Useful for mathematical code.
  - nd - ND-array operations.
  - prng - Pseudo-Random Number Generators. Currently just xoroshiro128+.
  - stats - Statistics. Currently just for binary classifiers.
  - test - Helpers for unit testing.
  - toml - Save/load TOML files with optional compression.
  - vcd - Value Change Dump (from Verilog) reader and writer.
  - yaml - Extended YAML parser, useful for implementing DSLs on top of YAML.


Some useful scripts are provided in `dmppl/scripts` which show how to use some
parts of the library modules.

  - beamer-times - Report the time breakdown for beamer presentations by reading
    annotations in the LaTeX.
  - parvec - Generate pseudorandom parameter vectors for design space
    exploration with repeatable results.
  - vcd-utils - Convert VCD (Verilog IEEE1364) files to/from YAML and CSV,
    extract information, or cleanup dodgy VCDs using the forgiving reader
    with strict writer.
  - svg2png - Simple wrapper around inkscape to export SVGs to PNGs.


Some experiments are given in `dmppl/experiments` which are likely not useful
to most people.

  - relest - (Relationship Estimation) Model SoC signal relations.
    Part of my PhD project presented at LOD2019.
  - eva - (EVent Analysis) Measure and visualize correlations between
    measurements.
    Part of my PhD project.
  - correlator - Interface to USB/serial/ACM hardware controlling FPGA with
    SoC-correlation-accelerator.
    Part of my PhD project.


Supports multiple versions of Python (2.7, 3.6, 3.7, 3.8).

  - Dropping support for <3.6 allows use of type annotations.
  - Dropping support for <3.8 allows use of newer language features such as the
    walrus operator, and getting rid of version-specific hacks like
    `openCsvKwargs'.
    Don't necessarily need to wait for distros to support 3.8+, only wait for
    3.6+ since altinstall+venv seems to be the recommended way forward.
    low priority
  - Keeping support for old versions allows compatibility with other programs
    which have built-in Python shells,
    TODO: Collate version dependencies for various programs and decide what I
    want to support: Inkscape, Blender, nextpnr, yosys, ...


See the `Makefile` to wrapup common actions and provide examples of how to run
things.

  - `make venv` to create a virtual environment for each supported version.
  - `make unittest` to perform all unit tests.
  - `make unittest-coverage` to perform all unit tests collecting code coverage
    and produce HTML reports.
  - `make dist` to build a setuptools distribution.
  - `make clean` to remove all generated files.


TODO:

  1. mypy
  2. Implement vch, vchlite?
  3. Expand documentation here
  4. Sphinx/readthedocs

[semantic versioning](https://semver.org/spec/v2.0.0.html)
