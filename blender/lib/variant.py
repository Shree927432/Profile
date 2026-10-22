"""Run another script's code under new names: one builder, two guitars.

    load(path, subs, name)   reads the Python file at `path`, applies the text substitutions
                             `subs` ([(old, new)], in order) and runs it as a fresh module `name`
                             (registered in sys.modules), with its own globals.

guitar_04 (Number One) is built on the same Strat as guitar_02: props/guitar_04.py runs
props/guitar_02.py this way with "guitar_02" -> "guitar_04" (object, material and image names,
its spec GUITAR_04, its blueprint module) and then replaces only the functions that differ.
guitar_02.py itself is not touched, so its model and export stay exactly as they were.
"""
import sys
import types


def load(path, subs, name):
    with open(path) as f:
        src = f.read()
    for old, new in subs:
        src = src.replace(old, new)
    mod = types.ModuleType(name)
    mod.__file__ = path
    sys.modules[name] = mod
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod
