from __future__ import annotations

from .common import panel
from .backends import MagicaCloth2


_BACKEND_MODULES = (
    MagicaCloth2,
)


def register():
    for module in _BACKEND_MODULES:
        module.register()
    panel.register()


def unregister():
    panel.unregister()
    for module in reversed(_BACKEND_MODULES):
        module.unregister()
