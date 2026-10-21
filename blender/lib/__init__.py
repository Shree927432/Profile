"""Shared helpers for the Blender scripts that build the room.

Import from a script run inside Blender after putting the `blender/` folder on
sys.path (see blender/README.md):

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from lib import constants, names, materials, geo, render
"""
