
from __future__ import absolute_import

import gzip
import sys
import yaml # pip install pyyaml # Requires python 2.7 or 3.4+
from .base import stripSuffix

_version_help = "Python 2.7 or 3.4+ required."
if sys.version_info[0] == 2:
    assert sys.version_info[1] == 7, _version_help
elif sys.version_info[0] == 3:
    assert sys.version_info[1] >= 4, _version_help
else:
    assert False, _version_help

# {{{ YAML marked load
# Every dict/list/str is replaced with MapNode/SeqNode/StrNode/etc, which
#   subclasses dict/list/str/etc to add the attributes `start_mark` and
#   `end_mark`.
# Please see the yaml.error module for the `Mark` class.
# Note that only the following data types are supported:
# - dict
# - list
# - str
# - int
# - bool, actually returned as int since bool() cannot be subclassed.
# - float
# - none, actually just a valueless class as NoneType can't be subclassed.
class YamlConstructor(yaml.constructor.SafeConstructor):
    class MapNode(dict):
        def __init__(self, x, start_mark, end_mark):
            dict.__init__(self, x)
            self.start_mark = start_mark
            self.end_mark = end_mark

        def __new__(self, x, start_mark, end_mark):
            return dict.__new__(self, x)

    class SeqNode(list):
        def __init__(self, x, start_mark, end_mark):
            list.__init__(self, x)
            self.start_mark = start_mark
            self.end_mark = end_mark

        def __new__(self, x, start_mark, end_mark):
            return list.__new__(self, x)

    class StrNode(str):
        def __init__(self, x, start_mark, end_mark):
            str.__init__(self)
            self.start_mark = start_mark
            self.end_mark = end_mark

        def __new__(self, x, start_mark, end_mark):
            return str.__new__(self, x)

    class IntNode(int):
        def __init__(self, x, start_mark, end_mark):
            int.__init__(self)
            self.start_mark = start_mark
            self.end_mark = end_mark

        def __new__(self, x, start_mark, end_mark):
            return int.__new__(self, x)

    class FloatNode(float):
        def __init__(self, x, start_mark, end_mark):
            float.__init__(self)
            self.start_mark = start_mark
            self.end_mark = end_mark

        def __new__(self, x, start_mark, end_mark):
            return float.__new__(self, x)

    class NoneNode():
        def __init__(self, x, start_mark, end_mark):
            self.start_mark = start_mark
            self.end_mark = end_mark

    def construct_yaml_map(self, node):
        obj, = yaml.constructor.SafeConstructor.construct_yaml_map(self, node)
        return self.MapNode(obj, node.start_mark, node.end_mark)

    def construct_yaml_seq(self, node):
        obj, = yaml.constructor.SafeConstructor.construct_yaml_seq(self, node)
        return self.SeqNode(obj, node.start_mark, node.end_mark)

    def construct_yaml_str(self, node):
        obj = yaml.constructor.SafeConstructor.construct_scalar(self, node)
        return self.StrNode(obj, node.start_mark, node.end_mark)

    def construct_yaml_int(self, node):
        obj = yaml.constructor.SafeConstructor.construct_yaml_int(self, node)
        return self.IntNode(obj, node.start_mark, node.end_mark)

    def construct_yaml_bool(self, node):
        obj = yaml.constructor.SafeConstructor.construct_yaml_bool(self, node)
        return self.IntNode(int(obj), node.start_mark, node.end_mark)

    def construct_yaml_float(self, node):
        obj = yaml.constructor.SafeConstructor.construct_yaml_float(self, node)
        return self.FloatNode(obj, node.start_mark, node.end_mark)

    def construct_yaml_null(self, node):
        obj = yaml.constructor.SafeConstructor.construct_yaml_null(self, node)
        return self.NoneNode(obj, node.start_mark, node.end_mark)

YamlConstructor.add_constructor("tag:yaml.org,2002:map",
                                YamlConstructor.construct_yaml_map)

YamlConstructor.add_constructor("tag:yaml.org,2002:seq",
                                YamlConstructor.construct_yaml_seq)

YamlConstructor.add_constructor("tag:yaml.org,2002:str",
                                YamlConstructor.construct_yaml_str)

YamlConstructor.add_constructor("tag:yaml.org,2002:int",
                                YamlConstructor.construct_yaml_int)

YamlConstructor.add_constructor("tag:yaml.org,2002:bool",
                                YamlConstructor.construct_yaml_bool)

YamlConstructor.add_constructor("tag:yaml.org,2002:float",
                                YamlConstructor.construct_yaml_float)

YamlConstructor.add_constructor("tag:yaml.org,2002:null",
                                YamlConstructor.construct_yaml_null)

class YamlMarkedLoader(yaml.reader.Reader,
                       yaml.scanner.Scanner,
                       yaml.parser.Parser,
                       yaml.composer.Composer,
                       YamlConstructor,
                       yaml.resolver.Resolver):
    def __init__(self, stream):
        yaml.reader.Reader.__init__(self, stream)
        yaml.scanner.Scanner.__init__(self)
        yaml.parser.Parser.__init__(self)
        yaml.composer.Composer.__init__(self)
        yaml.constructor.SafeConstructor.__init__(self)
        yaml.resolver.Resolver.__init__(self)

def yamlMarkedLoad(stream):
    return YamlMarkedLoader(stream).get_single_data()

# }}} YAML marked load

def loadYml(fname, marked=False): # {{{
    '''Load a YAML object.

    Automatically append fname suffix if not provided.
    If file doesn't exist return None, leaving the caller to check.
    This makes it usable in filtered list comprehensions.

    Using marked gives the character position of each piece of data.
    '''
    assert isinstance(fname, str)
    assert 0 < len(fname)
    assert isinstance(marked, bool)

    freal = stripSuffix(stripSuffix(fname, ".gz"), ".yml")
    assert 0 < len(freal)

    loader = yamlMarkedLoad if marked else yaml.safe_load

    try:
        if fname.endswith(".gz"):
            fname_ = freal + ".yml.gz"
            with gzip.GzipFile(fname_, 'rb') as fd:
                obj = loader(fd)
        else:
            fname_ = freal + ".yml"
            with open(fname_, 'rb') as fd:
                obj = loader(fd)
    except IOError:
        obj = None

    return obj
# }}} def loadYml

def saveYml(obj, fname): # {{{
    '''Save a YAML object, optionally compressed with GZip.

    Append fname suffix if not provided.

    foo         -> foo.yml
    foo.yml     -> foo.yml
    foo.yml.gz  -> foo.yml.gz
    '''
    assert isinstance(fname, str)
    assert 0 < len(fname)

    freal = stripSuffix(stripSuffix(fname, ".gz"), ".yml")
    assert 0 < len(freal)

    # TODO: Descend into object and convert everything to plain Python data
    # types so safe_dump doesn't complain about things like marked_load or
    # numpy types.

    if fname.endswith(".gz"):
        fname_ = freal + ".yml.gz"
        with gzip.GzipFile(fname_, 'wb') as fd:
            fd.write(yaml.safe_dump(obj).encode("utf-8"))
    else:
        fname_ = freal + ".yml"
        with open(fname_, 'w') as fd:
            yaml.safe_dump(obj, fd)

    return
# }}} def saveYml

if __name__ == "__main__":
    assert False, "Not a standalone script."
