from __future__ import annotations

import bpy

from .backend_registry import iter_backend_panels


class HOCLOTH2_PT_main_panel(bpy.types.Panel):
    bl_label = "HoCloth2"
    bl_idname = "HOCLOTH2_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "HoCloth2"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        top = layout.box()
        top.label(text="Unity Physics Host", icon="MOD_PHYSICS")
        row = top.row(align=True)
        row.operator("hocloth2.host_status", text="Status", icon="INFO")
        row.operator("hocloth2.host_launch", text="Launch", icon="PLAY")

        panels = iter_backend_panels()
        if not panels:
            layout.label(text="No backend registered.", icon="ERROR")
            return

        for backend_panel in panels:
            box = layout.box()
            header = box.row(align=True)
            header.label(text=backend_panel.label, icon="PLUGIN")
            backend_panel.draw(context, box)


class HOCLOTH2_OT_host_status(bpy.types.Operator):
    bl_idname = "hocloth2.host_status"
    bl_label = "Host Status"
    bl_description = "Show the current Unity host status"

    def execute(self, context: bpy.types.Context):
        self.report({"INFO"}, "Unity host bridge is not implemented yet.")
        return {"FINISHED"}


class HOCLOTH2_OT_host_launch(bpy.types.Operator):
    bl_idname = "hocloth2.host_launch"
    bl_label = "Launch Host"
    bl_description = "Launch the bundled Unity host"

    def execute(self, context: bpy.types.Context):
        self.report({"INFO"}, "Unity host launcher is not implemented yet.")
        return {"FINISHED"}


CLASSES = (
    HOCLOTH2_PT_main_panel,
    HOCLOTH2_OT_host_status,
    HOCLOTH2_OT_host_launch,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
