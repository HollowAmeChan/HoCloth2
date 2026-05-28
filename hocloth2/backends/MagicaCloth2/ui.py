import bpy

from . import props


_COMPONENT_ICONS = {
    "BONE_CLOTH": "MOD_CLOTH",
    "BONE_SPRING": "BONE_DATA",
    "SPHERE_COLLIDER": "MESH_UVSPHERE",
    "CAPSULE_COLLIDER": "MESH_CYLINDER",
    "PLANE_COLLIDER": "MESH_PLANE",
}


def _short_path(path: str) -> str:
    if not path:
        return ""
    return path if len(path) <= 56 else "..." + path[-53:]


class HOCLOTH2_MC2_UL_components(bpy.types.UIList):
    bl_idname = "HOCLOTH2_MC2_UL_components"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        del context, data, icon, active_data, active_propname, index
        row = layout.row(align=True)
        row.prop(item, "enabled", text="")
        row.label(
            text=item.display_name or item.name or item.component_type,
            icon=_COMPONENT_ICONS.get(item.component_type, "PLUGIN"),
        )
        if item.bone_count:
            row.label(text=str(item.bone_count), icon="BONE_DATA")


def _draw_add_buttons(layout):
    row = layout.row(align=True)
    op = row.operator("hocloth2.mc2_add_component", text="BoneCloth", icon="MOD_CLOTH")
    op.component_type = "BONE_CLOTH"
    op = row.operator("hocloth2.mc2_add_component", text="BoneSpring", icon="BONE_DATA")
    op.component_type = "BONE_SPRING"

    row = layout.row(align=True)
    op = row.operator("hocloth2.mc2_add_component", text="Sphere", icon="MESH_UVSPHERE")
    op.component_type = "SPHERE_COLLIDER"
    op = row.operator("hocloth2.mc2_add_component", text="Capsule", icon="MESH_CYLINDER")
    op.component_type = "CAPSULE_COLLIDER"
    op = row.operator("hocloth2.mc2_add_component", text="Plane", icon="MESH_PLANE")
    op.component_type = "PLANE_COLLIDER"


def _draw_component_editor(layout, component):
    box = layout.box()
    header = box.row(align=True)
    header.prop(
        component,
        "ui_expanded",
        text="",
        icon="TRIA_DOWN" if component.ui_expanded else "TRIA_RIGHT",
        emboss=False,
    )
    header.label(text=component.display_name or component.name, icon=_COMPONENT_ICONS.get(component.component_type, "PLUGIN"))
    header.operator("hocloth2.mc2_remove_component", text="", icon="TRASH")

    if not component.ui_expanded:
        return

    box.prop(component, "enabled")
    box.prop(component, "display_name")
    box.prop(component, "component_type")

    if component.component_type in props.BONE_COMPONENT_TYPES:
        box.prop(component, "armature_object")
        box.prop(component, "root_bone_name")
        box.prop(component, "bone_count")
        box.prop(component, "connection_mode")
        box.operator("hocloth2.mc2_refresh_component", text="Refresh From Active Bone", icon="FILE_REFRESH")

        params = box.column(align=True)
        params.prop(component, "radius")
        params.prop(component, "gravity_strength")
        params.prop(component, "damping")
        params.prop(component, "stiffness")
        params.prop(component, "drag")
    else:
        box.prop(component, "source_object")
        box.prop(component, "radius")
        if component.component_type == "CAPSULE_COLLIDER":
            box.prop(component, "length")
        box.prop(component, "collider_friction")

    box.label(text=component.status or "Idle", icon="INFO")


def draw_panel(context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
    scene = context.scene

    _draw_add_buttons(layout)

    components = scene.hocloth2_mc2_components
    row = layout.row(align=True)
    row.label(text=f"Components: {len(components)}", icon="OUTLINER_COLLECTION")

    if components:
        layout.template_list(
            "HOCLOTH2_MC2_UL_components",
            "",
            scene,
            "hocloth2_mc2_components",
            scene,
            "hocloth2_mc2_component_index",
            rows=4,
        )
        component = props.get_active_component(scene)
        if component is not None:
            _draw_component_editor(layout, component)
    else:
        layout.label(text="Select an armature bone or collider object, then add a component.", icon="INFO")

    runtime = layout.box()
    runtime.label(text="Runtime", icon="MODIFIER")
    row = runtime.row(align=True)
    row.operator("hocloth2.mc2_build", text="Build", icon="FILE_REFRESH")
    row.operator("hocloth2.mc2_step", text="Step", icon="FRAME_NEXT")
    row.operator(
        "hocloth2.mc2_toggle_live",
        text="Pause" if scene.hocloth2_mc2_live_running else "Live",
        icon="PAUSE" if scene.hocloth2_mc2_live_running else "PLAY",
    )
    runtime.operator("hocloth2.mc2_export_snapshot", text="Snapshot", icon="FILE_CACHE")
    if scene.hocloth2_mc2_runtime_handle:
        runtime.label(text=f"Runtime handle: {scene.hocloth2_mc2_runtime_handle} / step {scene.hocloth2_mc2_step_index}", icon="LINKED")
    if scene.hocloth2_mc2_last_snapshot_path:
        runtime.label(text=_short_path(scene.hocloth2_mc2_last_snapshot_path), icon="FILE_CACHE")
    if scene.hocloth2_mc2_last_debug_json_path:
        runtime.label(text=_short_path(scene.hocloth2_mc2_last_debug_json_path), icon="TEXT")
    runtime.label(text=scene.hocloth2_mc2_status or "Idle", icon="INFO")


CLASSES = (
    HOCLOTH2_MC2_UL_components,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
