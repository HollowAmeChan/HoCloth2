import os
import sys


bl_info = {
    "name": "HoCloth2",
    "author": "Hollow_ame",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > HoCloth2",
    "description": "Blender bridge for Unity-hosted secondary-motion solvers.",
    "category": "Animation",
}

PLUGIN_DIR = os.path.dirname(__file__)
LIB_DIR = os.path.join(PLUGIN_DIR, "_Lib")
if os.path.isdir(LIB_DIR):
    for name in sorted(os.listdir(LIB_DIR)):
        path = os.path.join(LIB_DIR, name)
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)

from . import hocloth2


def register():
    hocloth2.register()


def unregister():
    hocloth2.unregister()
