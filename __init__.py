bl_info = {
    "name": "HoCloth2",
    "author": "Hollow_ame",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > HoCloth2",
    "description": "Blender bridge for Unity-hosted secondary-motion solvers.",
    "category": "Animation",
}

from . import hocloth2


def register():
    hocloth2.register()


def unregister():
    hocloth2.unregister()
