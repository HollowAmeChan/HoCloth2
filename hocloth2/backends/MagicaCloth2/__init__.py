from __future__ import annotations

from ...common.backend_registry import BackendPanel, register_backend_panel, unregister_backend_panel
from . import ops, props, ui


BACKEND_ID = "MagicaCloth2"


def register() -> None:
    props.register()
    ops.register()
    ui.register()
    register_backend_panel(
        BackendPanel(
            backend_id=BACKEND_ID,
            label="Magica Cloth 2",
            draw=ui.draw_panel,
            order=10,
        )
    )


def unregister() -> None:
    unregister_backend_panel(BACKEND_ID)
    ui.unregister()
    ops.unregister()
    props.unregister()
