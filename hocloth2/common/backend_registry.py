from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import bpy


DrawCallback = Callable[[bpy.types.Context, bpy.types.UILayout], None]


@dataclass(frozen=True)
class BackendPanel:
    backend_id: str
    label: str
    draw: DrawCallback
    order: int = 100


_PANELS: dict[str, BackendPanel] = {}


def register_backend_panel(panel: BackendPanel) -> None:
    _PANELS[panel.backend_id] = panel


def unregister_backend_panel(backend_id: str) -> None:
    _PANELS.pop(backend_id, None)


def iter_backend_panels() -> tuple[BackendPanel, ...]:
    return tuple(sorted(_PANELS.values(), key=lambda panel: (panel.order, panel.label)))
